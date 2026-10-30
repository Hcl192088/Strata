"""IQ3S_MT1_AB analysis, recomputed from raw rows-AB.json (out/). python analyze.py [out_dir]"""
import json, math, statistics as st, sys
from collections import defaultdict
from pathlib import Path

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / 'out')
# two-sided 95% t quantiles
TQ = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}
rows = json.load(open(OUT / 'rows-AB.json'))
rows = [r for r in rows if r['arm'] in ('S2K', 'MT1', 'S2KB')]


def ci(v):
    n = len(v)
    m = st.mean(v)
    if n < 2:
        return m, float('nan'), float('nan'), float('nan'), n - 1
    s = st.stdev(v)
    h = TQ[n - 1] * s / math.sqrt(n)
    return m, s, m - h, m + h, n - 1


blk = defaultdict(lambda: dict(tok=0, ms=0.0, pts={}, n=0, win=0.0, cpu=0.0, gpu=0.0, host=0.0, msw=0.0, outs={}))
for r in rows:
    if r.get('error') or not r.get('m_decode_ms'):
        continue
    b = blk[(r['arm'], r['round'])]
    b['tok'] += r['m_out_tokens'] or 0
    b['ms'] += r['m_decode_ms']
    b['n'] += 1
    b['pts'][r['pid']] = (r['m_out_tokens'], r['m_decode_ms'], r['m_decode_tok_s'])
    w = r.get('windows') or 0
    if w and r.get('cpu_ms') is not None:
        b['win'] += w
        b['cpu'] += r['cpu_ms'] * w
        b['gpu'] += (r.get('gpu_wait_ms') or 0) * w
        b['host'] += (r.get('host_ms') or 0) * w
        b['msw'] += (r.get('ms_window') or 0) * w
    b['outs'][r['pid']] = r.get('completion_tokens')

complete = sorted(rd for rd in {k[1] for k in blk} if all((a, rd) in blk and blk[(a, rd)]['n'] == 10 for a in ('S2K', 'MT1', 'S2KB')))
print('complete rounds:', complete)


def toks(a, rd):
    b = blk[(a, rd)]
    return b['tok'] / b['ms'] * 1000


def seg(a, rd, key):
    b = blk[(a, rd)]
    return b[key] / b['win']


res = {}
print('\n== per-arm per-round block tok/s')
for a in ('S2K', 'MT1', 'S2KB'):
    v = [toks(a, r) for r in complete]
    print(a, [round(x, 2) for x in v], 'mean %.2f' % st.mean(v))
    res['tok_' + a] = v


def paired(x, y, label):
    d = [(toks(x, r) / toks(y, r) - 1) * 100 for r in complete]
    m, s, lo, hi, df = ci(d)
    print('%s: mean %+.2f%% sd %.2f  95%%CI [%+.2f, %+.2f] df=%d  diffs %s' % (label, m, s, lo, hi, df, [round(q, 1) for q in d]))
    pts = sorted({p for k in blk for p in blk[k]['pts']})
    dp = []
    for p in pts:
        ax = [blk[(x, r)]['pts'][p][2] for r in complete if p in blk[(x, r)]['pts']]
        ay = [blk[(y, r)]['pts'][p][2] for r in complete if p in blk[(y, r)]['pts']]
        dp.append((st.mean(ax) / st.mean(ay) - 1) * 100)
    m2, s2, lo2, hi2, df2 = ci(dp)
    print('   per-point: mean %+.2f%% sd %.2f CI [%+.2f, %+.2f] df=%d  %s' % (m2, s2, lo2, hi2, df2, [round(q, 1) for q in dp]))
    return dict(mean=m, lo=lo, hi=hi, df=df, point_mean=m2, point_lo=lo2, point_hi=hi2, diffs=d, pts=dp)


print('\n== paired tok/s (by round)')
res['MT1_vs_S2K'] = paired('MT1', 'S2K', 'MT1 vs S2K')
res['AA'] = paired('S2KB', 'S2K', 'S2KB vs S2K (A/A)')
res['MT1_vs_S2KB'] = paired('MT1', 'S2KB', 'MT1 vs S2KB')

print('\n== engine segments, window-weighted per block (ms/window)')
for key, name in (('cpu', 'CPU'), ('gpu', 'GPU-reach wait'), ('host', 'per-layer host'), ('msw', 'ms/window')):
    for a in ('S2K', 'MT1', 'S2KB'):
        v = [seg(a, r, key) for r in complete]
        print('%-14s %-5s mean %.3f  %s' % (name, a, st.mean(v), [round(x, 2) for x in v]))
    for x, y, lab in (('MT1', 'S2K', 'MT1-S2K'), ('S2KB', 'S2K', 'S2KB-S2K (A/A)')):
        d = [seg(x, r, key) - seg(y, r, key) for r in complete]
        m, s, lo, hi, df = ci(d)
        print('   %-16s %s paired diff mean %+.3f ms  95%%CI [%+.3f, %+.3f] df=%d' % (lab, name, m, lo, hi, df))
        res['seg_%s_%s' % (key, lab)] = (m, lo, hi)

print('\n== output tokens per point (mean over rounds) and block totals')
pts = sorted({p for k in blk for p in blk[k]['pts']})
for a in ('S2K', 'MT1', 'S2KB'):
    per = [st.mean([blk[(a, r)]['pts'][p][0] for r in complete]) for p in pts]
    tot = [blk[(a, r)]['tok'] for r in complete]
    print(a, 'per-point mean tokens', [round(x, 1) for x in per], 'block total mean %.1f' % st.mean(tot), tot)
for x in ('MT1', 'S2KB'):
    dt = [blk[(x, r)]['tok'] - blk[('S2K', r)]['tok'] for r in complete]
    same = sum(1 for r in complete for p in pts if blk[(x, r)]['pts'][p][0] == blk[('S2K', r)]['pts'][p][0])
    print('%s - S2K block token diff by round %s; points with identical length %d/%d' % (x, dt, same, len(complete) * len(pts)))
# S2K vs S2KB deterministic?
json.dump(dict(complete=complete, **{k: v for k, v in res.items()}), open(OUT / 'analysis.json', 'w'), indent=1, default=str)
