# Fate trace provenance — 2026-10-18

Status: `BLOCKED_INPUT_INTEGRITY` for the Fate direction only.

The current local trace is `D:\strata\state\hermes-routing.frozen-01.bin`, 20,742,144 bytes, SHA256 `87CA2E3EA201E4AFEB27C415BBFC4927D67EFFC4ECFC6D97F1F3E94AA291509D`. The strict parser still stops at `ValueError: partial record payload`; the retry exit code was 1 and no JSON or Markdown result was created.

There is a provenance conflict with the older `LUNA-20261012-027.ram-screening-20261013.md`, which reports a different trace SHA256 (`a2a71e...`) and 12,569 complete 48-layer windows. That older identity cannot be assigned to the current local file.

I hardened the local Fate analyzer to accept the actual IQ pack v3 `native_experts.txt` layer-level schema. A unit check passed with 48 layers × 512 experts. Re-running the analyzer confirms the remaining failure is the routing trace payload, not the expert-size parser.

Scoped provenance checks found no additional local routing trace under `state`, `work`, `outputs` or `reports`. On `DESKTOP-LKMLUPC`, after a fresh identity/process gate (`PROCESS_GATE=NO_MATCH`), 2,329 source code files were scanned for route-trace capture terms with zero matches. The two scoped remote roots contained one filename matching trace/routing, `C:\Users\User\Strata-Adrian-control\runs\mtp-cost-trace-controller.log`, which is not a routing trace. This does not claim a full-disk scan.

Decision: do not truncate, patch, substitute or benchmark from this input. Obtain a complete trace through an approved capture flow. Fate remains a direction-specific input block; DoMoE evidence-ledger and reproducibility work continue.
