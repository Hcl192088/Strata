# Current identity consistency audit — 2026-10-18

本機 controlled pointers 已交叉核對一致：

- binary SHA256：`366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2`
- actual build source HEAD：`61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`
- config SHA256：`C805B1206CDD23B22EE3CC66A80C52014EF9904CDB4314A6C6A17B8E00FFEA18`
- quantization：`IQ3_XXS`

`LIVE_DEPLOYMENT`、`CAMPAIGN_CURRENT_BEST`、paper gate、adapt-async contract 與 DoMoE matrix 全部一致；legacy IQ2 snapshots 仍標示為不可用 authority。

這是 local pointer consistency，不是 fresh remote revalidation。任何 capture、benchmark、build、resume 或 deployment 前仍必須重新核對遠端 hostname、process、source、binary、config 與 model。
