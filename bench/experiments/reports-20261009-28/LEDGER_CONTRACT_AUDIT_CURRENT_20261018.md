# Current Ledger Contract Audit — 2026-10-18

The previous ledger audit reported only 22 rows and was stale. A fresh audit now covers all 46 current EXPERIMENT_INDEX.jsonl rows, including this audit's own index entry, the DoMoE overlap diagnostic, its priority manifest and the authority map.

All 46 IDs are unique. Required fields are complete, every local evidence path exists, all remote_run_started values are boolean false, and no row makes an unsupported global-fastest claim. Historical ID naming patterns are retained as legacy information, and protective wording such as NO_UNSUPPORTED_GLOBAL_STATUS is not treated as a global claim.

This proves the local coordination contract and evidence-path presence only. It does not prove remote benchmark correctness, paper reproduction, or current performance. The campaign remains active with four direction-level soft blockers and no hard blocker.
