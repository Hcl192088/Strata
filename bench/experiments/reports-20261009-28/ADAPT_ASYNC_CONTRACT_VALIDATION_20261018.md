# Adapt-async contract validation — 2026-10-18

離線核對結果：contract 的 binary/source/config/model identity 與受控 IQ3 baseline 一致，且只允許未來候選加入 `--adapt-async 1`；scheduled API 沒有被觸碰。

但 runner 仍未 ready。最新 scoped preflight 沒有找到 executable、serve runner、request harness 或 raw log；contract 定義的 asynchronous startup、exchange buffer、實際 adaptive swaps 與 matched pairs 都還沒有 runtime proof。因此目前結論是 `CONTRACT_VALID_RUNNER_NOT_READY`，不是 benchmark、deployment 或 promotion。

下一步只能是取得同 source 的 isolated runner，或繼續離線 ledger/state validation。`iq3-ram-adapt-013` 仍只是 source-backup-only，不能當 fallback。
