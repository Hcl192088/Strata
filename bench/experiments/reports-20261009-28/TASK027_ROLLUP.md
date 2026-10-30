# Task027 rollup

`LUNA-20261012-027` is the durable task identity. The files listed below are append-only local report artifacts and continuation evidence; this rollup does not replace or rewrite them.

## Canonical identity

- Task: `LUNA-20261012-027`
- Source: `coordination/task-027-file-tier-reuse-20261012`
- Locked commit: `da28699a382304ec8afc87a547f9c37123985f77`
- Plan: `coordination/TASK_027_CAMPAIGN.md`
- Plan SHA256: `c2e91c66497770ceed902e5e6070f0e065d35bca`
- Primary status: `BLOCKED`
- Primary decision: `ENV_BLOCKED`
- Primary report: [LUNA-20261012-027_REPORT.md](D:\strata\state\LUNA-20261012-027_REPORT.md)
- Publication: `REPORT_LOCAL_UNVERIFIED`; the local report contains a published marker, but the durable handoff state and available connector snapshot do not confirm publication.

## What is actually established

- The primary matched campaign measured candidate median `47.36 tok/s` versus control median `37.22 tok/s`, paired median delta `+28.01%`, across two pairs.
- The plan required clean control median `>=45 tok/s`; that gate failed, so the campaign stopped before confirmation, source change, deployment or promotion.
- The current IQ3 API deployment remains unchanged by this task.
- Continuations below are diagnostics, rejects, partial results or packaging; none is a promoted replacement for the deployed IQ3 baseline.

## Continuation index

| Local report | Observed status / decision | Raw evidence path |
|---|---|---|
| `LUNA-20261012-027.adapt-every-20261014.md` | `PARTIAL_ENV_BLOCKED_REPORT_LOCAL` | `C:\Users\User\Strata-Adrian-control\runs\adapt-every-20261014` and `runs\adapt-every-recheck-20261014` |
| `LUNA-20261012-027.api-diagnosis-20261013.md` | `PARTIAL_DIAGNOSIS` | `C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\diagnosis-cli-vs-serve-20261013` |
| `LUNA-20261012-027.decode-segments-20261015.md` | `REPORT_LOCAL; diagnostic only` | `C:\Users\User\Strata-Adrian-control\runs\decode-segments-20261015` |
| `LUNA-20261012-027.fixed-ram-20261015.md` | `runtime reserve gate failed; no deploy` | report contains evidence path/details |
| `LUNA-20261012-027.followup.md` | `COMPLETED_MEASUREMENT_NO_50PLUS_REPRODUCTION` | report contains evidence path/details |
| `LUNA-20261012-027.gpu-profile-20261015.md` | `DIAGNOSED_CPU_DEPENDENCY_NO_SOURCE_CHANGE` | `C:\Users\User\Strata-Adrian-control\runs\gpu-profile-20261015` |
| `LUNA-20261012-027.gu-tasks-20261015.md` | `REPORT_LOCAL; REJECT_NO_3PCT_GAIN` | `C:\Users\User\Strata-Adrian-control\runs\gu-tasks-20261015-r2` |
| `LUNA-20261012-027.gu-weighted-20261015.md` | `REPORT_LOCAL; no deployment` | `C:\Users\User\Strata-Adrian-control\runs\gu-weighted-20261015` |
| `LUNA-20261012-027.mtp-api-settings-20261014.md` | `REPORT_LOCAL` | `C:\Users\User\Strata-Adrian-control\runs\mtp-api-settings-20261014` |
| `LUNA-20261012-027.mtp-depth-20261014.md` | `REPORT_LOCAL; REJECT depth4` | `C:\Users\User\Strata-Adrian-control\runs\mtp-depth-20261014` |
| `LUNA-20261012-027.mtp-fixed-20261014.md` | `PARTIAL` | `C:\Users\User\Strata-Adrian-control\runs\mtp-fixed-20261014` |
| `LUNA-20261012-027.mtp-hnorm-state-20261014.md` | `PARTIAL; no clear end-to-end acceleration` | `C:\Users\User\Strata-Adrian-control\runs\mtp-hnorm-20261014` |
| `LUNA-20261012-027.mtp-options-20261014.md` | `REPORT_LOCAL` | `C:\Users\User\Strata-Adrian-control\runs\mtp-options-20261014`, `mtp-coupled-sampled-20261014`, `mtp-cost-trace-20261014`, `mtp-dynamic-gate-20261014` |
| `LUNA-20261012-027.mtp-pr1934-ab-20261015.md` | `REJECT_NO_3PCT_GAIN` | `C:\Users\User\Strata-Adrian-control\runs\mtp-pr1934-ab-20261015` |
| `LUNA-20261012-027.mtp-pr1934-package-20261015.md` | `COMPLETED_PACKAGING_NOT_DEPLOYED` | `NONE; packaging only` |
| `LUNA-20261012-027.offline-budget-20261015.md` | `offline/static diagnostic` | report contains evidence path/details |
| `LUNA-20261012-027.pap-live-20261015.md` | `REJECT current candidate; REPORT_LOCAL` | report contains evidence path/details |
| `LUNA-20261012-027.pool-split-20261015.md` | `REPORT_LOCAL; diagnostic decomposition` | `C:\Users\User\Strata-Adrian-control\runs\pool-split-20261015-r3` |
| `LUNA-20261012-027.pre-attention-20261013.md` | `blocked/diagnostic; no production promotion` | report contains evidence path/details |
| `LUNA-20261012-027.ram-screening-20261013.md` | `offline screening; no production policy change` | report contains evidence path/details |
| `LUNA-20261012-027.reclaim-ram-20261015.md` | `target NOT MET; no scheduled integration` | report contains evidence path/details |
| `LUNA-20261012-027.segment-diagnostic-20261015.md` | `historical storage audit; not built/enabled` | report contains evidence path/details |
| `LUNA-20261012-027.vram-prefetch-20261013.md` | `COMPLETED; REJECT GPU-only cross-layer pilot` | `C:\Users\User\Strata-Adrian-control\runs\vram-prefetch-20261013` |

## Next allowed research order after identity/process gate

1. Fate trace/offline cross-layer predictor diagnostic.
2. DoMoE profile/domain routing offline evaluation.
3. HOBBIT IQ3 miss-path feasibility only if RAM and quality gates are explicit.
4. ReMoE, CommitMoE and FloE remain research candidates requiring additional model/training or conversion conditions.

No item above authorizes a remote run by itself. Before each remote run, revalidate host, process inventory, source/build identity, current-best identity, temperature and matched workload.

## Coverage and limitations

- Checked: project `AGENTS.md`, handoff protocol, the live IQ3 audit/report, all `LUNA-20261012-027*.md` files currently in `D:\strata\state`, and their status/raw-path markers.
- Not moved or deleted: all legacy reports, outputs, work copies and raw evidence.
- Not checked in this organization pass: every byte of large remote logs, a fresh GitHub connector snapshot, or a fresh remote process/binary revalidation.
- Therefore this is a local coordination index, not proof of current remote liveness or GitHub publication.
