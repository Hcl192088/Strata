# AGENTS.md

Strata runs the Qwen3.8-Flash-Next mixture-of-experts model (and its Coder, Swift 1.5 and Unsloth variants) on a
normal PC: one NVIDIA or AMD graphics card plus system RAM, on Windows or Linux. It has a C++/CUDA/HIP engine
(`src/`, `include/`), a Python server with an OpenAI- and Anthropic-compatible API and a web app (`serve/`), and a
one-click installer (`setup.py`, started by `START-HERE.bat` / `setup.sh`).

## Installing Strata for a user

Follow **[docs/AI_SETUP.md](docs/AI_SETUP.md)**: check the PC, pick the model by RAM, run setup non-interactively,
start and verify the server, and connect the user's apps. Never expose the server beyond `127.0.0.1` without
`--api-key`. As an alternative to shell commands, Strata's MCP server ([docs/MCP_SERVER.md](docs/MCP_SERVER.md))
offers the same steps as tools.

## Working on the code

- How the engine works, every measured number, the API and all settings: [docs/DETAILS.md](docs/DETAILS.md) and
  the [paper](docs/paper/Strata-Paper.pdf).
- AMD (HIP) build and validation: [docs/AMD_HIP.md](docs/AMD_HIP.md); multi-GPU: [docs/MULTI_GPU.md](docs/MULTI_GPU.md).
- Setup's own tests run without a GPU or downloads: `python tools/test_setup_<name>.py` (for example
  `tools/test_setup_amd.py`, `tools/test_setup_choices.py`).
- Keep the docs' style: plain words, measured numbers with what they were measured on, no claims without a
  measurement.

## Codex session handoffs

- Store future Codex session handoffs in .codex/handoffs/ in this remote worktree (C:\Users\User\Strata-Adrian-control), not only in a local workspace.
- Treat the remote Git copy as authoritative for handoff state. After a handoff is verified, commit the task-scoped handoff/configuration changes and push them to the configured GitHub origin on the current branch.
- Keep handoffs executable and evidence-based; record verified facts, unresolved blockers, and the next command. Do not put secrets, tokens, cookies, or credentials in handoffs.
- Preserve unrelated worktree changes and do not modify or stop unrelated processes while preparing a handoff.

## Workspace layout and retention

- Use C:\Users\User\Strata-Adrian-control as the canonical Strata project root for source, documentation, handoffs, and small benchmark manifests. This is the user's GitHub fork clone; modify this repository directly.
- Use C:\Users\User\Strata only for large local archive/runtime staging. Do not treat it as a second source project or create new Strata test roots directly under C:\Users\User.
- Keep source, build, runtime, and result paths explicit in manifests. GitHub should contain source, documentation, handoff files, and small manifests; model weights, packs, MTP binaries, build outputs, and large logs stay local.
- Do not delete the IQ2 or v0.1.38 projects by name alone. The current IQ3 benchmark still uses the IQ2 project paths for the IQ2 tokenizer and the MTP runtime at packs\iq2_xs\tokenizer and mtp\rt, plus the v0.1.38 expert profile learned-heart.bin. Verify effective command references before moving or deleting any subdirectory.
- Treat archive moves as reversible first. Permanently delete only after the archived manifest and all active command references have been checked.
