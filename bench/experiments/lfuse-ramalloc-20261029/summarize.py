import json,statistics
from pathlib import Path
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text(encoding='utf-8-sig'))
pairs=load('pairs.json');rows=[x for x in load('rows.json') if 1<=x['round']<=6]
assert len(pairs)==6 and len(rows)==120
arms={}
for a in ('C','F'):
 r=[x for x in rows if x['arm']==a];assert len(r)==60 and all(not x['error'] for x in r)
 windows=sum(x['windows'] for x in r)
 arms[a]={'requests':len(r),'tokens':sum(x['m_out_tokens'] for x in r),'decode_ms':sum(x['m_decode_ms'] for x in r)}
 arms[a]['pooled_tok_s']=arms[a]['tokens']/arms[a]['decode_ms']*1000
 for k in ('ms_window','gpu_wait_ms','cpu_ms','tokens_per_window'):
  arms[a][k]=sum(x[k]*x['windows'] for x in r)/windows
points=[]
for p in sorted({x['pid'] for x in rows}):
 rates={a:sum(x['m_out_tokens'] for x in rows if x['pid']==p and x['arm']==a)/sum(x['m_decode_ms'] for x in rows if x['pid']==p and x['arm']==a)*1000 for a in arms}
 points.append({'point':p,**rates,'delta_percent':100*(rates['F']/rates['C']-1)})
result={'status':'STOPPED_BY_USER_NO_PROMOTION','completed_pairs':6,'formal_requests':120,'smoke_requests':9,'excluded_partial_round':7,'mean_pair_delta_percent':statistics.mean(x['delta_percent'] for x in pairs),'negative_pairs':sum(x['delta_percent']<0 for x in pairs),'arms':arms,'per_point':points,'full_preregistered_8round_CI':'NOT_COMPUTED_USER_STOPPED','quality':'NO_OPERATOR_OR_SEMANTIC_PARITY_PROOF','restoration':load('independent-poststop-verify.json')}
(R/'RESULT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
table='\n'.join('|%d|%.3f|%.3f|%+.3f%%|'%(x['round'],x['C_tok_s'],x['F_tok_s'],x['delta_percent']) for x in pairs)
text=f'''# Task027 continuation: RAM quota / LFUSE

Status: STOPPED_BY_USER_NO_PROMOTION; REPORT_LOCAL. User requested early termination on 2026-10-29. No deployment.

LFUSE: six complete paired rounds / 120 formal requests, plus C/F/C smoke nine requests. Mean paired speed change {result['mean_pair_delta_percent']:+.3f}%; five of six rounds negative. Pooled C {arms['C']['pooled_tok_s']:.3f}, F {arms['F']['pooled_tok_s']:.3f} tok/s (different token totals, so primary is the paired-round mean). No useful acceleration observed; reject candidate for this configuration. This is not the preregistered eight-round result; no full-test CI or statistical significance claim.

|Round|C tok/s|LFUSE tok/s|Change|
|---|---:|---:|---:|
{table}

Coverage: all ten captured Hermes points in each of twelve complete fresh-engine formal blocks. Original temperature1.0/top_p.95/top_k20/min_p0/seeds1001..1010 preserved; max_tokens512 only. Same A1E6...91AD8 binary/config060F...93D93,3153slots/20GiB/20479MiB,AboveNormal; only candidate env STRATA_LFUSE=1. Complete blocks passed runtime/capacity/error/repetition guards. Source contract and smoke do not prove operator bitwise or semantic quality parity. Current runtime branch activation has no dedicated kernel counter. Partial round7 C six responses remains raw and is excluded; round7 F and round8 not run. Raw remote runs/lfuse-ab-20261029-attempt2; no private prompts/responses copied into this report.

Termination engineering record: stop.py first checked ownership but failed while inspecting an expired distant ancestor; it did not terminate any process. Its presence was detected by the live benchmark process gate, which stopped partial round7 and invoked existing cleanup/finally restore. A second stop check found campaign already restoring and performed no termination. Raw campaign phase FAILED/PROCESS_GATE is preserved, not rewritten as normal completion; analytical status STOPPED_BY_USER is separate. No unrelated process stopped. Initial attempt1 C smoke stopped because our broad MISMATCH guard matched normal check_mismatch_rows=0; guard corrected before fresh attempt2, old run retained and excluded.

Original API restored at19:30:12; independently rechecked PID1356,loaded,idle,AboveNormal,current-best binary/config hash,all original env,3153slots/20479MiB. No test process remained at independent process gate. No temperature/source/live-setting change.

RAM quota bounded offline screen: full8623-window old neuro trace/all48layers,engine-LRU baseline matched all11 requests. Training requests0-4 to heldout5-10 reduced SSDbytes14.1055%,below25%gate. All-data finite-grid conservative DP18.6909%,not a global upper bound. No live allocation change or tok/s forecast. Full coverage/limitations in RAM_RESULT.md.

Publication: reports remain local and in the same remote run directory. Earlier automatic approval review rejected report commit/push pending explicit payload-to-GitHub approval; no retry or alternate publication. No GitHub publication or deployment.
'''
(R/'RESULT.md').write_text(text,encoding='utf-8')
print(json.dumps({k:result[k] for k in ('status','completed_pairs','mean_pair_delta_percent','negative_pairs')}));print(json.dumps(arms))
