import json
a=json.load(open('analysis.json'));cm=a['cmp'];mt=a['metrics']
arms=list(mt);P=['p01','p05','p08']
def esc(s):return (s or '').replace('\n','⏎').replace('|','\\|')
def cell(x):
    if x is None:return 'n/a'
    return '相同' if x['identical'] else '不同 @%d'%x['idx']
def pct(x,y):return '%+.1f%%'%(100*(x/y-1))
C=mt['C'];C2=mt['C2']
L=[]
L+=['# GPU_SWITCH_EXACT_SCREEN 結果','',
'任務：LUNA-20261012-027 continuation；使用者授權的篩選（不做 A/B 速度跑）。env-only，無 source 修改、build、live config 改寫、push、GitHub 寫入。',
'遠端 run root：`C:\\Users\\User\\Strata-Adrian-control\\runs\\gpu-screen-20261029`；本機 raw：`D:\\strata\\state\\gpu-screen-20261029\\raw\\`（evidence.zip 206 檔 size/SHA 全數通過）。detached controller（排程 Strata-GPU-Screen-20261029）跑完 10 個 block，campaign.json phase=DONE、verdict=SCREEN_COMPLETE、restored=true、verified=true。','']
L+=['## 一、結論（分類）','','判定方法：C 與 C2 本身不同（見第二節），所以依 ledger 改用「首差位置與 A/A 首差比較」：某臂某題只要與 C 或 C2 其中一個相同的前綴，長度不短於 C 與 C2 彼此相同的前綴（p01 完全相同；p05 前 246 字元；p08 前 51 字元），就視為落在 A/A 噪音內；較早分歧、且對 C 與 C2 都早於基準，才算超出噪音。','',
'| 開關 | 分類 | 依據 |','|---|---|---|',
'| STRATA_DF_QB_Q4 | EXACT（A/A 噪音內，有限度） | p01 相同、p05 與 C 相同；p08 與 C 到 137 才分歧（基準 51），文字連貫 |',
'| STRATA_DF_BRANCH | EXACT（A/A 噪音內） | p01 相同；p05 對 C 分歧 @246（= C vs C2 基準）；p08 與 C2 相同 |',
'| STRATA_LFUSE | EXACT（三題與 C 逐字相同） | 唯一三題皆與 C 完全相同的開關 |',
'| STRATA_MMVF_ROWS | EXACT（A/A 噪音內） | p01 相同；p05 對 C @246、對 C2 @297；p08 對 C @60、對 C2 @51 |',
'| STRATA_ATTN_LANECELL | EXACT（A/A 噪音內） | p01 相同；p05 對 C @246、對 C2 @297；p08 對 C @51、對 C2 @147 |',
'| STRATA_GDN_SPLIT | UNCLEAR | p05 對 C 與 C2 都在 @136 分歧（早於基準 246），p01、p08 在噪音內；文字連貫、無迴圈，僅 1 題超出噪音，n 太小 |',
'| STRATA_TSUM | UNCLEAR | 同 GDN_SPLIT：p05 對 C 與 C2 都 @136，且與 GDN_SPLIT 的 p05 輸出彼此一致；其餘在噪音內 |',
'| STRATA_QFUSE | BROKEN | 三題都在前 7～15 字元分歧；p01 出現重複破碎（`" or change of direction" " or " or " or ...`，偵測器命中 `" or`）；p05 結尾語句破碎，p08 亦偏離 |','',
'限制：每臂 3 題 x 128 token（reasoning 多半被截斷），比對的是 reasoning_content 與 content 串接字串（首差為字元索引）；n=1 次，C 與 C2 本身有差異，所以「EXACT」指「未觀察到超出 A/A 噪音的偏離」，不是 bitwise 證明。engine log 沒有任何含開關名稱的行（switch-active-*.json 皆空），只能證明 engine 收到 env（meta.effective_env 與 harness 的 effective-env 斷言通過），不能證明每個 kernel 分支都實際走到。','']
L+=['## 二、C vs C2（A/A 基準）','','| 題 | C2 vs C | 首差 | 周圍（C2 / C） |','|---|---|---|---|']
for p in P:
    v=cm['C2|'+p]['vsC']
    if v['identical']:L.append('| %s | 相同 | - | - |'%p)
    else:L.append('| %s | 不同 | @%d（C2 長 %d、C 長 %d） | C2：`%s`<br>C：`%s` |'%(p,v['idx'],v['len'],v['reflen'],esc(v['this']),esc(v['ref'])))
L+=['','C 與 C2 在同一 live binary／config 下 p05、p08 就不同，所以單一 C 不能當 bitwise 基準；基準首差：p01 無、p05 @246、p08 @51。','']
L+=['## 三、各臂 x 各題比較','','| 臂 | 題 | 對 C | 對 C2 | 破碎/迴圈旗標 | 對 C 首差周圍（本臂 / C） |','|---|---|---|---|---|---|']
for k in arms:
    if k in('C','C2'):continue
    for p in P:
        v=cm[k+'|'+p];c=v['vsC']
        ex='-' if c['identical'] else '`%s`<br>`%s`'%(esc(c['this']),esc(c['ref']))
        fl='迴圈：'+v['loop'] if v['loop'] else '無'
        L.append('| %s | %s | %s | %s | %s | %s |'%(k.replace('STRATA_',''),p,cell(c),cell(v['vsC2']),fl,ex))
L+=['','人工檢視：QFUSE p01/p05 結尾明顯破碎（引號與 or 重複、語句不成句）；其餘臂的 reasoning 皆為連貫英文，無重複迴圈。偵測器（同 2～6 詞片段連續 4 次以上）只命中 QFUSE p01。finish_reason：C 為 stop/length/length；QB_Q4 為 stop/length/tool_calls；QFUSE 為 length/length/tool_calls。','']
L+=['## 四、粗略單次速度指標（n=1，3 題 x 128 token，非 A/B）','',
'來源：raw/rows.json（engine 計時）；pooled tok/s = Σtokens x 1000 / Σdecode_ms；ms/w、tokens/w 為總和相除；CPU ms/w、GPU-reach(gpu_wait) ms/w 以 windows 加權。僅為粗略指標，不構成速度結論、不用於候選判定。','',
'| 臂 | 與C相同題數 | tokens | windows | tok/s | vs C | vs C2 | ms/w | vs C | vs C2 | tok/w | vs C | CPU ms/w | vs C | GPU-reach ms/w | vs C |','|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
for k in arms:
    m=mt[k];n=sum(1 for p in P if cm[k+'|'+p]['vsC']['identical']) if k!='C' else 3
    L.append('| %s | %d/3 | %d | %d | %.2f | %s | %s | %.2f | %s | %s | %.3f | %s | %.2f | %s | %.2f | %s |'%(k.replace('STRATA_',''),n,m['tokens'],m['windows'],m['tok_s'],pct(m['tok_s'],C['tok_s']),pct(m['tok_s'],C2['tok_s']),m['ms_w'],pct(m['ms_w'],C['ms_w']),pct(m['ms_w'],C2['ms_w']),m['tok_w'],pct(m['tok_w'],C['tok_w']),m['cpu_ms'],pct(m['cpu_ms'],C['cpu_ms']),m['gpu_wait'],pct(m['gpu_wait'],C['gpu_wait'])))
L+=['','解讀限制：',
'- 只有輸出與 C 逐字相同的題，window／T 才可能一致、逐 window 比較才算 like-for-like；整臂三題全同的只有 LFUSE。即使如此，C 與 C2 的 windows 就差 %d vs %d、ms/w 差 %s、CPU ms/w 差 %s，單次噪音已大於多數開關間差異。'%(C['windows'],C2['windows'],pct(C2['ms_w'],C['ms_w']),pct(C2['cpu_ms'],C['cpu_ms'])),
'- 輸出不同的臂（含 QFUSE，其 tokens/windows 本身就不同：windows %d、tok/w %.3f）tokens、windows 與 T 分布不同，速度不可比。'%(mt['STRATA_QFUSE']['windows'],mt['STRATA_QFUSE']['tok_w']),
'- GPU-reach 各臂 %.2f～%.2f ms/w，C 為 %.2f、C2 為 %.2f，差異在噪音內；本次不支持也不否定「單開縮短 GPU 段」。'%(min(m['gpu_wait'] for m in mt.values()),max(m['gpu_wait'] for m in mt.values()),C['gpu_wait'],C2['gpu_wait']),'']
L+=['## 五、config 審核與環境','',
'- 八個開關 source getenv 位置沿用 gpu-bundle-20261029/RESULT.md 的證據；本次未重做 source 審核。',
'- controller 啟動前逐臂（C、8 個單開、C2）比對 config：與 live config 只允許該臂一個 env=1、per-block log 路徑、cwd 不同，config-audit.json 全數 equal_except_authorized=true。',
'- 每個 block 的 meta.effective_env：C／C2 只有 STRATA_NATIVE_PIPE=1、STRATA_IQ3S_MT1=1；單開臂另加且僅加該臂 env=1。10 個 block 皆 status=OK、PIPE ACTIVE、無 fatal／CUDA error／mismatch 文字、strict 容量 3153／20.00 GiB／20479 MiB、priority 32768（AboveNormal）、binary SHA A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8、config SHA 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93（controller identity 檢查）。max_tokens 128、無 PIPE_CHECK、無輪次／停止規則。',
'- 順序：C、DF_QB_Q4、DF_BRANCH、GDN_SPLIT、LFUSE、QFUSE、TSUM、MMVF_ROWS、ATTN_LANECELL、C2；每臂新引擎。','']
L+=['## 六、live 還原與獨立核對','',
'- 先刪舊排程 Strata-GPU-Bundle-20261029（Ready，紀錄於 raw/old-task-cleanup.json）。',
'- controller finally 還原 API：14:39:30 `API RESTORE OK`（restore.log）。final_verify.json 與之後另跑的 independent_verify.json 皆 verified=true：單一 strata.exe PID 18544、A1E6…、config 060F…、priority 32768（AboveNormal）、/health loaded（http://<tailscale-host>:8080）、/metrics expert_slots 3153／arena_mib 20479、env PIPE=1 且 MT1=1、八個開關皆無。',
'- 我的新排程 Strata-GPU-Screen-20261029 保留，狀態 Ready；無 controller 殘留。','']
L+=['## 七、原始檔','','- 本機 raw：`D:\\strata\\state\\gpu-screen-20261029\\raw\\`（campaign.json、rows.json、config-audit.json、out\\block-*\\resp-p*.json／meta.json／engine.log、final_verify.json、independent_verify.json、restore.log）',
'- 分析：analysis.json、analyze.py、report.py；controller.py、launch.ps1 為本次改編版。','- 未做：速度 A/B、source 審核、原始 token ID 比對（harness 未保留）。']
open('RESULT.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
