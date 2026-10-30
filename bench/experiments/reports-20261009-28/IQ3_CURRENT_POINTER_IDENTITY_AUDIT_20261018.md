# IQ3 Current Pointer Identity Audit — 2026-10-18 02:51 +08:00

- `LIVE_DEPLOYMENT` and `CAMPAIGN_CURRENT_BEST` both identify binary `366A355E...015E2`.
- The live pointer records `IQ3_XXS`; the campaign pointer remains controlled-baseline-only and makes no global-fastest claim.
- The two legacy IQ2 references are correctly rooted at `D:\strata\CURRENT_BEST.json` and `D:\strata\CONTROL_48T.json`; neither file exists now.
- The authority map was corrected to record those absent historical references rather than implying state copies exist.
- No remote operation, process stop, temperature change or fallback occurred.
