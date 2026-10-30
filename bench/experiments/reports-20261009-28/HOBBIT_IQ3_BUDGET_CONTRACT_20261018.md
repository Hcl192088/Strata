# HOBBIT IQ3 budget contract — 2026-10-18

目前已驗證每個 IQ3 native expert 是 `83,814,400` bytes（約 `79.9255 MiB`）。20 GiB 只是理論上可容納 `256` 個 native expert blob，並不代表有 20 GiB 可用來放低精度副本。

未來 HOBBIT feasibility 必須先量到：baseline 實際 resident 使用量、KV/allocator headroom、低精度 artifact 的實際 bytes、staging metadata，以及 miss population。只有

`extra_copy_bytes <= usable_spare_bytes`

且 output parity、miss-path transfer timing、accepted decode tok/s 都通過，才有資格進入受控測試。現在 lower-precision artifact 不存在，因此 ratio、可放幾個副本與品質影響都保持 `UNKNOWN`，不做假設、不轉換、不增加 RAM。

本工作單元沒有遠端 run、quantization/RAM/source/model/scheduler/temperature 修改、process stop 或 fallback。
