# Strata 下一步：保持現行輸出的軟體效能診斷

- Project Root: D:\strata
- Date: 2026-10-28 Asia/Taipei
- Scope: 使用者要求先回顧工作、再訂下一步；不換硬體，可能影響輸出的方向先排除。
- Authorization: 使用者後續明確授權 MT1 部署及更新 best；已完成部署。其他候選的 build/benchmark/部署不在本輪授權內。
- Git: 本機無 .git；不建立 repository，不需 commit/push。

## 已核對的狀態與新進展

讀取 .codex/handoffs/2026-10-28-strata-handoff.md、10/18 sampling/cache/CPU 交班、當前 ledger 尾段、LIVE_DEPLOYMENT.json、CAMPAIGN_CURRENT_BEST.json、WORKER-SKEW 報告與 analysis.json 摘要、IQ_ALLTYPES_NT1_MICROBENCH 與 IQ3S_MT1_AB 完整報告。

交班 staleness 工具回 STALE，原因為缺 Project Root metadata；這不是已證實內容過期。state/SESSION.md、TODO.md、DECISIONS.md、DEBUG_LOG.md 不存在，沿用實際受控檔案，不新增平行狀態體系。

Current best 已於本輪更新為 S2K+MT1：binary SHA256 385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5，MISS_OVERLAP=1、SPIN_US=2000、STRATA_IQ3S_MT1=1，STRATA_IQ_MT_MIN 未設；3153 GPU slots／20 GiB RAM／locked 20479 MiB。遠端獨立驗證已完成；實際 canonical source HEAD 於部署前為 e42e96ce1f2368835f466ebb67fd3189719b5dc3，build base 仍為 61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406，兩者不可混用。

重要更新：pack 的 gate/up 混合五種型別，不能把所有層視為 IQ3_XXS。最新逐型別微基準已有正面結果；MT1 的 Hermes replay 按輪 +4.26%（CI +2.15..+6.37），CPU -2.19 ms/window。使用者後續明確修正範圍：接受相同數學運算下浮點累加順序的微小差異，MT1 保留且優先於交錯方向；仍排除路由偏置、跳過 expert、重新量化。MT1 實際生成可能改變，不稱為逐位相同。先核對部署狀態與舊 best 的完整更新流程；本輪未執行部署草稿，也未自行授權其自動回滾。

## 優先接續：MT1 部署準備與 current-best 更新

已完成：本機 LIVE_DEPLOYMENT.json、CAMPAIGN_CURRENT_BEST.json、CURRENT_BEST_HISTORY.md 均指向 S2K+MT1，舊 S2K 全量快照保留。遠端 Strata-Task020-API 已指向 start_task020_api_s2k_mt1.ps1，priority 2；3/3 smoke 成功，環境、容量、AboveNormal、binary/config/launcher SHA 皆驗證。完整 receipt 在 state/mt1-deploy-20261028/out/ 與遠端同名 runs/ 目錄。遠端 deployment commit 6251a722f9c98fbfde3465cb5f4639de589a008b 已建立；push 因 wincredman／無互動認證失敗，不重試、不換認證來源。詳見該目錄 publication.json。

沿用 S2K 做法：保留舊 config/launcher 與受控快照，建立 MT1 config/launcher，核對程序與閒置後切既有 Strata-Task020-API action，保持 priority 2；驗證實際 binary SHA、env（MT1=1 且 MT_MIN 未設）、容量、AboveNormal、health 與 smoke。驗證成功後才更新 live/campaign 指標並追加歷史，並更新後續 harness 的 config/launcher/env identity。MT1 沿用 S2K binary，僅 SHA 不足以區分新舊 best。正式執行前需審查草稿及既有授權，不把本機文件當遠端完成證據。

## 結案與保留

- 不重跑：PATCH4、PIN/AA、timer resolution、worker/affinity/spin 掃描、P/E 依速度重分配，除非有新機制證據。
- RAM 淘汰策略已有冷/暖模擬，不能再稱只測過 LRU；收益小。全域跨層 RAM 配額是不同問題，但先列次選。
- GPU-only predictor prefetch 已有負面整機結果；不原樣重做。
- +3..6% 交錯收益及 +11% CPU 上限都是特定舊量測的推估，不是 S2K/Hermes 已驗證上限。

## MT1 之後：gate/up–down 交錯，先做可行性與保守上限

目的：判斷不同 expert 的 gate/up（偏解碼算力）與 down（偏頻寬）能否交錯，保持原 kernel、量化、浮點累加及最終 expert 合併順序。

1. 若之後授權遠端唯讀診斷，先確認 SSH host/hostname、遠端 AGENTS、process gate、current-best binary SHA、source identity/dirty state。出現未分類干擾程序即停；不自行停止 live。
2. 讀實際 S2K build source 的 native expert/pool 路徑，畫出 gate/up → activation/quantize → down → reduction 的資料依賴；列出 scratch 所有權、跨 expert 共用狀態與 barrier 原因。當前本機 src/ 缺 native_expert.cpp，不以其他檔案代替完整來源。
3. 先看既有 worker trace 是否保留逐 expert/phase 事件；analysis.json 是彙總，不能假裝可還原逐 expert 時序。若粒度不足，明列缺口，不臆造模擬結果，也不自行新增插樁 run。
4. 模型須同時計入 DRAM 共享上限、P/E 吞吐、down 必須等待完整 activation、dispatch/scratch 成本；不能把兩 phase 當成互不競爭資源，不能把 worker 閒置百分比直接當收益。
5. 交付一頁 GO/NO-GO：可交錯單位、需要改的檔案、保持數值順序的方法、保守可省 ms/window、Hermes 可遷移性、未知項。若連理想排程都不足 +3%，結案；若只有樂觀上限達標而無保守估計，標示證據不足，另擬最小測量計畫。

## 有條件的第二階段：尚未授權

僅第一階段 GO 且取得執行授權後，在獨立 source/build 內實作單一候選；先核對原 build identity，再核對候選與開關 off 的控制身分。保持 slots、RAM、temperature、路由及 MTP 設定，不加 fallback。

正確性先行：相同 frozen inputs 下，每 expert gate/up、activation、down 與最終 reduction 逐位相同；涵蓋五種 gate/up 型別、實際 down 型別、nt=1/2/3、P/E 路徑。發現任何不一致即停，不以「誤差很小」放行。

端到端另外檢查：suffix 決策使用 wall-clock，既有 A/A 本身亦會改變輸出。算子 parity 不等於端到端 parity；先建立同條件 A/A 的 token/decision 行為，若不能排除候選額外改變輸出，就維持未通過，不部署，也不藉修改 suffix 或 sampling 繞過限制。

效能計畫須事前固定、不能看中途顯著性任意停表；同工作負載與容量，輪替 paired blocks，使用既有 Hermes 10 點並保留 token 數/decision、CPU ms/window、accepted decode tok/s。沿用已驗證 runner 的必要能力前須審查，不直接執行部署草稿。門檻建議按輪提升 >=3% 且 95% CI 排除 0，另需上述正確性關卡；未達標不採用。

## 次選：依序，不並行啟動

1. 相同 RAM 總 bytes 的跨層配額：先離線 marginal miss-byte/cost curves；多工作負載驗證。不能用減少讀取比例直接當速度提升。
2. SSD useful bytes vs issued bytes：檢查 kGap 合併空隙、對齊放大與 read 後 memcpy 的關鍵路徑成本；先量，沒有足夠成本就不重排 pack 或改 buffer。
3. 路由偏置、跳過 expert、重新量化、硬體或系統功耗調整仍排除；相同數學運算的逐型別/逐核心 kernel 可保留為 MT1 後續，不要求逐 token 完全相同，但須核對數值差異與實際生成行為。

## Coverage / 未驗證

本輪完整讀取所列交班與兩份新 kernel 報告，ledger 做相關條目/尾段檢查，JSON 只讀指標或摘要。未全面掃描所有歷史報告、未重算大型原始 trace、未重新核算 MT1 raw 統計、未 SSH/查即時程序、未測速/編譯/部署、未停止程序。此檔是本機決策紀錄，不是遠端完成報告；未發布 GitHub。

## 下一個可直接執行的本機命令

```powershell
Get-Content D:\strata\state\NEXT_PLAN_EXACT_OUTPUT_20261028.md
```

讀後按第一階段範圍取得/確認執行授權，再做遠端 gate 與真正 source 檢查；不因本檔存在就自動 benchmark。
