# PCIE_BALANCE_PORT 衝突處理

Base：f520bc5e9d31c93caeb296b059e3a3eaa16e493f，獨立 pcie-balance-20261029 分支。
上游 patch：04be241a5a7ec016716cb50aab99be82a801e4fc，SHA256 29EC65BF4770ADFCD8C1D4AC055C67E14C9D9F1DA520359953B0AA1F5888C071。

10 個 rejected hunks（4 檔）：
- verify_kernels.hpp 1：base 無 fused wait-copy 宣告；只在原 wait_flag_ge 後新增 stamped 宣告，未引入 fused kernel。
- expert_source.cpp 2：base 無 PCIE_MIN1 上下文，固定 m 為 const；直接用 upstream pick 計算 const m。cpu_jobs=njobs 放在既有 pt(run) 前，保留 njobs1／MISS_OVERLAP 分段與 native pipeline 呼叫。
- verify.cpp 4：base 無 h_nf_，只在既有 host array 加 h_bal_；base 無 fused wait-copy／fuse_rows，原兩個 wait 位置加 conditional stamped wait；在原 staged launching 後清零 stamps。未引入不存在的 h_nf_、fused wait 或新 tail-skip 機制。
- generate.cpp 3：set_remote_expert_opt 後接 balance setter，保留 base native_head 判斷；base 無 req_img_keys，在原 req_pcie_frac 旁宣告 req_pcie_set；原 pcie_frac parser 分支設定該旗標。

其餘 hunks 自動套用（offset 差異留於原 apply 輸出）。完整 diff 已逐項閱讀，未修改 native pipeline／MISS_OVERLAP 的實作。

驗收所需最小額外輸出：上游只在 CLI generate 輸出 fit，Hermes 是 serve；於 serve 原 decode timing 前增加 balance-only 每 request 一行 PCIE_BALANCE fit，含 ready、ncpu/ngpu/ngpu_p、explore 及五個係數。無新環境開關、無改計算決策；balance OFF 不輸出該行。

Off 行為靜態檢查：model.on 預設 false、ready=false、pick 回傳原 fixed 值；未 setter 時 h/m_bal 均 null、原 wait kernel 不變、不配置 stamps、不 sample/solve。實際 bitwise 驗證待執行。
