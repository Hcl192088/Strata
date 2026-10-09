#!/usr/bin/env python3
"""Re-run the 2026-10-08 RTX 4070/IQ2_XS benchmark from provenance.json.

Standard-library only. No network, download, model redistribution, or automatic
publication. Run "check" (SHA-256) *separately* from "run" to avoid warming the
OS file cache immediately before a timed measurement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
from datetime import datetime, timezone

MANIFEST = Path(__file__).with_name("provenance.json")
SOURCE_COMMIT = "9ec3806058cf32ab27a55e4377daf7cf0d087dec"
PATH_OPTIONS = {"--pack", "--native", "--ple-gguf", "--mtp",
                "--expert-profile", "--tokens-file"}
DECODE_RE = re.compile(
    r"^decode\s+(\d+) tokens in\s+([\d.]+) ms\s+->\s+([\d.]+) tok/s",
    re.MULTILINE,
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def git_head(directory: Path) -> str | None:
    try:
        p = subprocess.run(["git", "-C", str(directory), "rev-parse", "HEAD"],
                           capture_output=True, text=True, check=True)
        return p.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def checked_path(root: Path, rel: str) -> Path:
    candidate = (root / rel).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("Manifest path escapes data root: " + rel)
    return candidate


def expected_files(manifest: dict) -> list[dict]:
    rows = []
    for entry in manifest["model"]["native_shards"]:
        rows.append({"role": "model", **entry})
    rows.extend(manifest["artifacts"])
    return rows


def verify(manifest: dict, data_root: Path, engine: Path, source: Path | None,
           mode: str, permit_different_binary: bool) -> tuple[list[str], list[str]]:
    problems, warnings = [], []
    head = git_head(source) if source else None
    if source:
        if head is None:
            problems.append(f"Cannot determine Git HEAD in source directory: {source}")
        elif head.lower() != SOURCE_COMMIT:
            problems.append(f"Wrong source HEAD: {head}; expected {SOURCE_COMMIT}")
        try:
            dirty = subprocess.run(
                ["git", "-C", str(source), "status", "--porcelain"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            if dirty:
                warnings.append("Source working tree has uncommitted changes")
        except (OSError, subprocess.CalledProcessError):
            warnings.append("Cannot check whether source tree is clean")
    else:
        warnings.append("Source Git checkout not verified (provide --source-root)")
    if not engine.is_file():
        problems.append(f"Engine executable missing: {engine}")
    else:
        expected = manifest["source"]
        if engine.stat().st_size != expected["binary_bytes"]:
            msg = (f"Engine size mismatch: {engine.stat().st_size} vs "
                   f"{expected['binary_bytes']} bytes")
            (warnings if permit_different_binary else problems).append(msg)
        digest = sha256(engine)
        if digest != expected["binary_sha256"].upper():
            msg = f"Engine binary SHA-256 mismatch: {digest}"
            (warnings if permit_different_binary else problems).append(msg)
    for item in expected_files(manifest):
        target = checked_path(data_root, item["path"])
        if not target.is_file():
            problems.append(f"MISSING [{item['role']}]: {target}")
            continue
        if target.stat().st_size != item["bytes"]:
            problems.append(f"SIZE MISMATCH [{item['role']}]: {target}")
            continue
        if mode == "sha256" and sha256(target) != item["sha256"].upper():
            problems.append(f"SHA256 MISMATCH [{item['role']}]: {target}")
    if mode == "size":
        warnings.append("Data file SHA-256 was NOT checked; only sizes were compared")
    return problems, warnings


def make_command(manifest: dict, data_root: Path, engine: Path) -> list[str]:
    original = manifest["primary_command"]["args"]
    command = [str(engine)]
    path_value = False
    for arg in original:
        if path_value:
            command.append(str(checked_path(data_root, arg)))
            path_value = False
        else:
            command.append(arg)
            path_value = arg in PATH_OPTIONS
    if path_value:
        raise ValueError("Path flag at end of provenance argument vector")
    return command


def gpu_snapshot(path: Path) -> None:
    try:
        p = subprocess.run(
            ["nvidia-smi", "--query-gpu=timestamp,name,memory.total,memory.used,"
             "memory.free,driver_version", "--format=csv"],
            capture_output=True, text=True, timeout=20,
        )
        path.write_text(p.stdout if p.returncode == 0 else p.stderr,
                        encoding="utf-8")
    except (OSError, subprocess.TimeoutExpired) as exc:
        path.write_text(str(exc), encoding="utf-8")


def run_benchmark(manifest: dict, data_root: Path, engine: Path,
                  output: Path, repetitions: int) -> None:
    output.mkdir(parents=True, exist_ok=False)
    command = make_command(manifest, data_root, engine)
    env = os.environ.copy()
    env.update(manifest["primary_command"]["environment"])
    result_rows = []
    expected_tokens = int(manifest["primary_command"]["output_tokens"])
    for index in range(1, repetitions + 1):
        folder = output / f"run-{index:02d}"
        folder.mkdir()
        # Do not publish raw stdout: the engine prints the full prompt and
        # output token IDs, potentially encoding private text.
        (folder / "command.json").write_text(
            json.dumps({"argv": command,
                        "environment_overrides": manifest["primary_command"]["environment"],
                        "started_utc": datetime.now(timezone.utc).isoformat()},
                       indent=2), encoding="utf-8")
        gpu_snapshot(folder / "gpu-before.csv")
        with (folder / "stdout.log").open("w", encoding="utf-8") as stdout, \\
             (folder / "stderr.log").open("w", encoding="utf-8") as stderr:
            proc = subprocess.run(command, cwd=data_root, env=env,
                                  stdout=stdout, stderr=stderr, check=False)
        gpu_snapshot(folder / "gpu-after.csv")
        output_text = (folder / "stdout.log").read_text(encoding="utf-8")
        matches = DECODE_RE.findall(output_text)
        row = {"run": index, "exit_code": proc.returncode,
               "accepted_decode_tok_s": None, "output_tokens": None,
               "decode_ms": None, "valid": False}
        if proc.returncode == 0 and len(matches) == 1:
            tokens, ms, rate = matches[0]
            row.update({"output_tokens": int(tokens), "decode_ms": float(ms),
                        "accepted_decode_tok_s": float(rate),
                        "valid": int(tokens) == expected_tokens})
        (folder / "summary.json").write_text(json.dumps(row, indent=2),
                                               encoding="utf-8")
        result_rows.append(row)
        print(f"run {index}/{repetitions}: {row}", flush=True)
    success = [r["accepted_decode_tok_s"] for r in result_rows if r["valid"]]
    report = {
        "source_commit_required": SOURCE_COMMIT,
        "binary_sha256_expected": manifest["source"]["binary_sha256"],
        "workload": "same prompt/profile and all artifact hashes REQUIRED for exact comparison",
        "results": result_rows,
        "valid_runs": len(success),
        "median_accepted_decode_tok_s": statistics.median(success) if success else None,
        "mean_accepted_decode_tok_s": statistics.mean(success) if success else None,
        "min_accepted_decode_tok_s": min(success) if success else None,
        "max_accepted_decode_tok_s": max(success) if success else None,
        "historical_primary_median": manifest["run_sets"]["primary_e4_s24"]["median_tok_s"],
        "note": "GPU snapshots are before/after, NOT an in-run peak VRAM measurement",
    }
    (output / "report.json").write_text(json.dumps(report, indent=2),
                                        encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
    if len(success) != repetitions:
        raise SystemExit("One or more runs failed or produced the wrong output token count")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["check", "run"])
    p.add_argument("--data-root", type=Path, required=True,
                   help="Folder containing models/, packs/, mtp/, profiles/, prompts/")
    p.add_argument("--engine", type=Path, required=True,
                   help="Path to the compiled strata.exe executable")
    p.add_argument("--source-root", type=Path,
                   help="The pinned Git checkout to verify with git rev-parse HEAD")
    p.add_argument("--hash-mode", choices=["sha256", "size"],
                   help="Defaults to sha256 for check, size for run (avoid pre-run cache warming)")
    p.add_argument("--allow-binary-mismatch", action="store_true",
                   help="Run a rebuild that differs in bytes; not a byte-identical engine reproduction")
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("--out", type=Path, help="New output directory for raw logs (never overwritten)")
    args = p.parse_args()
    if args.action == "run" and (not args.out or args.runs < 1):
        p.error("run requires --out and --runs >= 1")
    data_root, engine = args.data_root.resolve(), args.engine.resolve()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mode = args.hash_mode or ("sha256" if args.action == "check" else "size")
    problems, warnings = verify(manifest, data_root, engine,
                                 args.source_root.resolve() if args.source_root else None,
                                 mode, args.allow_binary_mismatch)
    for line in warnings:
        print("WARNING:", line, file=sys.stderr)
    if problems:
        for line in problems:
            print("ERROR:", line, file=sys.stderr)
        return 2
    print(f"Preflight OK ({mode} data validation)")
    if args.action == "run":
        run_benchmark(manifest, data_root, engine, args.out.resolve(), args.runs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
