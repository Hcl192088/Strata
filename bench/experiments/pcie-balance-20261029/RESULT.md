[LUNA_BLOCKED]

# PCIE_BALANCE_PORT：移植與閘門通過，正式測試／復原待連線核對

TASK_ID：LUNA-20261012-027 continuation。STATUS：BLOCKED_CONNECTIVITY（2026-10-29 12:17:44 台北；SSH 自12:06起持續失敗超過10分鐘，依brief停止連線嘗試）。TASK_SOURCE：2026-10-29 使用者直接 brief（Claude planner），非新 GitHub claim；無 TASK_BRANCH／TASK_COMMIT_SHA coordination lock。本次明確禁止 GitHub writes／push，故未執行 publish。

已完成 port、fresh build、SMOKE3／CHK10 與 PIN8＋BALANCE 機制閘門。正式前兩輪已完成，最後成功遠端讀取時正執行第3輪 B8；目前無法連線，不能判定最終效能或 live 已復原。未改 live config、未修改遠端 main、未 push／寫 GitHub。

## Source／build identity

- hostname 實讀：DESKTOP-LKMLUPC。
- source worktree：`C:\Users\User\Strata-Adrian-control\runs\pcie-balance-20261029\source`；canonical root 為 junction，解析後是 `C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control`。
- base：`refs/tags/native-pipe-generic-20261029^{commit}`＝`f520bc5e9d31c93caeb296b059e3a3eaa16e493f`。同名 branch/tag 導致 shorthand ambiguous，已用完整 tag ref 確認。
- 新 branch：`pcie-balance-20261029`；commit：`4639ae8a61c870abde192e13f09c6b0489604977`；annotated local tag：`pcie-balance-port-20261029`；commit 後該 worktree 乾淨。
- upstream patch 由公開 `https://github.com/Niko1221/Strata/commit/04be241a5.patch` 直接存入新 run root，完整 upstream SHA `04be241a5a7ec016716cb50aab99be82a801e4fc`，patch SHA256 `29EC65BF4770ADFCD8C1D4AC055C67E14C9D9F1DA520359953B0AA1F5888C071`。沒有新增 remote、fetch、clone 或 mirror。
- fresh build：新 `runs\pcie-balance-20261029\build`，exit_code=0。沿用 deploy-prep build.cmd：VsDevCmd x64、NMake Makefiles、Release、CUDA arch89、STRATA_ENABLE_CUDA=ON、相同 FETCHCONTENT_SOURCE_DIR_STRATA_LLAMACPP、target strata、-j2；只替換 source/build/log 路徑。
- binary SHA256：`DF13A36431461CA117F105BE4588BBAA618C9357BD7281F812391547CD689EC2`。
- build.cmd SHA256：`CB71AEDDF41C50D19B7849BD42FE305F13E37636B01341CE894BF0DF3C0FA1CD`。
- 完整檔案 SHA：本機 `identity.json`；實際完整 diff：`ported.patch`。

## 衝突與 opt-in

原 patch 10 個 hunk reject／4 個檔案，逐一手工對照解決，詳 `CONFLICTS.md`：

| 檔案 | hunks | 解法 |
|---|---:|---|
| verify_kernels.hpp | 1 | base 無 fused wait-copy 上下文；只新增 stamped wait 宣告 |
| expert_source.cpp | 2 | base 無 PCIE_MIN1；直接以 pick 計算 const m；cpu_jobs=njobs 放原 pt(run) 前，保留 njobs1／MISS_OVERLAP／native pipeline |
| verify.cpp | 4 | base 無 h_nf_／fused wait；只加 h_bal_ 回收、兩處 conditional stamped wait、啟動前清零 stamps |
| generate.cpp | 3 | 既有 setter 後接 balance setter；在原 req_pcie_frac 旁宣告 request flag；原 pcie_frac 分支設定該 flag |

其餘 hunks 依 offset 自動套用，沒有引入上游不存在於 base 的 fused wait、PCIE_MIN1 或新 tail-skip 功能。完整 diff 已閱讀；native pipeline、MISS_OVERLAP 原實作未重寫。

上游 fit 原只在 CLI generate 結尾輸出，Hermes 使用 serve。為符合 brief 的機制證據要求，在原 serve decode timing 前增加每 request 一行 balance-only `PCIE_BALANCE fit`，輸出 ready／samples／explore 與係數；無新開關、無改決策。

OFF 靜態證據：model.on 預設 false，ready=false，pick 回傳原 fixed 值；不呼叫 setter 時 h/m_bal=null，原 wait kernels 不變，不配置 stamps、不 sample/solve。SMOKE／CHK 實測在 BALANCE OFF、PIN OFF 下證明 native pipeline 對 reference 位元一致；未另外執行完整 OFF binary 對原 binary 的全輸出等價測試。

## 已驗證 checks

| block | Hermes 題目／tokens 上限 | 結果 | gu/down coverage |
|---|---|---|---|
| SMOKE | p01/p05/p08 ×128 | OK、零 bitwise mismatch、PIPE ACTIVE | 全10組 |
| CHK | p01..p10 ×128 | OK、零 bitwise mismatch、PIPE ACTIVE | 全10組、missing=[] |

完整10組為 (16,20)、(16,42)、(17,20)、(17,42)、(18,20)、(18,42)、(21,20)、(21,42)、(22,20)、(22,42)。`check-*.json` 的 checks 是匹配進度行數；values 是各進度行累積計數相加，**不可解讀為不重複比較值總數**，本報告不使用該值作 coverage 結論。

機制 probe（p04/p05/p06 ×128；PIPE=1／PIN=1／PIN_GIB=8／BALANCE=1）：

- startup：registered=8.00 GiB、pinned=8.00 GiB、locked=12288 MiB、3153 slots／20.00 GiB；locked＋registered＝20480 MiB，嚴格容量通過。
- decode PCIe experts/層-window：1.68、1.00、1.27，皆 >0。
- 三題皆 `fit ready=1`；最後一題 ncpu=8737、ngpu=8784、ngpu_p=6240、explore=8742。
- 最後 fit：CPU_us＝433.604＋88.955*n_cpu＋0.000*n_pcie；GPU_us＝106.240＋186.108*n_pcie，log 明示 PCIe count per layer from these。
- PIPE ACTIVE，無 NATIVE_PIPE FATAL／CHECK MISMATCH；PIN 與 native pipeline 共存閘門通過。
- startup 仍有先前完整 page-locking refused 訊息，部分註冊隨後實際成功；本 gate 依實際 registered 與 decode 計數判定，未把拒絕訊息隱藏。

## 正式 A/B：目前可確認範圍

既有 harness 複製自 `runs\native-pipe-deploy-prep-20261029\harness`，沿用 Hermes requests、stop_api／restore_api、逐 block／逐 request process gate、每 block 新 engine、AboveNormal。config audit 驗證只容許 exe／cwd／log／臂開關差異；cwd=exe.parent。sampling 沿用 harness temperature=0，未變更模型溫度。C＝live binary＋PIPE1／MT1；P8＝新binary＋PIN8；B8＝新binary＋PIN8＋BALANCE。除 CHECK／probe 外 max_tokens=512。

| 輪次 | 順序 | 已取得 B8/C |
|---|---|---:|
| 1 | C→P8→B8，全部完成 | −2.2330698816036443% |
| 2 | P8→B8→C，全部完成 | −1.0850474942168287% |
| 3 | B8→C→P8；最後實讀為 B8 已載入 | 未取得 |
| 4–5 | 是否執行尚未確認 | 未取得 |

以上兩個比值來自遠端實讀 `round-deltas.json`，不是從逐題速率估算。前三輪停止規則尚無法核對；不得因前兩輪為負就宣稱觸發。

**未取得**：完整 rows.json、per-block pooled tok/s／ms/window／tokens/window／CPU ms/w／GPU-reach ms/w／PCIe與CPU experts/層、完整逐輪 B8/C／B8/P8／P8/C、95% CI／df與逐題 secondary。正式 rows 在遠端，尚未下載，未建立虛假的空 rows.json。無最終候選／無效結論。

## API 與連線

停機前 independently 實讀及 controller preflight 驗證：live engine PID31512，binary `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`；config `060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93`；AboveNormal；health loaded=true；3153／20.00／20479；PIPE=1／MT1=1。current-best 遠端 BEST.json 亦由 controller 檢查相符。

臨時排程工作 `Strata-PCIE-Balance-20261029` priority2，detached venv Python controller（psutil 可用），在 finally 執行既有 restore_api 與 final_verify；未修改 active config bytes。首次 prelaunch 因 Windows cp950 讀 UTF-8 BEST.json 失敗，當時 API 未停；明確指定 UTF-8 後通過，正式 controller 只啟動一次。

API 約11:42起依 stop_api 停止；最後成功讀取時（第3輪B8）仍停機。最後程序：controller PID26496／venv parent30052；B8 r3 server5332/5648、engine8524，command lines 都核對為本 run。無未分類干擾程序；無關一般服務只記錄、未停止。

12:06起 SSH timeout。12:07:41、12:10:40 本機實讀：作用中 Wi-Fi＝TANetRoaming（與 brief 的手機熱點不同），Tailscale 本機 offline／logged out，無法連 controlplane.tailscale.com／coordination server，TCP22=false。證據支持筆電端 Tailscale 連線故障；peer 清單的 desktop active 是既有本機視圖，不能視為即時桌機存活證據。未改網路、登入狀態或採其他通道。已通知使用者切回手機熱點。

**live API 目前狀態未確認；不能宣稱 restored。** finally 已寫入且 controller detached，但程式碼存在不等於恢復已成功。需恢復連線後讀 campaign／restore／final_verify 並獨立驗證。

## Coverage／剩餘工作

完整閱讀：指定本機規則／協調協定／ledger 相關條目／兩份報告；遠端 AGENTS、完整 upstream patch、完整移植 diff、衝突相關上下文、build flags、harness 的設定／process／停復機／request／capacity 路徑。實讀 hostname、tag identity、main dirty 狀態、live config／binary SHA與API狀態。main 既有工具變更與未追蹤檔原樣保留。

執行端完整 checks／mechanism 由 controller 讀整份 engine.log 驗證；本機已保存 checks summary／mechanism／identity／diff，**尚未下載完整 engine logs／正式 rows 來作獨立 audit**。build.log 只讀 tail 與 exit_code，未逐行審閱完整 warning；整個 source tree／模型／自然語言 responses 未全面 audit，未做模型大檔 hash；不是全倉庫審計。大型檔不複製 source/build/model，原始權威位置留在遠端。

恢復連線後先 process gate，讀現有 campaign／wrapper.done／restore／final_verify，勿重啟 controller／重跑 benchmark。若仍執行就等待；完成後獨立驗 live、收集 raw、計算全部統計、補完本報告並 append ledger。臨時排程工作尚未移除，避免在狀態不明時影響仍執行的 controller。

## Raw paths

- 遠端：`C:\Users\User\Strata-Adrian-control\runs\pcie-balance-20261029`，junction實體路徑 `C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control\runs\pcie-balance-20261029`。
- root：upstream.patch／ported.patch／rejects／identity.json／build.cmd／build.log／build-result.json／controller.py／campaign.json／rows.json／round-deltas.json／processes-*.json／inputs.json／config-audit.json。
- checks：out/block-00-SMOKE-r0、block-01-CHK-r0、block-02-MECH-r0。
- 已完成正式：out/block-03-C-r1、04-P8-r1、05-B8-r1、06-P8-r2、07-B8-r2、08-C-r2；最後實讀09-B8-r3。
- 本機：`D:\strata\state\pcie-balance-20261029`（identity／ported.patch／CONFLICTS／check-SMOKE／check-CHK／mechanism／network-status／CHECKPOINT／執行與收集分析腳本）。

截止追加：12:17:44 本機 tailscale status 仍顯示 offline／logged out／無法連 coordination server；network-status-final.txt 與 network-profile-final.json 已保存。此時停止筆電端後續遠端操作；遠端 detached controller 是否完成、是否觸發第3輪停止規則、API是否復原皆未確認。恢復連線後只能先盤點及讀既有狀態，不重跑。


## 協調者補收（2026-10-29 12:25）
連線恢復後核對：controller phase=DONE，第 3 輪後依停止規則結束（B8/C −2.23、−1.09、−0.99%），12:13:41 API RESTORE OK；live 獨立驗證 A1E6／060F／AboveNormal／loaded／PIPE=1／MT1=1。rows.json 已下載。B8/C 平均 −1.43%（CI −3.15~+0.28，df=2）；B8/P8 +0.60%（CI −1.96~+3.17）；P8/C −2.02%（CI −3.90~−0.14）。判定 STOPPED，非候選。詳見 ledger。
