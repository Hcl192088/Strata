# GPU_KERNEL_BW_DIAG（nsys GPU metrics）結果 — 2026-10-30 第 2 次（協調者自己執行）

- 授權：使用者「重跑」。terra 第 2 次只做完前檢就停（未停 API），協調者改 attempt-1 控制器為 controller2.py 執行。
- Identity：A1E6…91AD8／060F…93D93，live command 與 env 相符；prompt neuro.tokens SHA 9350…18BA（28912 token）。nsys 2026.5.1，`nsys profile` 全程收集，trace=cuda,nvtx，cuda-graph-trace=node，gpu-metrics ad10x 10 kHz。注入下 3135 slots（只記錄）。
- 執行：GEN 512 完整（DONE 512 length）；prefill 25.9 s；decode 292 windows、1.75 tok/w、39.51 ms/w、44.4 tok/s、GPU-reach 12.78、CPU 17.66、draft 2.16——與 live 正常值相近，trace 開銷小。
- 還原：API PID 5412、loaded、idle、3153、A1E6；一次性 task 已移除；無 nsys 殘留。遠端 trace2.nsys-rep（59 MB）、trace2.sqlite（824 MB）保留於 run 資料夾。
- decode 段：PP 最後一行（prefill 完）→ DONE，11.46 s，696k kernels，114.5k 取樣。

## 每 window（= 每 token ×512/292）
| 家族 | ms/window | DRAM 平均 | GB/s |
|---|---:|---:|---:|
| dense mmvq（*mmvq*） | 6.96 | 69.4% | 350 |
| HC（gr_*） | 3.66 | 66.2% | 334 |
| attention | 1.26 | 40.0% | 201 |
| GDN | 0.95 | 68.3% | 344 |
| router/topk | 0.25 | 22.9% | 116 |
| 其他（含 wait_flag_ge 16.3 ms/w） | 21.8 | 16.2% | 82 |

GPU 有 kernel 在跑的比例 86%，但其中 wait_flag_ge_kernel（GPU 端自旋等 CPU 旗標）佔 16.3 ms/w，不是計算。

## 前 10 kernel（ms/window、平均長度、DRAM%）
wait_flag_ge 16.3（114 µs，7.9%）；native_mmvq_il 1.75（51 µs，72.3%）；gr_down_staged 1.72（17 µs，68.7%）；gr_up_multi 1.68（17 µs，63.1%）；native_gu_multi 1.49（16 µs，39.3%）；native_mmvq_multi 1.30（14 µs，56.8%）；native_q5_k_mmvq 1.21（137 µs，86.7%）；attn_chunk 1.02（76 µs，37.0%）；native_down_multi 1.00（10 µs，25.8%）；native_q6_k_mmvq 0.96（28 µs，70.0%）。

## 限制
- 取樣每 100 µs 一點，數值是該 100 µs 的平均；比 100 µs 短的 kernel（gr_*、*_multi 約 10–17 µs）的百分比混入相鄰 kernel 與空隙，會被低估或高估，只能當粗估。長 kernel（q5_k 137 µs、mmvq_il 51 µs）較可信。
- 只量 DRAM 頻寬比例；attention、router 可能是計算或延遲受限，低 % 不代表能靠頻寬改善。

## 判讀（事前規則）
- dense 69%、HC 66%：落在 65–80% 之間，規則兩端都不觸發（不是 ≥80% 結案，也不是 ≤65% 設計）。
- 上限估算（提升到 85%）：dense 6.96×(1−69.4/85)=1.28 ms/w；HC 3.66×(1−66.2/85)=0.81 ms/w；合計約 2.1 ms/w（≈+5%）。若把 native_gu_multi／native_down_multi（GPU 上的 expert，2.5 ms/w、26–39%，但屬短 kernel 取樣模糊）也算進去，粗上限再加約 1.5 ms/w。
- 實際收益受限於 critical path：只有 GPU-reach wait（12.78 ms/w）那段會變快；GPU 自旋等 CPU 的 16 ms/w 不受影響。
