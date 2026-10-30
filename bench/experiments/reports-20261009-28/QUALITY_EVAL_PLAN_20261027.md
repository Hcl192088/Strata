# 路由偏置三臂 task-level 品質評估計畫（草稿，2026-10-27，未執行）

狀態：DRAFT，等使用者核可。核可前不改 harness、不連遠端、不跑任何東西。

## 1. 目的與要回答的問題

10/20 的 replay 顯示三個臂速度大幅提升，但都改變了輸出，品質沒評估：

| 臂 | binary | env | 10/20 速度（paired vs C） |
|---|---|---|---|
| CRP25 | control `366A355E..15E2` | `STRATA_ROUTE_PRIOR=0.25` | +15.7%（campaign A） |
| DB25V100 | candidate `89380A69..F923` | `STRATA_ROUTE_BIAS=0.25`, `STRATA_ROUTE_BIAS_VRAM=1.0` | +39.3%（campaign C） |
| DG100 | candidate `89380A69..F923` | `STRATA_GATE_COUNT=1`, `STRATA_GATE_SKIP=0.1` | +41.3%（campaign C） |
| C（對照） | control `366A355E..15E2` | 無 | 37.64 tok/s |

問題：在實際 Hermes 工作上，哪些臂的品質「不比 control 自己跟自己比的差異更差」？

關鍵前提：control 本身不是 bit-exact（10/20 C-vs-C 只有 9/30 完全相同、prefix 0.37），所以不能用「輸出相同」當標準，必須拿 **C-vs-C 的差異當基準線**，判斷各臂的差異有沒有超出這條線。

## 2. 題目集（60 題）

| 類別 | 題數 | 來源 | 評分方式 |
|---|---:|---|---|
| A. Hermes 工具選擇 | 20 | Hermes DB 唯讀副本（同 10/19 做法），含現有 p03/p07/p08/p09/p10 | 自動：工具名稱與參數 |
| B. Hermes 多輪（最後一則是 tool 結果） | 10 | 同上，含 p04/p06 | 盲測兩兩比較 |
| C. Hermes 一般問答／開放題 | 10 | 同上，含 p01/p02/p05 | 盲測兩兩比較 |
| D. 有標準答案的客觀題 | 20 | 新寫：繁中數學／邏輯 8、程式小題 6、事實／單位換算 6 | 自動：比對答案 |

- A–C 從原本 10 題擴到 40 題：10 題太少，一題翻轉就是 10%。
- D 用來抓「推理能力變差」：路由偏置改的是 expert 選擇，可能讓模型算錯，但 Hermes 題目看不出對錯。
- 已知限制（沿用 10/19）：DB 不存 tool schema，是從過去的呼叫重建的，工具行為只是近似。
- 隱私：Hermes 題目含私人訊息，只放在本機 `state/` 和遠端 runs，不上 GitHub。

## 3. 抽樣設定與設計

- **用 production 抽樣**（temperature 1.0、top_p 0.95、top_k 20、min_p 0、enable_thinking、reasoning_effort medium），`max_tokens` 1024（server `--max-new` 1024）。理由：品質要看使用者實際碰到的情況；10/20 的 greedy 不代表 production。D 類客觀題同樣用 production 設定。
- 臂：C、CRP25、DB25V100、DG100，各 **3 輪**，交錯排序，每個 block 都是新的 engine（沿用 `replay_ab_20261020.py` 流程）。
- 不放 D（candidate binary、不開旋鈕）：10/20 campaign B 的 D 對 C 是 -0.5%，一致度 10/30，跟基準線相同，已有證據顯示 candidate binary 本身是中性的。如果要更嚴謹可以補 2 輪，時間 +約 1 小時。
- 總量：4 臂 × 3 輪 × 60 題 = 720 個請求，12 個 block。
- 時間估計：10/20 每個 block（10 題、greedy、512 token）約 3.3 分鐘；改成 60 題、1024 token、含 6–9k prompt 的 prefill，估計每 block 25–35 分鐘 → **總計約 5–7 小時，排夜間跑，上限 8 小時**。期間 live API 會停，由 runner 的 finally 恢復。
- 順帶記錄 tok/s 和 SSD MB／請求，但這是次要指標，不拿來做結論（抽樣模式下雜訊較大）。

## 4. 指標與判定標準（事前登記，跑完不改）

每臂對 C 計算，並用 C 自己 3 輪之間的比較當基準線。

1. **硬失敗**（自動）：工具呼叫 JSON 無法解析、呼叫不存在的工具、`finish=length`、重複迴圈（同一個 20-gram 出現 ≥3 次）、空回答、語言漂移（以英文或簡體回答繁中提問）。
   - 判定：該臂 180 個輸出的硬失敗數 ≤ C 的硬失敗數 + 3。
2. **工具選擇（A 類，60 個輸出／臂）**：C 三輪出現過的工具，加上人工標記為合理的工具，構成「可接受工具集合」。
   - 判定：該臂工具名稱落在集合內的比例 ≥ C 的 leave-one-out 比例 − 10 個百分點。
3. **客觀題正確率（D 類，60 個輸出／臂）**：
   - 判定：該臂正確率 ≥ C − 5 個百分點（約等於 20 題少對 1 題）。
4. **盲測兩兩比較（B＋C 類，60 個輸出／臂）**：評審看到請求和兩個答案（隨機標 X／Y、不知道哪個是哪個臂），判斷較好／相當／較差，並寫理由。混入 C-vs-C 配對做校準。
   - 淨負分 = 判「臂較差」比例 − 判「臂較好」比例。
   - 判定：臂的淨負分 ≤ C-vs-C 淨負分 + 10 個百分點。
   - 評審：Sonnet subagent（不另花 API 費用，用的是 Claude 額度）。使用者抽查 10 組，包含所有判「較差」的配對。
5. **整體結論**：四項都過才算「品質通過」。通過的臂裡選最快的，作為下一步候選。

提早停止：第 1 輪結束後，如果某臂硬失敗已經 ≥ C + 6，後面兩輪就跳過該臂，省時間。

這份計畫**不包含**正式部署：通過的臂要另外擬部署計畫，並在 live API 上做 A/B，再請使用者授權。

## 5. 執行前要做的本機準備（核可後才做）

- `tools/replay_ab_20261020.py`：題目清單改成可設定（現在寫死 `p01..p10`）；`make_body` 支援 production 抽樣參數；`max_tokens` 1024。
- 新增 `tools/quality_score_20261027.py`：計算硬失敗、工具選擇、客觀題正確率，並產生盲測配對（打亂順序、記錄對照表）。
- 題目抽取：從 Hermes DB 唯讀副本抽出 30 題新題（沿用 10/19 的重建方式）；DB 副本的路徑執行前先確認。D 類 20 題連同標準答案寫成 `state/quality-eval-20261027/objective.json`，先給使用者看。
- 先用假的回應測一遍評分程式，不連遠端。

## 6. Identity gate（照 AGENTS.md）

- 開跑前與每個 block：遠端 hostname DESKTOP-LKMLUPC、control SHA `366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2`、candidate SHA `89380A695369409F129AA086DC884CEAF5E0A6CC30113D6400EDF4134336F923`、容量 gate（slots 3153／20.00 GiB／locked 20479 MiB）。
- 記錄 60 題請求檔與每臂 config 的 SHA256。
- 開跑前、每個 block 前後都盤點程序；有未分類程序就停在 process gate。
- 結果寫入最近相關 task（LUNA-20261012-027 系列，執行前重新核對）的 follow-up，append-only；不寫 GitHub，除非使用者另外要求走兩階段 outbox。
- 長時間監看時，SSH 連續失敗超過 10 分鐘就停止重試，查清是哪一端後回報。

## 7. Ledger 預登記（核可後寫入 EXPERIMENT_LEDGER.md）

## 2026-10-27 xx:xx｜路由偏置三臂品質評估
- 類型：結構（家族：路由偏置；評估，不改 source）
- 假設：如果 CRP25／DB25V100／DG100 在 Hermes 與客觀題上的差異不超過 C-vs-C 基準線，則可以把 decode 從 37.6 提升到 43–53 tok/s 而不降低品質，因為這三臂只動低權重或可替換的 expert
- 目標段／上限：waitCPU（10/15 profile 約 10.4 ms/token；拆解已過期）→ 已實測 +16～41%
- 指標：硬失敗、工具選擇、客觀題正確率、盲測淨負分（見計畫第 4 節）
- 設計：60 題 × 4 臂 × 3 輪，交錯，production 抽樣
- 停止條件：第 1 輪硬失敗 ≥ C + 6 的臂停止
- 結果：（待填）
