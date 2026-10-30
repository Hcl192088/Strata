import json
from pathlib import Path
R=Path(__file__).resolve().parent
ds=json.loads((R.parent/'io-arrival-20261029/dispatch-analysis.json').read_text())
a=json.loads((R/'analysis.json').read_text())
meta={}
for line in (R.parent/'cpu-r4-20261029/raw/native_experts.txt').read_text().splitlines():
 if line and not line.startswith('#'):
  q=line.split();meta[int(q[0])]=int(q[1])
def model(factors):
 saved=0;oldsum=0
 for d in ds:
  s=factors[meta[d['layer']]]
  ready=(d['ready_end']-d['start'])/1e6
  io=(d['bulk_ready']-d['start'])/1e6
  gap=(d['cold_begin']-max(d['ready_end'],d['bulk_ready']))/1e6
  cold=(d['cold_end']-d['cold_begin'])/1e6
  old=(d['cold_end']-d['start'])/1e6
  new=max(ready/s,io)+gap+cold/s
  saved+=old-new;oldsum+=old
 save=saved/1114;w=37.06552962298025
 return dict(saved_ms_window=save,conditional_speedup_percent=100*(w/(w-save)-1),dispatch_ms_window=oldsum/1114)
types=sorted(set(meta.values()))
best={t:max(x['ratio'] for x in a['all_rows'] if x['type']==t and x['full']==1) for t in types}
worst={t:min(x['ratio'] for x in a['selected'] if x['type']==t) for t in types}
out=dict(status='CONDITIONAL_PLANNING_ONLY',dispatches=len(ds),windows=1114,
 limits=['Posthoc maximum per type across core/nt/variant is unrealizable optimism, not a selected kernel or live-weight estimate.',
         'Scales all observed ready-prefix/cold duration by a full-row single-core microbenchmark ratio; scheduler, LRU/copy/noncompute portions may not scale.',
         'Observed I/O offsets fixed, GPU/other window costs fixed, new packing costs excluded.',
         'Not a global upper bound or measured engine speed; no quality gate.'],
 uniform13=model({t:1.3 for t in types}),best_per_type=best,optimistic_posthoc=model(best),worst_selected_per_type=worst,pessimistic_proxy=model(worst))
(R/'model.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
