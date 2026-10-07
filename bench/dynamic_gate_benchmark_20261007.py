import csv
import hashlib
import json
import os
import re
import socket
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(r"C:\Users\User\Strata-v038-prefill-seed-20261006")
META_PATH = Path(r"C:\Users\User\B_forced.command.json")
OUT_ROOT = ROOT / "work-dynamic-gate-20261007" / "benchmark"
HOST_EXPECTED = "DESKTOP-LKMLUPC"
ARMS = {
    "B": {"fixed": 0, "check": 0, "min_gain": None},
    "D": {"fixed": 128, "check": 0, "min_gain": None},
    "F2": {"fixed": 0, "check": 64, "min_gain": 2.0},
    "F4": {"fixed": 0, "check": 64, "min_gain": 4.0},
    "F6": {"fixed": 0, "check": 64, "min_gain": 6.0},
}


def now():
    return datetime.now().astimezone().isoformat()


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def run_capture(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError(f"command failed rc={p.returncode}: {args!r}\n{p.stdout}\n{p.stderr}")
    return p.stdout.strip()


def process_names():
    out = run_capture(["tasklist", "/FO", "CSV", "/NH"])
    rows = list(csv.reader(out.splitlines()))
    names = [row[0] for row in rows if row and row[0].lower().startswith(("strata", "llama"))]
    ps = (
        f"$me={os.getpid()}; "
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.ProcessId -ne $me -and $_.Name -match '^(python|python3)' "
        "-and $_.CommandLine -match 'force_B_runner|parent_retest|periodic_decode|dynamic_gate' } | "
        "ForEach-Object { '{0}:{1}' -f $_.ProcessId,$_.CommandLine }"
    )
    wrapper_rows = run_capture(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps])
    return names + ([line for line in wrapper_rows.splitlines() if line.strip()] if wrapper_rows else [])


def gpu_state():
    return run_capture([
        "nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader"
    ])


def ram_state():
    out = run_capture([
        "powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
        "$os=Get-CimInstance Win32_OperatingSystem; [math]::Round($os.FreePhysicalMemory/1024,0)"
    ])
    values = re.findall(r"(?m)^\s*(\d+)\s*$", out)
    if not values:
        raise RuntimeError(f"cannot verify free RAM: {out!r}")
    free_mib = int(values[-1])
    if free_mib < 4096:
        raise RuntimeError(f"free RAM below safety floor: {free_mib} MiB")
    return {"free_mib": free_mib, "raw": out}


def preflight():
    host = socket.gethostname()
    if host.upper() != HOST_EXPECTED:
        raise RuntimeError(f"wrong remote host: {host!r}, expected {HOST_EXPECTED!r}")
    busy = process_names()
    if busy:
        raise RuntimeError(f"Strata/llama/benchmark wrapper already running; refusing to stop or overlap: {busy}")
    return {"hostname": host, "gpu": gpu_state(), "ram": ram_state(), "processes": busy}


def parse_kv(line):
    return {key: value for key, value in re.findall(r"([A-Za-z_]+)=([^\s]+)", line)}


def parse_metrics(stdout_text, stderr_text):
    metrics = {}
    combined = stdout_text + "\n" + stderr_text
    patterns = [
        (r"(?m)^decode\s+(\d+) tokens in ([0-9.]+) ms\s+->\s+([0-9.]+) tok/s", "decode"),
        (r"(?m)^prefill\s+(\d+) tokens in ([0-9.]+) ms\s+->\s+([0-9.]+) tok/s\s+\(time to first token ([0-9.]+) ms\)", "prefill"),
    ]
    m = re.search(patterns[0][0], stdout_text)
    if m:
        metrics.update({"decode_tokens": int(m.group(1)), "decode_ms": float(m.group(2)), "decode_tok_s": float(m.group(3))})
    m = re.search(patterns[1][0], stdout_text)
    if m:
        metrics.update({"prefill_tokens": int(m.group(1)), "prefill_ms": float(m.group(2)), "prefill_tok_s": float(m.group(3)), "ttft_ms": float(m.group(4))})
    m = re.search(r"R4 expert-cache hits\s+(\d+)\s+of\s+(\d+)\s*=\s*([0-9.]+)", stdout_text)
    if m:
        metrics.update({"gpu_hits": int(m.group(1)), "gpu_lookups": int(m.group(2)), "gpu_hit_rate": float(m.group(3))})
    m = re.search(r"adaptive tier\s+(\d+) experts swapped", stdout_text)
    if m:
        metrics["total_swaps"] = int(m.group(1))
    m = re.search(r"adaptive costs\s+ranking\s+([0-9.]+)\s+transfer\s+([0-9.]+)\s+sync\s+([0-9.]+) ms total", stdout_text)
    if m:
        metrics.update({"ranking_ms": float(m.group(1)), "transfer_ms": float(m.group(2)), "sync_ms": float(m.group(3))})
    gate = re.search(
        r"strata periodic gate: checks=(\d+) accepted=(\d+) rejected=(\d+) acceptance_rate=([0-9.]+) "
        r"interval=(\d+) threshold=([0-9.]+) eval_total_ms=([0-9.]+) ranking_total_ms=([0-9.]+) "
        r"mean_gain_pp=([0-9.]+) accepted_mean_gain_pp=([0-9.]+) rejected_mean_gain_pp=([0-9.]+)",
        stderr_text,
    )
    if gate:
        metrics.update({
            "periodic_checks": int(gate.group(1)), "periodic_accepted": int(gate.group(2)),
            "periodic_rejected": int(gate.group(3)), "gate_acceptance_rate": float(gate.group(4)),
            "gate_interval": int(gate.group(5)), "gate_threshold": float(gate.group(6)),
            "gate_eval_total_ms": float(gate.group(7)), "gate_ranking_total_ms": float(gate.group(8)),
            "gate_mean_gain_pp": float(gate.group(9)), "gate_accepted_mean_gain_pp": float(gate.group(10)),
            "gate_rejected_mean_gain_pp": float(gate.group(11)),
        })
    gates = []
    for line in stderr_text.splitlines():
        if line.startswith("strata periodic gate: pos="):
            item = parse_kv(line)
            item["decision"] = "ACCEPT" if " ACCEPT " in line else "REJECT"
            item["pos"] = int(item["pos"])
            item["current"] = float(item["current"])
            item["candidate"] = float(item["candidate"])
            item["gain"] = float(item["gain"].removesuffix("pp"))
            item["threshold"] = float(item["threshold"])
            item["changed"] = int(item["changed"])
            item["swaps"] = int(item["swaps"])
            item["eval_ms"] = float(item["eval_ms"])
            item["rank_ms"] = float(item["rank_ms"])
            item["transfer_ms"] = float(item["transfer_ms"])
            item["sync_ms"] = float(item["sync_ms"])
            gates.append(item)
    segments = []
    for line in stderr_text.splitlines():
        if line.startswith("strata segment:"):
            item = parse_kv(line)
            if "accepted_decode_tokens" in item:
                segments.append(item)
    return metrics, gates, segments


def expected_positions(arm):
    cfg = ARMS[arm]
    interval = cfg["fixed"] or cfg["check"]
    return list(range(64 + interval, 1025, interval)) if interval else []


def run_arm(meta, arm, exe_sha, profile_sha, tokens_sha):
    cfg = ARMS[arm]
    before = preflight()
    args = list(meta["args"])
    if cfg["fixed"]:
        args += ["--periodic-every", str(cfg["fixed"])]
    if cfg["check"]:
        args += ["--periodic-adaptive-check-every", str(cfg["check"]), "--periodic-adaptive-min-gain", str(cfg["min_gain"])]
    arm_dir = OUT_ROOT / arm
    arm_dir.mkdir(parents=False, exist_ok=False)
    stdout_path = arm_dir / "stdout.log"
    stderr_path = arm_dir / "stderr.log"
    command = {
        "arm": arm, "periodic_every": cfg["fixed"], "periodic_adaptive_check_every": cfg["check"],
        "periodic_adaptive_min_gain": cfg["min_gain"], "hostname": socket.gethostname(), "exe": meta["exe"],
        "exe_sha256": exe_sha, "baseline_metadata_exe_sha256": meta.get("exe_sha256"),
        "profile_sha256": profile_sha, "tokens_sha256": tokens_sha, "args": args,
        "environment": meta["environment"], "preflight": before, "started_at": now(),
    }
    (arm_dir / "command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")
    env = os.environ.copy()
    env.update({str(k): str(v) for k, v in meta["environment"].items()})
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        proc = subprocess.Popen([meta["exe"]] + args, cwd=str(ROOT), env=env, stdout=stdout, stderr=stderr)
        exit_code = proc.wait(timeout=1800)
    after = preflight()
    stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
    metrics, gates, segments = parse_metrics(stdout_text, stderr_text)
    expected = expected_positions(arm)
    generated_positions = [int(x) for x in re.findall(r"strata periodic: prediction generated accepted_decode_tokens=(\d+)", stderr_text)]
    consumed_positions = [int(x) for x in re.findall(r"strata periodic: prediction consumed accepted_decode_tokens=(\d+)", stderr_text)]
    applied_positions = [int(x) for x in re.findall(r"strata periodic: cache swaps completed accepted_decode_tokens=(\d+)", stderr_text)]
    retired_count = len(re.findall(r"strata periodic: prediction usage retired", stderr_text))
    if cfg["check"]:
        lifecycle_complete = (
            generated_positions == expected and consumed_positions == expected and
            [g["pos"] for g in gates] == expected and
            len(applied_positions) == sum(g["decision"] == "ACCEPT" for g in gates) and
            retired_count == sum(g["decision"] == "ACCEPT" for g in gates) and
            all(g["swaps"] == 0 for g in gates if g["decision"] == "REJECT")
        )
    else:
        lifecycle_complete = (
            generated_positions == expected and consumed_positions == expected and
            applied_positions == expected and retired_count == len(expected)
        )
    checks = {
        "native_exit_0": exit_code == 0,
        "decode_1024": metrics.get("decode_tokens") == 1024,
        "prefill_seed_applied": "strata seed B: prefill forced applied swaps=" in stderr_text,
        "decode64_seed_applied": "strata seed B: decode64 forced applied swaps=" in stderr_text,
        "no_residual_strata_llama_or_wrapper": not after["processes"],
        "periodic_lifecycle_complete": lifecycle_complete,
    }
    result = {
        **command, "finished_at": now(), "exit_code": exit_code, "postflight": after,
        "metrics": metrics, "gates": gates, "segments": segments,
        "generated_positions": generated_positions, "expected_positions": expected,
        "consumed_positions": consumed_positions, "applied_positions": applied_positions,
        "checks": checks,
        "stderr_lines": [line for line in stderr_text.splitlines() if line.startswith("strata periodic") or line.startswith("strata segment")],
    }
    (arm_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (OUT_ROOT / "segments.csv").open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["arm", "accepted_decode_tokens", "window_end", "lookups", "hits", "misses", "hit_rate", "decode_tok_s", "cumulative_swaps", "cpu_pool_ms", "ranking_ms", "transfer_ms", "sync_ms", "gate_eval_ms"])
        if f.tell() == 0:
            writer.writeheader()
        for segment in segments:
            writer.writerow({"arm": arm, **segment})
    if not all(checks.values()):
        raise RuntimeError(f"invalid arm {arm}: {json.dumps(checks)}")
    return result


def main():
    if OUT_ROOT.exists() and any(OUT_ROOT.iterdir()):
        raise RuntimeError(f"benchmark output already exists and is non-empty: {OUT_ROOT}")
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    exe = Path(meta["exe"])
    profile = Path(meta["profile"])
    tokens = Path(meta["tokens_file"])
    if not exe.exists() or not profile.exists() or not tokens.exists():
        raise RuntimeError("benchmark input path missing")
    exe_sha = sha256(exe)
    profile_sha = sha256(profile)
    tokens_sha = sha256(tokens)
    if profile_sha != meta["profile_sha256"] or tokens_sha != meta["tokens_sha256"]:
        raise RuntimeError("profile or tokens hash differs from B metadata")
    results = []
    for arm in ARMS:
        results.append(run_arm(meta, arm, exe_sha, profile_sha, tokens_sha))
    summary = {"hostname": socket.gethostname(), "exe_sha256": exe_sha, "results": results, "finished_at": now()}
    (OUT_ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"hostname": summary["hostname"], "exe_sha256": exe_sha, "arms": [r["arm"] for r in results]}, indent=2))


if __name__ == "__main__":
    main()

