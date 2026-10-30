"""Offline bounds from existing ON1/ON2 counters, not a new benchmark or event replay."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT.parent
BW = 45.7  # historical 9-worker pure-read measurement, GB/s, not a universal bandwidth limit
out = {'method': 'aggregate resource/traffic bounds, no fabricated per-expert timeline',
       'dram_reference_GBs': BW, 'source': [], 'runs': {}, 'limitations': [
           'ON1/ON2 are S2K/neuro before MT1, not current MT1/Hermes phase traces.',
           'Pure-read bandwidth and logical kernel bytes provide only a reference traffic floor.',
           'Equal-core busy-time bound freezes measured service times and ignores P/E differences; it is not a physical lower bound.',
           'Aggregate counters do not encode per-expert ready times, task order, or a reconstructible pipeline schedule.',
           'Gate/up and down share cores and bandwidth; min(phase times) is not an achievable overlap estimate.'
       ]}
totals = dict(windows=0, gu_ns=0, down_ns=0, quant_ns=0, call_ns=0, busy_ns=0,
              gu_bytes=0, down_bytes=0, idle_core_ns=0, calls=0, experts=0)
for name in ('ON1', 'ON2'):
    p = ROOT / 'raw' / ('run-' + name) / 'wskew.json'
    d = json.loads(p.read_text())
    text = (p.parent / 'stderr.log').read_text(encoding='utf-8', errors='replace')
    matches = re.findall(r'decode timing:\s*(\d+) windows', text)
    assert len(matches) == 1, (name, matches)
    windows = int(matches[0])
    assert d['n_workers'] == 9 and d['host_works'] == 1
    cols = d['thr_cols'].split(',')
    th = [dict(zip(cols, r)) for r in d['thr']]
    ph = [dict(zip(d['phase_cols'].split(','), r)) for r in d['phase']]
    calls = d['call']
    assert sum(c[2] for c in calls) == d['ncalls']
    mode = {}
    for m in (0, 1):
        pr = [r for r in ph if r['mode'] == m]
        tr = [r for r in th if r['mode'] == m]
        wall = sum(r['wall_ns'] for r in pr)
        busy = sum(r['busy_ns'] for r in tr)
        nbytes = sum(r['bytes'] for r in tr)
        idle = wall * 10 - busy
        assert idle >= 0
        assert sum(r['phases'] for r in pr) == d['ncalls']
        mode[m] = dict(wall_ns=wall, busy_ns=busy, bytes=nbytes, idle_core_ns=idle,
                       wall_ms_window=wall / windows / 1e6,
                       aggregate_GBs=nbytes / wall,
                       core_utilization=busy / (10 * wall),
                       idle_equiv_ms_window=idle / 10 / windows / 1e6)
    quant = sum(c[4] for c in calls)
    call = sum(c[3] for c in calls)
    assert call >= mode[0]['wall_ns'] + mode[1]['wall_ns'] + quant
    row = dict(windows=windows, calls=d['ncalls'], experts=sum(c[5] for c in calls),
               gu=mode[0], down=mode[1], quant_ms_window=quant / windows / 1e6,
               pool_ms_window=call / windows / 1e6)
    out['runs'][name] = row
    out['source'].append(dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest().upper()))
    for k, val in dict(windows=windows, gu_ns=mode[0]['wall_ns'], down_ns=mode[1]['wall_ns'],
        quant_ns=quant, call_ns=call, busy_ns=mode[0]['busy_ns'] + mode[1]['busy_ns'],
        gu_bytes=mode[0]['bytes'], down_bytes=mode[1]['bytes'],
        idle_core_ns=mode[0]['idle_core_ns'] + mode[1]['idle_core_ns'],
        calls=d['ncalls'], experts=row['experts']).items():
        totals[k] += val
w = totals['windows']
s = {k: totals[k] / w / 1e6 for k in ('gu_ns', 'down_ns', 'quant_ns', 'call_ns')}
out['historical_combined'] = dict(windows=w, calls=totals['calls'], experts_per_call=totals['experts'] / totals['calls'],
    gu_ms_window=s['gu_ns'], down_ms_window=s['down_ns'], quant_ms_window=s['quant_ns'], pool_ms_window=s['call_ns'],
    logical_MB_window=(totals['gu_bytes'] + totals['down_bytes']) / w / 1e6,
    traffic_reference_floor_ms_window=(totals['gu_bytes'] + totals['down_bytes']) / w / (BW * 1e6),
    equal_core_idle_equiv_ms_window=totals['idle_core_ns'] / 10 / w / 1e6,
    frozen_service_equal_core_work_ms_window=totals['busy_ns'] / 10 / w / 1e6,
    gu_aggregate_GBs=totals['gu_bytes'] / totals['gu_ns'],
    down_aggregate_GBs=totals['down_bytes'] / totals['down_ns'])

p = STATE / 'iq3s-mt1-ab-20261028/out/rows-AB.json'
allrows = json.loads(p.read_text())
rows = [r for r in allrows if r['arm'] == 'MT1']
assert len(allrows) == 300 and len(rows) == 100 and all(not r.get('error') for r in rows)
nw = sum(r['windows'] for r in rows)
timing = {k: sum(r[k] * r['windows'] for r in rows) / nw for k in
          ('ms_window', 'cpu_ms', 'gpu_wait_ms', 'jobs_ms', 'draft_ms', 'tokens_per_window')}
rate = 1000 * sum(r['tokens'] for r in rows) / sum(r['decode_ms'] for r in rows)
gap_ms_token = 1000 / rate - 20
out['current_MT1_Hermes'] = dict(rows=len(rows), pooled_tok_s=rate, ms_token=1000/rate,
    target_tok_s=50, gap_ms_token=gap_ms_token, timing=timing,
    CPU_fraction=timing['cpu_ms']/timing['ms_window'],
    CPU_zero_Amdahl_tok_s=rate / (1-timing['cpu_ms']/timing['ms_window']),
    needed_window_reduction_ms=timing['ms_window'] * (1-rate/50),
    needed_CPU_reduction_fraction=(1-rate/50) / (timing['cpu_ms']/timing['ms_window']))
out['scenarios_not_predictions'] = [dict(window_saved_ms=save,
    tok_s=rate * timing['ms_window'] / (timing['ms_window']-save),
    gain_pct=100 * save / (timing['ms_window']-save)) for save in (0.5, 1, 1.5, 2, 2.5, 3)]
out['decision'] = 'NO_GO for direct long A/B or claiming +3..6%; only a minimal future expert-readiness mechanism probe can resolve pipeline value.'
target = ROOT / 'offline_pipeline_bound.json'
target.write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({k: out[k] for k in ('historical_combined', 'current_MT1_Hermes', 'scenarios_not_predictions', 'decision')}, indent=2))
