# Hermes CPU診斷與Windows I/O機制篩選

2026-10-29 約01:00；Task027直接夜間授權continuation。目標仍50tok/s；尚未完成夜間優化目標，不promotion。

## 完成的實測

遠端overnight-20261029 controller已DONE，90個正式請求（C/O/D各30）及3個probe。D的30請求2838windows完整對帳：CPU24.4965、GU11.8793、quant0.1438、down5.1629、join6.0902、LRU1.1957、殘差0.02459ms/window。GU48.49%、down21.08%、join24.86%、LRU4.88%。不是純解碼/SSD裝置service分解。

重疊項另列：helper9.6633、direct9.7495、copy1.7165、issue/wait8.0163、ready4.1681、inline0.09694ms/window。issued/useful=1.001657。不能相加或把helper整段當可省收益。

第一輪C/O priority不匹配已排除。後兩輪O/C差+3.72/-0.64%，均值+1.54%；D/O差+2.84/-4.57%，均值-0.86%。n=2且輸出window mix不同，不能證明無插樁擾動或小速度改善。phase accounting可信度由逐request守恆提供；分項仍是診斷binary的量測。

runner已透過原排程恢復MT1：PID27736，AboveNormal32768，binary385EF64E…30F5，configF23F1AAD…EB6F，health loaded、slots3153/arena20479、VRAM free254MiB。final_verify.json確認MT1 env1、無MT_MIN/DIAG。priority watcher隨controller退出，不再存在。API及memory-policy run/watch已逐PID/command分類；沒有殘留測試/build。

## 新的結構方向：未映射的direct讀取來源

來源：read_direct原始註解（本機targeted快照）描述NTFS mapped/cached GGUF可能序列化direct I/O；不先當本機實測結論。先做兩個256MiB shadow隔離probe，從第一shard16GiB位置複製相同bytes，NO_BUFFERING+OVERLAPPED讀寫；shadow原創與驗證都不走buffered讀取。兩檔SHA256同為fa06702107581931cc10f14359509fd9faaba98ee1366d1524c7f6e8ea57f3f5。API保持原MT1載入且不生成，沒有其他test/build。

初測：6輪交錯，QD16。512KiB unmapped/mapped吞吐比約3.037（相對+203.74%，paired95%CI+126.33..281.14%）；2MiB約1.572但CI跨0，不能以此單獨投全模型。

同檔確認：保持M檔mapped reference，U先unmapped六輪、後mapped六輪。512KiB U/M均值2.930→0.848；2MiB 1.619→0.892。兩檔完整direct hash再次通過。固定物理U檔一旦映射，優勢消失，支持mapping狀態是大差異來源；仍有不可逆時間順序、SSD cache與兩extent差異，沒有模型tok/s結論。全部24個初測cell、48個確認cell均保存，無挑樣刪除。

初測外層health誤打127.0.0.1（API bind<desktop-tailscale-ip>）且非terminating錯誤未阻擋probe；當時runner的final_verify、process、binary/config hash已核對。事後及確認試驗前均重新用正確bind核對loaded。沒有服務重啟或fallback。後續remote腳本ErrorActionPreference=Stop。

## 下一個必要行動

直接進候選實作/模型A/B，不再加小I/O掃描。最小方案：第一shard建立未映射byte-identical shadow，只有direct_讀取第一shard改用shadow；original mapping保留供其他用途，第二shard仍按原設計讀原檔。這是明確混合讀來源的候選，不是失敗後fallback。GPU resident、有效expert集合、CPU/GPU分流、RAM容量、quant bytes、sampling不變。

實作前重新process/identity gate。C盤實讀free69.37GB；原shard47.04GB+28.80GB，雙完整副本不合容量；只第一shard可留約22GB。需要direct-write copy、完整direct hash核對，不能用buffered hash將shadow放進file cache。若原尾長度不滿4096，須明確處理padding與prefix hash，不可猜對齊。

open_direct目前對paths_逐項CreateFileW，需確認第一shard精確path命中；選擇shadow時open失敗/大小不符/read失敗應fail closed，不能落入既有cached read/fill_stage替代。沒有shadow env時保留原流程。印出實際命中路徑和讀取counter，避免只有env沒有作用。診斷exe C7F41DF3…3FA54先保存到不可覆寫的命名檔，再進行候選增量build；不要覆寫current-best385E…30F5或live source。

candidate需驗證byte identity、MISS_OVERLAP_CHECK/rows、容量和protected GPU集合，先短probe再same-config C/O/S交錯A/B。計時開關另用診斷臂解釋join是否下降；性能主比較不加DIAG。若最終沒有顯著tok/s改善，保留MT1，不以I/O微基準宣告加速。重新登記正式實驗、配置AboveNormal不要再依賴繼承；單獨controller/watchdog最晚07:00結束自有tests、恢復原API。

## Checklist與coverage

1. 50 vs歷史46.9715，差1.2895ms/token、2.4745ms/window。
2. 最新Hermes自身D三輪CPU24.4965，使用本文件和原始30 phase紀錄；不套neuro。
3. 針對join6.09ms；理想全消除上限超過缺口，不把重疊issue8.02ms全算收益。LRU1.20即使全省仍不足缺口一半，不單獨投入長A/B。
4. 本輪是source計時與mapping機制，不連掃worker/affinity/spin；正式模型A/B才判定tok/s。
5. 不重做PIN/AA/PATCH4/MT_MIN/MTP gate，原先未映射讀源沒有本機模型A/B證據。
6. miss/預讀先保留，GPU placement受tail-skip限制；交錯計算排後，先攻已找到的大I/O差異；不改路由/量化/MTP數量。
7. 原估計scope錯誤已用decode快照修正；此次真正測出I/O mapping差異，接著驗證能否傳到模型join，不把微基準當最終成果。

實驗登記見ledger。沒有agent。remote controller與probe都已terminal，下一步仍須重盤點。coverage：90正式requests+3probe、30phase逐request檢查；IO初測24cells+確認48cells完整；僅targeted expert_source.cpp/open_direct/read_direct/LRU/source生命週期，未全面source audit。未做候選模型A/B、未改current-best、未commit/push這批資料。夜間目標保持active。
