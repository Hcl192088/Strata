"""Request-boundary estimates from existing logs only. No runtime/SSH or fabricated I/O timings."""
import hashlib
import json
import math
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'out'
rows = json.loads((OUT / 'rows-AB.json').read_text())
assert len(rows) == 300 and len({(r['arm'], r['round'], r['pid']) for r in rows}) == 300
pat = re.compile(r'MISS_OVERLAP progress: split_calls=(\d+) inline_reads=(\d+) helper_read_ms=([\d.]+) compute_while_read_ms=([\d.]+) join_wait_ms=([\d.]+) check_rows=(\d+) check_mismatch_rows=(\d+)')
keys = ('split_calls', 'inline_reads', 'helper_read_ms', 'ready_compute_ms', 'join_wait_ms', 'check_rows', 'check_bad')
def samples(t):
    return [dict(zip(keys, [int(x) if i in (0, 1, 5, 6) else float(x) for i, x in enumerate(m)])) for m in pat.findall(t)]
result = dict(method='carry-last-sample request estimates; monotone-counter boundary bands exclude first/last requests where needed',
    unit='ms unless specified', records=[], blocks=[], source_hashes=[], coverage={}, limitations=[
        'Counters print once per 64 split calls, not at decode begin/end. Per-request deltas are estimates, not exact phase partitions.',
        'Counters are process-global verifier-dispatch counters. Source also has prompt-side verification before DecSnap ds0; no exact decode-only MISS counter snapshot exists.',
        'helper_read measures prefetch_split_run duration including read/copy/bookkeeping, not pure SSD device time; it overlaps resident computation.',
        'ready_compute_ms is all first-pass resident computation, not measured intersection with I/O.',
        'join_wait includes helper completion/scheduling/spin delay. Non-join CPU residual includes down, activation quantization, LRU/copies and scheduling, not only IQ decode.',
        'inline synchronous reads occur in jobs according to source; count is logged, duration is not separately logged.',
        'm_file_mb/m_file_blobs are the captured /metrics request fields; log cumulative file MB includes prompt work and is not a decode-only substitute.'
    ])
byblock = defaultdict(list)
for r in rows:
    assert not r.get('error')
    byblock[(r['block'], r['arm'], r['round'])].append(r)
for (b, arm, rd), rs in sorted(byblock.items()):
    rs.sort(key=lambda r: r['pid'])
    assert len(rs) == 10
    d = OUT / ('block-%02d-%s-r%d' % (b, arm, rd))
    meta = json.loads((d / 'meta.json').read_text())
    cfg = json.loads((d / 'config.json').read_text())
    assert meta['status'] == 'OK' and meta['binary_sha256'] == '385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5'
    assert cfg['env'].get('STRATA_IQ3S_MT1') == ('1' if arm == 'MT1' else None)
    assert 'STRATA_IQ_MT_MIN' not in cfg['env']
    logpath = d / 'engine.log'
    full = samples(logpath.read_text(encoding='utf-8', errors='replace'))
    assert full and full[0]['split_calls'] == 1
    assert all(y['split_calls']-x['split_calls'] == 64 for x,y in zip(full,full[1:]))
    assert all(not x['check_bad'] for x in full)
    for k in keys:
        assert all(y[k] >= x[k] for x,y in zip(full,full[1:])), (d,k)
    point_samples = []
    for r in rs:
        tpath = d / ('tail-' + r['pid'] + '.log')
        ss = samples(tpath.read_text(encoding='utf-8', errors='replace'))
        assert ss
        point_samples.append(ss)
    assert [s for ss in point_samples for s in ss] == full, 'tail coverage differs from full engine log'
    prev = {k:0 for k in keys}
    for i,(r,ss) in enumerate(zip(rs,point_samples)):
        first,last = ss[0],ss[-1]
        delta = {k:last[k]-prev[k] for k in keys}
        w = r['windows']; cpu = r['cpu_ms']*w
        assert cpu > 0 and w > 0
        assert delta['join_wait_ms'] <= cpu, 'scope mismatch: sampled join exceeds CPU'
        item = dict(block=b, arm=arm, round=rd, pid=r['pid'], windows=w, tokens=r['tokens'],
            cpu_ms_window=r['cpu_ms'], cpu_total_ms=cpu, cpu_experts_layer=r['cpu_experts_per_layer_window'],
            cpu_us_expert_wall=r['cpu_us_per_expert'], request_timing_decode_ms=r['decode_ms'],
            file_MB_metrics=r['m_file_mb'], file_blobs_metrics=r['m_file_blobs'],
            file_MB_all_request_log=r['ssd_mb'], file_blobs_all_request_log=r['ssd_blobs'],
            sampled_delta=delta, progress_samples=len(ss),
            join_est_ms_window=delta['join_wait_ms']/w,
            nonjoin_CPU_est_ms_window=(cpu-delta['join_wait_ms'])/w,
            helper_est_ms_window=delta['helper_read_ms']/w,
            ready_compute_est_ms_window=delta['ready_compute_ms']/w,
            # These bands constrain request-level global counter deltas, NOT certified decode-only latency.
            join_request_counter_low=max(0,last['join_wait_ms']-first['join_wait_ms']),
            join_request_counter_high=(point_samples[i+1][0]['join_wait_ms']-prev['join_wait_ms']) if i<9 else None)
        result['records'].append(item)
        prev=last
    # Aggregate interior p02..p09 with rigorous monotone request-boundary sampling bands.
    inner_windows=sum(r['windows'] for r in rs[1:9])
    low=point_samples[8][-1]['join_wait_ms']-point_samples[1][0]['join_wait_ms']
    high=point_samples[9][0]['join_wait_ms']-point_samples[0][-1]['join_wait_ms']
    result['blocks'].append(dict(block=b,arm=arm,round=rd,windows=sum(r['windows'] for r in rs),last=full[-1],
        interior_windows=inner_windows, interior_join_low=low,interior_join_high=high,
        # For the whole block, last sample misses 0..63 final split calls; duration is not bounded.
        unsampled_final_split_call_count_max=63))
    result['source_hashes'].append(dict(path=str(logpath),sha256=hashlib.sha256(logpath.read_bytes()).hexdigest().upper()))

def aggregate(a):
    w=sum(r['windows'] for r in a)
    cpu=sum(r['cpu_total_ms'] for r in a)
    j=sum(r['sampled_delta']['join_wait_ms'] for r in a)
    h=sum(r['sampled_delta']['helper_read_ms'] for r in a)
    rc=sum(r['sampled_delta']['ready_compute_ms'] for r in a)
    nj=cpu-j
    return dict(requests=len(a),windows=w,CPU_ms_window=cpu/w,sampled_join_ms_window=j/w,
        sampled_join_fraction_CPU=j/cpu,nonjoin_CPU_ms_window=nj/w,helper_ms_window=h/w,
        resident_firstpass_ms_window=rc/w,file_MB_metrics=sum(r['file_MB_metrics'] for r in a),
        file_blobs_metrics=sum(r['file_blobs_metrics'] for r in a),
        file_MB_all_request_log=sum(r['file_MB_all_request_log'] for r in a),
        inline_reads_count=sum(r['sampled_delta']['inline_reads'] for r in a),
        needed_nonjoin_reduction_to_50=(1000/(1000*sum(r['tokens'] for r in a)/sum(r['request_timing_decode_ms'] for r in a))-20)*sum(r['tokens'] for r in a)/nj)
result['summary']={arm:aggregate([r for r in result['records'] if r['arm']==arm]) for arm in ('S2K','MT1','S2KB')}
mt=[r for r in result['records'] if r['arm']=='MT1']
result['MT1_by_point']={p:aggregate([r for r in mt if r['pid']==p]) for p in sorted({r['pid'] for r in mt})}
bb=[b for b in result['blocks'] if b['arm']=='MT1']
iw=sum(b['interior_windows'] for b in bb)
result['MT1_interior_request_counter_band']=dict(requests=80,windows=iw,
    join_low_ms_window=sum(b['interior_join_low'] for b in bb)/iw,
    join_high_ms_window=sum(b['interior_join_high'] for b in bb)/iw,
    note='Bounds are for p02..p09 full-request global-counter increments; decode-only purity not established.')
def corr(x,y):
    mx,my=st.mean(x),st.mean(y)
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))
result['MT1_descriptive_correlations_not_causal']=dict(
    CPU_window_vs_decode_MB_window=corr([r['cpu_ms_window'] for r in mt],[r['file_MB_metrics']/r['windows'] for r in mt]),
    sampled_join_window_vs_decode_MB_window=corr([r['join_est_ms_window'] for r in mt],[r['file_MB_metrics']/r['windows'] for r in mt]),
    CPU_window_vs_sampled_join_window=corr([r['cpu_ms_window'] for r in mt],[r['join_est_ms_window'] for r in mt]))
result['coverage']=dict(replay_rows=300,blocks=30,engine_logs=30,request_tails=300,MT1_requests=100,
    all_tail_progress_matches_full_logs=True,probe_excluded=True,remote_operations=0)
(ROOT / 'CPU_DECOMPOSITION_OFFLINE_20261029.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ('summary','MT1_interior_request_counter_band','MT1_descriptive_correlations_not_causal','coverage')},indent=2))
print('MT1 by point: pid CPU_ms/w join_est_ms/w nonjoin_ms/w helper_ms/w decode_MB/w')
for p,r in result['MT1_by_point'].items():
    a=[x for x in mt if x['pid']==p]
    print(p,*[round(r[k],3) for k in ('CPU_ms_window','sampled_join_ms_window','nonjoin_CPU_ms_window','helper_ms_window')],round(r['file_MB_metrics']/sum(x['windows'] for x in a),3))
