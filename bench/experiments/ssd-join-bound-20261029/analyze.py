import sys,json,hashlib,collections
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import ram_policy_sim_20261018 as S
import simulate_ram_routing as B
D=Path('state/ram-policy-sim-20261018/capture-01');O=Path('state/ssd-join-bound-20261029')
old=json.loads((D/'warm_policies.json').read_text());cap=json.loads((D/'capture-result.json').read_text())
assert hashlib.sha256((D/'routing-dump.bin').read_bytes()).hexdigest().upper()==cap['dump_sha256']
meas=[float(x['done'].split()[-3]) for x in cap['results']]
base=old['policies']['LRU_engine'];errs=[(a/b-1)*100 for a,b in zip(base['mb_req'],meas)]
res={'trace_sha':cap['dump_sha256'],'validation':{'measured_MB':meas,'sim_MB':base['mb_req'],'error_pct':errs,'max_abs_error_pct':max(map(abs,errs))}}
assert max(map(abs,errs))<=20,'STOP_MODEL_UNTRUSTWORTHY'
rank=B.profile('state/trace-baseline-profile.bin');sizes=B.sizes('state/trace-native-experts.txt')
E=S.build_events(str(D/'routing-dump.bin'),rank,3153,old['bounds']);init,sel=S.init_sets_from(rank,3153,21474406400,sizes)
P=S.LruEngine(init,None);gpu=set(rank[:3153]);groups=iter(B.windows(D/'routing-dump.bin'));wcur=-1;g=None;prev=None
stats={n:collections.Counter() for n in ['previous_window_last_token','same_index_previous_layer']};mw=collections.Counter();bw=collections.Counter()
for item in E.timeline:
 if item[0]=='X':
  _,l,inn,out=item;P.exchange(l,inn,out,None);gpu.discard((l,out));gpu.add((l,inn));continue
 t,w,l,needed,routed,req=E.ev[item[1]]
 if w!=wcur:
  prev=g if req==getattr(P,'last_req',req) else None;g=next(groups);wcur=w;P.last_req=req
 misses=set(needed)-P.res[l]
 predictions={}
 if prev is not None: predictions['previous_window_last_token']=list(prev[l][-1])
 if l>0:
  c=collections.Counter(e for ids in g[l-1] for e in ids)
  predictions['same_index_previous_layer']=[e for e,n in sorted(c.items(),key=lambda x:(-x[1],x[0]))[:10]]
 for name,pred in predictions.items():
  z=stats[name];pr=set(pred);z['events']+=1;z['guesses']+=len(pr);z['routed_targets']+=len(routed);z['correct_routed']+=len(pr&routed)
  read={e for e in pr if e not in P.res[l] and (l,e) not in gpu};z['prefetch_reads']+=len(read);z['prefetch_bytes']+=len(read)*sizes[l]
  z['extra_reads']+=len(read-set(needed));z['extra_bytes']+=len(read-set(needed))*sizes[l]
  z['rescued_misses']+=len(read&misses);z['rescued_bytes']+=len(read&misses)*sizes[l];z['baseline_misses']+=len(misses);z['baseline_bytes']+=len(misses)*sizes[l]
 r0=P.reads;P.access(l,needed,routed,t,w);mw[w]+=P.reads-r0;bw[w]+=(P.reads-r0)*sizes[l]
res.update(windows=len(mw),ram_experts=len(sel),ram_bytes=sum(sizes[l] for l,e in sel),layer_blob_sizes=sorted(set(sizes.values())),ram_slots_layer=[len(x) for x in init],sim_reads=sum(mw.values()),sim_bytes=sum(bw.values()),per_window=[{'window':w,'misses':mw[w],'useful_bytes':bw[w]} for w in range(len(mw))])
res['policy_summary']={}
for name in ['LRU_engine','OPT_forced','OPT_bypass']:
 p=old['policies'][name];r=sum(p['reads_req']);h=sum(p['hits_req']);b=sum(p['mb_req'])*1e6
 res['policy_summary'][name]={'reads':r,'hits':h,'RAM_hit_rate':h/(h+r),'bytes_rounded':b,'misses_per_window':r/len(mw),'bytes_per_window':b/len(mw),'adaptive_extra_reads':sum(p['adapt_ssd_req'])}
res['prefetch']={}
for n,z in stats.items():
 z=dict(z);z.update(precision=z['correct_routed']/z['guesses'],recall=z['correct_routed']/z['routed_targets'],miss_recall=z['rescued_misses']/z['baseline_misses'],byte_recall=z['rescued_bytes']/z['baseline_bytes'],extra_bytes_per_window=z['extra_bytes']/len(mw),rescued_bytes_per_window=z['rescued_bytes']/len(mw));res['prefetch'][n]=z
ph=json.loads(Path('state/overnight-20261029/phases.json').read_text());rows=[x for x in json.loads(Path('state/overnight-20261029/rows.json').read_text()) if x['arm']=='D'];assert len(ph)==len(rows)
res['phase_by_point']={}
for pid in sorted(set(r['pid'] for r in rows)):
 pairs=[(p,r) for p,r in zip(ph,rows) if r['pid']==pid];win=sum(p['windows'] for p,r in pairs);miss=sum(r['m_file_blobs'] for p,r in pairs)
 z={k:sum(p[k] for p,r in pairs) for k in ['issued_bytes','useful_bytes','issue_wait_ms','join_ms']};z.update(windows=win,misses=miss,misses_per_window=miss/win,issued_bytes_per_window=z['issued_bytes']/win,useful_bytes_per_window=z['useful_bytes']/win,api_MB=sum(r['m_file_mb'] for p,r in pairs));res['phase_by_point'][pid]=z
p=json.loads(Path('state/overnight-20261029/phase_analysis.json').read_text());iw=p['separate_overlapping_ms_window']['issue_wait_ms'];gbw=p['issued_GB']/p['windows'];factor=iw/gbw
res['estimate']={'issue_wait_ms_per_GB':factor,'gap_ms_window':1.2,'required_GB_saved_window':1.2/factor,'required_fraction':1.2/iw}
for name,z in res['policy_summary'].items():
 f=1-z['bytes_rounded']/res['policy_summary']['LRU_engine']['bytes_rounded'];z['saved_fraction']=f;z['conditional_phase_issue_ms_window']=iw*f
for name,z in res['prefetch'].items():z['conditional_phase_issue_ms_window']=iw*z['byte_recall']
(O/'analysis.json').write_text(json.dumps(res,indent=2)+'\n')
res.pop('per_window');print(json.dumps(res,indent=2))

