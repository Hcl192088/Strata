# 10/14～10/28 證據補傳（2026-10-30 晚）

早上和下午的兩次上傳只涵蓋 10/29 之後；`plans-20261029-30/EXPERIMENT_LEDGER-20261030.md` 也是從 10/19 才開始記。這次補上更早、仍然影響判斷的實驗。只放報告、分析或結果 JSON、腳本和 patch；原始輸出、token、模型回應、程序盤點都不上傳，主機 IP 已遮掉。

- `archive-20261014-28/<資料夾>/`：各實驗的本機證據資料夾
- `reports-20261009-28/`：LUNA 任務報告與主題文件（上游比對、品質評估計畫、文獻掃描、開關盤點、worker skew 等）

## 先看這些
| 主題 | 位置 | 重點 |
|---|---|---|
| 動態 MTP 深度／信心門檻（AMTP、vLLM adaptive verification 同類） | `reports-20261009-28/LUNA-20261012-027.mtp-options-20261014.md`、`archive-…/mtp-*-20261014/` | 依 (1+q1+q1·q2)/cost 每輪選長度的原型 **−2.40%**（接受率 87%→89–93%，但 tokens/window 1.63→1.53）；live 本身已有 `--spec-min-p 0.75`；被拒位置 Top-2 rescue 0/41；T1/T2/T3 驗證成本 26.4/37.0/53.3 ms（pipeline 與 MT1 上線前） |
| 固定 MTP 深度 4 | `reports-…/LUNA-20261012-027.mtp-depth-20261014.md` | 三對全負，平均 −6.04% |
| CPU/GPU 時間軸 | `reports-…/LUNA-20261012-027.nsys-timeline-20261027.md`、`archive-…/nsys-timeline-20261027/` | GPU 真正工作 18.7 ms/w，其餘是 wait_flag_ge 自旋；只重疊 7%；層間資料依賴 |
| CPU 頻寬 roofline 與 worker skew | `archive-…/cpu-bw-20261028/`、`worker-skew-20261028/`、`reports-…/WORKER-SKEW-20261028.md` | DRAM 45.7 GB/s；gate/up 每核約 3.8 GB/s（卡在解碼運算）；E 群只晚 12.5% |
| SSD 讀取重疊 | `archive-…/miss-overlap-20261027/`、`s2k-confirm-20261028/` | MISS_OVERLAP 只回收 0–1.6 ms；短 spin（S2K）+6.5% 已上線 |
| 多 token CPU kernel | `archive-…/iq3s-mt1-ab-20261028/`、`mt1-deploy-20261028/` | MT1 +4.26% 已上線 |
| PCIe pin／adaptive async | `archive-…/next4-20261028/`、`pinaa-20261028/` | 確認輪全部無效 |
| 路由偏置（會改輸出） | `archive-…/cand-20261020/`、`reports-…/QUALITY_EVAL_PLAN_20261027.md`、`UPSTREAM_025_027_COMPARE_20261028.md` | 10/20 +15～60%，品質評估從未執行 |
