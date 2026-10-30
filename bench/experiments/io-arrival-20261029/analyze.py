import json,re,statistics,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
root=R/'raw'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
rows=load(R/'D-rows.json');assert len(rows)==10 and all(not r.get('error') for r in rows)
log=(root/'engine.log').read_text(encoding='utf-8',errors='replace')
phase=[]
for line in log.splitlines():
 if line.startswith('CPU_PHASE_DECODE '):phase.append({k:float(v) for k,v in re.findall(r'(\w+)=([\d.]+)',line)})
assert len(phase)==10
batches={};dispatch=[];begin={};end={}
trace=root/'arrivals.csv'
for line in trace.read_text().splitlines():
 tag,*a=line.split(',');a=list(map(int,a))
 if tag in ('B','E'):
  assert len(a)==2;(begin if tag=='B' else end)[a[0]]=a[1]
 elif tag=='I':
  req,bid,nq,nf,cb,ce=a;assert bid not in batches
  batches[bid]={'req':req,'nq':nq,'nf':nf,'copy_begin':cb,'copy_end':ce,'q':{},'w':[]}
 elif tag=='Q':
  req,bid,q,size,submit,lo,hi=a;b=batches[bid];assert req==b['req'] and submit<=lo<=hi<=b['copy_begin']<=b['copy_end']
  assert q not in b['q'];b['q'][q]={'size':size,'submit':submit,'lo':lo,'hi':hi}
 elif tag=='W':
  req,bid,dst,q,offset,n=a;assert req==batches[bid]['req'];batches[bid]['w'].append((dst,q,offset,n))
 elif tag=='D':
  assert len(a)==13;dispatch.append(dict(zip(('req','layer','b0','b1','start','ready_end','bulk_ready','cold_begin','cold_end','nready','ncold','npend','split'),a)))
 else:raise AssertionError(('UNKNOWN_RECORD',tag))
assert sorted(begin)==sorted(end)==list(range(1,11))
assigned=set();details=[]
for d in dispatch:
 assert begin[d['req']]<=d['start']<=d['cold_begin']<=d['cold_end']<=end[d['req']]
 bs=[batches[i] for i in range(d['b0']+1,d['b1']+1)]
 assert all(b['req']==d['req'] for b in bs)
 ids=set(range(d['b0']+1,d['b1']+1));assert not assigned&ids;assigned|=ids
 expert=[];intervals=[]
 for b in bs:
  assert len(b['q'])==b['nq'] and set(b['q'])==set(range(b['nq']))
  groups={}
  for dst,q,off,n in b['w']:
   assert q in b['q'];groups.setdefault(dst,[]).append((q,off,n))
  for dst,win in groups.items():
   q=[b['q'][x[0]] for x in win]
   expert.append({'lo':max(x['lo'] for x in q),'hi':max(x['hi'] for x in q),'bytes':sum(x[2] for x in win)})
  intervals.extend((q['hi']-q['lo'])/1e6 for q in b['q'].values())
 cold=(d['cold_end']-d['cold_begin'])/1e6
 if expert:
  firstlo=min(x['lo'] for x in expert);firsthi=min(x['hi'] for x in expert)
  lastlo=max(x['lo'] for x in expert);lasthi=max(x['hi'] for x in expert)
  optimistic=max(0,min(cold,(d['cold_begin']-firstlo)/1e6))
  observed=max(0,min(cold,(d['cold_begin']-firsthi)/1e6))
 else:firstlo=firsthi=lastlo=lasthi=0;optimistic=observed=0
 details.append({**d,'io_batches':len(bs),'io_requests':sum(b['nq'] for b in bs),'expert_destinations':len(expert),'cold_ms':cold,'first_ready_lower_ns':firstlo,'first_ready_observed_ns':firsthi,'last_ready_lower_ns':lastlo,'last_ready_observed_ns':lasthi,'optimistic_bound_ms':optimistic,'observed_bound_ms':observed,'completion_spread_ms':max(0,(lasthi-firsthi)/1e6),'interval_width_max_ms':max(intervals,default=0),'copy_ms':sum((b['copy_end']-b['copy_begin'])/1e6 for b in bs)})
outside=[]
for bid in sorted(set(batches)-assigned):
 b=batches[bid];assert len(b['q'])==b['nq']
 start=min(q['submit'] for q in b['q'].values());finish=b['copy_end']
 assert not any(d['req']==b['req'] and start<d['cold_end'] and finish>d['start'] for d in dispatch),'UNASSIGNED_IO_OVERLAPS_DISPATCH'
 outside.append({'batch':bid,'req':b['req'],'requests':b['nq'],'start':start,'end':finish,'full_duration_ms':(finish-start)/1e6,'caller':'NOT_IDENTIFIED_OUTSIDE_CPU_DISPATCH'})
assert assigned|{x['batch'] for x in outside}==set(batches)
per=[]
for req,(r,p) in enumerate(zip(rows,phase),1):
 assert r['windows']==p['windows'] and p['windows']>0
 ds=[d for d in details if d['req']==req];windows=p['windows']
 assert len(ds)<=48*windows,('EXTRA_DISPATCHES',req,len(ds),windows)
 # A no-miss dispatch contributes zero; dispatch coverage is reported, not silently imputed.
 per.append({'point':r['pid'],'windows':windows,'dispatches':len(ds),'possible_layer_windows':48*windows,'io_batches':sum(d['io_batches'] for d in ds),'io_requests':sum(d['io_requests'] for d in ds),'miss_dispatches':sum(d['io_batches']>0 for d in ds),'multi_expert_dispatches':sum(d['expert_destinations']>1 for d in ds),'optimistic_bound_ms_window':sum(d['optimistic_bound_ms'] for d in ds)/windows,'observed_bound_ms_window':sum(d['observed_bound_ms'] for d in ds)/windows,'cold_ms_window':sum(d['cold_ms'] for d in ds)/windows,'copy_ms_window':sum(d['copy_ms'] for d in ds)/windows,'join_ms_window':p['join_ms']/windows,'inline_ms_window':p['inline_ms']/windows,'lru_ms_window':p['lru_ms']/windows,'pipeline_ms_window':p['pipeline_ms']/windows,'decode_ms':r['m_decode_ms'],'tokens':r['m_out_tokens']})
windows=sum(x['windows'] for x in per);decode=sum(x['decode_ms'] for x in per);tokens=sum(x['tokens'] for x in per)
mean_window=decode/windows
outside_credit=sum(x['full_duration_ms'] for x in outside)/windows
upper=sum(d['optimistic_bound_ms'] for d in details)/windows+outside_credit
obs=sum(d['observed_bound_ms'] for d in details)/windows
coverage=len(dispatch)==48*windows
out={'status':('NO_GO_UNCHANGED_WORK_STREAMING_BOUND' if upper<mean_window/11 else 'HEADROOM_ONLY') if coverage else 'INCONCLUSIVE_DISPATCH_COVERAGE','requests':10,'windows':windows,'dispatches':len(dispatch),'expected_layer_windows':48*windows,'full_dispatch_coverage':coverage,'io_batches':len(batches),'io_requests':sum(b['nq'] for b in batches.values()),'outside_dispatch_batches':outside,'outside_dispatch_full_time_credit_ms_window':outside_credit,'diagnostic_pooled_tok_s':tokens/decode*1000,'diagnostic_mean_ms_window':mean_window,'saving_needed_for_10pct_ms_window':mean_window/11,'optimistic_bound_ms_window':upper,'observed_bound_ms_window':obs,'conditional_optimistic_speedup_percent':100*(mean_window/(mean_window-upper)-1),'completion_interval_ms_max':max(d['interval_width_max_ms'] for d in details),'per_point':per,'quality':'CHECKED_NATIVE_PIPE_SMOKE_ONLY_NOT_SEMANTIC_PARITY','limitations':['instrumented wait-any changes observation/wakeup timing; not a performance A/B','completion times are observed intervals, not device timestamps','bound assumes unchanged cold-batch compute duration, unbounded readiness publication, no CPU contention or copy cost for early expert','two outside-dispatch reads retained with full elapsed-time credit; exact callers not identified','no future route prediction, reduction of reads/work, kernel/layout improvement or cross-layer scheduling modeled','no deployment; full implementation not authorized by headroom alone']}
(R/'analysis.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
(R/'dispatch-analysis.json').write_text(json.dumps(details),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ('per_point','limitations')},indent=2))
