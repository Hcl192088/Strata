# R4 repair mechanism — partial result

TASK_ID: LUNA-20261012-027 direct-user continuation. STATUS: PARTIAL / REPORT_LOCAL. 使用者授權測試與 API 暫停恢復；本輪 API 未停。

四格 IQ3_S：每格 18 experts、6 layers，P/E、nt2/3；每格五輪 native / old R4 / lowreg 輪替，完整 GU→quant→actual down（Q2 type42 使用 act_quant_any/q2_rows_any）。每個格子對每個 expert 的 old R4/lowreg gate/up/h/down 全 bits 一致。相對 native，h 和 down 有大量 bit 差異，品質未通過；小誤差不等於非劣。每格完整 expert 的 native / lowreg median us 與速度差：P nt2 403.339 / 323.178 (+24.80%)；P nt3 450.411 / 388.839 (+15.83%)；E nt2 958.361 / 1012.050 (−5.30%)；E nt3 1176.161 / 1170.461 (+0.49%)。相對舊 R4 完整 expert：+6.75%, −0.02%, +6.09%, +8.66%，依上述格序。非同 input 完整 production pool，不含 repack、原 row 分配與 conversion；並存兩份 blob 只供測試，不代表容量過關。五輪非完整平衡輪序，不能用作整機加速結論。

| 範圍 | 狀態 |
|---|---|
| lowreg 對舊 R4 bits 和完整 expert 小篩 | TESTED；QUALITY_UNCONFIRMED 對 native |
| native-lane rounding 修復 | 未完成，非 NO_GO |
| packed-stream prefetch 單獨臂、熱迴圈 spill/load | 未完成 |
| HC 同精度成本／去重門 | 未完成；既有 profile 改 stream，不能當原排程暴露時間 |
| Q6 單矩陣成本／去重門 | 未完成；已核對 source 有 generic multi-token 與 head packed，未建立原排程 Q6 單項貢獻 |
| production pool、整機短篩／組合 | DEFERRED，前置品質與完整成本門未通過 |

遠端原始資料 C:\Users\User\Strata-Adrian-control\runs\r4-repair-20261030。binary SHA256 37D93AD668274A92BC308690D0154B93803C5ACF6C436896E265C7CBCF498671；raw log SHA256 lp2-nt2 36AFDA5D52A485414853DE56FDCD0EF1478D681390356BAACE7BCBB29EDB73EA；lp2-nt3 5FD82E33BB2F9DB95D8F601E4292793BA716AFAE2723F0A7F53B147EFB6EE4E6；lp15-nt2 A762CF972859941E4646BEE3DAD1A075F426F8407D206285C8795972A4A6059E；lp15-nt3 1AF990F084CB2301A2F41816DCA166D30FD369653974A45B5DCE270E043028F5。來源與 library SHA 見 inputs.json。

執行前後 current-best SHA A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8，config SHA 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93；source f520bc5 clean。獨立確認 11:19 API loaded、idle、queued 0、PID32568，3153 slots/20479 MiB，沒有 bench/build 進程，遠端 independent-verify-attempt2.json；首次 localhost API 驗證錯誤保留 independent-verify.json，因服務綁定 <desktop-tailscale-ip> 而修正位址。controller verify-postrun.json 另驗證 priority/env。未部署、未變更 sampling、未發布 GitHub。

## Additional completed screens

Four-arm packed-prefetch run C:\Users\User\Strata-Adrian-control\runs\r4-prefetch-20261030, executable SHA256 426B9668A32B33486CA4FF70D4D61726FD485EC2E28C68AA8A6348F43F137056. Four cells, 18 experts, 5 rotated passes, same full blob, actual down. Prefetch arm bitwise equals old R4 for all 18 samples per cell; lowreg-to-old bits separately established in first run. Complete-expert median us old→prefetch: P nt2 342.656→340.767 (+0.55%); P nt3 382.867→398.517 (−3.93%); E nt2 1057.794→1030.733 (+2.63%); E nt3 1244.156→1284.033 (−3.11%). Bounded single-distance screen NO_GO for expanding or combining prefetch: mixed and small; not a general prefetch impossibility. Raw hashes lp2-nt2 1427D3256B2A045991F8B17A27A8C8C56F00D86854BBA1344CF681C0E074C28B; lp2-nt3 C9FF32DC2280245DB5DA6AB192FD09DBE9757445A27426B2E7FF39A5D6FB2555; lp15-nt2 71C1DFE4D71764D159A69B8E04B3B1F0CAE6DE545F1AC429CBAA283780C899D0; lp15-nt3 4B14D505E58CEA4CDE2A924AAE1C4B926F94B031FD3A09FA6E3BB033B5A933E5.

Native exactness via per-expert full GU unpack into reused scratch then unchanged native GU and actual down: all 18 h/down outputs bitwise match native in each of four cells. Complete expert median native→unpack us: P nt2 386.767→1795.328 (21.54% native throughput); P nt3 441.789→1678.178 (26.33%); E nt2 966.606→3058.656 (31.60%); E nt3 1182.711→3240.517 (36.50%). This method is NO_GO at measured costs; it establishes only exact unpack/native path, not direct native-lane packed computation, and does not preclude a different implementation. Scratch reused but its memory and conversion are counted; it is not a production capacity validation. Raw C:\Users\User\Strata-Adrian-control\runs\r4-native-unpack-20261030; executable SHA256 926E7DA83F0C9AB0C61669B06A5F330B507AA8BC02D2C4B77C4D6B2BEAF9F42F; raw hashes lp2-nt2 86D49E1F99751D1047470766CF13DECF3F0C0A1A109353E9C8D3097C1C931458; lp2-nt3 72F5AD273B19D5ADFC4ACFA5E9DCF028A6765D84AE6F3B3DD54093BC22800C60; lp15-nt2 90F5AE2756A40C8C1A433A8A110222B94140B09AB034CDC3D9432382871EF612; lp15-nt3 982D4A333BE121FCD0FC5DF7668642B6E400F18C030D1566D17824B4C157885B.

HC evidence update: existing instrumented HC0 down 0.85–0.90 ms/window and up 0.83–0.85 ms/window across 3 requests (GDN+QSA); norm 0.34–0.35; HC1 remains grouped with router 2.50–2.61. This instrumentation disables shared side stream and DF_BRANCH; no original-schedule exposure or HC1-only bound. Source `fused_gr.cu` launch_multi already has plain/split/staged, per-token reuse, staged cp_async double buffering, and GR_DOWN_MAX4. HC new layout duplication check is partial; cannot establish unused waste, cost headroom or support prototype. Q6 source has generic multi-token path and head-specific packed layout; no original-schedule Q6-only timing or individual matrix headroom. Both are DEFERRED, not NO_GO.

Final independent receipt C:\Users\User\Strata-Adrian-control\runs\r4-native-unpack-20261030\independent-final.json SHA256 7837EC9CE0EBF3E9BA3210000D5CFEB2551BC208CE135939F578FB6BAB0B78E4; API remained running loaded/idle/3153/20479, binary/config matched. No restore was necessary. Controller postrun also checks priority/env. No source integration, deployment, or GitHub publication.

Remaining unfinished: direct packed native-lane/FMA prototype, hot-loop dynamic spill/load accounting, original schedule HC0/HC1 and Q6 cost isolation, complete variant deduplication; no production pool or combined engine run. This task is PARTIAL, not a complete plan execution. The tests did not establish a quality-qualified candidate with enough weighted cost evidence; no whole-engine speed claim.

## Parent final acceptance
2026-10-30：父層只於交付後驗收，未重跑 benchmark。抽驗 lowreg P/nt2、prefetch E/nt3、unpack P/nt2 raw SHA256 均符合報告；抽驗 bit/DONE/SUM 記錄。重新 strict-host SSH 核對 DESKTOP-LKMLUPC、最終 receipt SHA7837EC9C…B0B78E4、實體 BEST binary/config SHA 一致；API loaded/idle/queued0、3153slots/20479MiB、PID32568，只有已分類 API/watch，無 bench/build 殘留。接納三項有界微基準的已完成證據；不接納為 native 品質過關、整機加速或全計畫完成。HC/Q6、direct packed native-lane、動態 spill/load 與 production pool 仍未完成，STATUS 保持 PARTIAL/REPORT_LOCAL。父層只抽驗上述關鍵資料，未逐列重算全部 raw timings。
