"""NEXT4 analysis. usage: python analyze_next4.py <out_dir>   (raw rows recomputed from rows-AB.json / engine logs)
Pre-registered verdict (ledger NEXT4): per-point mean >= +3% AND per-point 95% CI excludes 0 -> positive; otherwise null.
Block-pooled tok/s = sum(tokens)/sum(decode_ms) per (arm, round); paired by round (df=n-1) and per point (mean over rounds, df=9)."""
import json, math, re, statistics as st, sys
from collections import defaultdict
from pathlib import Path

OUT = Path(sys.argv[1])
T = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262}
rows = json.load(open(OUT / 'rows-AB.json'))
blocks = json.load(open(OUT / 'blocks.json'))
qs = json.load(open(OUT / 'queue_state.json'))
CTRL = 'S2K'


def ci(v):
    n = len(v)
    m = st.mean(v)
    s = st.stdev(v) if n > 1 else float('nan')
    h = T[n - 1] * s / math.sqrt(n) if n > 1 else float('nan')
    return m, s, m - h, m + h, n - 1


ok_blocks = {(b['arm'], b['round']) for b in blocks if b['status'] == 'OK' and b['round'] > 0}
B = defaultdict(lambda: [0, 0.0, {}])
for r in rows:
    if r.get('error') or not r.get('m_decode_ms') or (r['arm'], r['round']) not in ok_blocks:
        continue
    k = (r['arm'], r['round'])
    B[k][0] += r['m_out_tokens'] or 0
    B[k][1] += r['m_decode_ms']
    B[k][2][r['pid']] = r['m_decode_tok_s']
arms = sorted({a for a, _ in B}, key=lambda a: ['S2K', 'PIN8', 'PIN16', 'AA', 'P4_8', 'P4_16'].index(a))
rate = lambda k: B[k][0] / B[k][1] * 1000
print('blocks OK per arm:', {a: sorted(r for (x, r) in B if x == a) for a in arms})
res = {}
for a in arms:
    v = [rate((a, r)) for r in range(1, 6) if (a, r) in B]
    print('%-6s pooled tok/s per round %s mean %.2f' % (a, [round(q, 1) for q in v], st.mean(v)))
print()
for a in arms:
    if a == CTRL:
        continue
    d = [(rate((a, r)) / rate((CTRL, r)) - 1) * 100 for r in range(1, 6) if (a, r) in B and (CTRL, r) in B]
    if len(d) < 2:
        print(a, 'too few paired rounds', len(d))
        continue
    m, s, lo, hi, df = ci(d)
    pts = sorted({p for k in B for p in B[k][2]})
    dp = []
    for p in pts:
        ax = [B[(a, r)][2][p] for r in range(1, 6) if (a, r) in B and p in B[(a, r)][2]]
        ay = [B[(CTRL, r)][2][p] for r in range(1, 6) if (CTRL, r) in B and p in B[(CTRL, r)][2]]
        if ax and ay:
            dp.append((st.mean(ax) / st.mean(ay) - 1) * 100)
    m2, s2, lo2, hi2, df2 = ci(dp)
    pos = m2 >= 3 and lo2 > 0
    res[a] = dict(round=(m, lo, hi, df), point=(m2, lo2, hi2, df2), positive=pos, rounds=len(d))
    print('%-6s vs S2K  by-round %+.2f%% CI [%+.2f,%+.2f] df=%d  (diffs %s)' % (a, m, lo, hi, df, [round(q, 1) for q in d]))
    print('       per-point %+.2f%% CI [%+.2f,%+.2f] df=%d  -> %s' % (m2, lo2, hi2, df2, 'POSITIVE (pre-registered)' if pos else 'NULL/negative (pre-registered)'))
print()

# mechanism: window-weighted from per-request rows
print('== mechanism (window-weighted over measured requests of OK blocks)')
agg = defaultdict(lambda: defaultdict(float))
for r in rows:
    if (r['arm'], r['round']) not in ok_blocks or not r.get('windows'):
        continue
    w = r['windows']
    a = agg[r['arm']]
    a['w'] += w
    for k_src, k in (('ms_window', 'win'), ('gpu_wait_ms', 'gpu'), ('jobs_ms', 'jobs'), ('cpu_ms', 'cpu'), ('cpu_experts_per_layer_window', 'cpu_exp'),
                     ('pcie_per_layer_window', 'pcie'), ('vram_hits_per_layer_window', 'vram'), ('cpu_us_per_expert', 'cpu_us')):
        if r.get(k_src) is not None:
            a[k] += w * r[k_src]
mech = {}
for arm in arms:
    a = agg[arm]
    if not a['w']:
        continue
    mech[arm] = {k: a[k] / a['w'] for k in ('win', 'gpu', 'jobs', 'cpu', 'cpu_exp', 'pcie', 'vram', 'cpu_us')}
    mech[arm]['jobs+cpu'] = mech[arm]['jobs'] + mech[arm]['cpu']
    print('%-6s windows %6d  ms/win %.2f  GPU-wait %.2f  jobs %.2f  CPU %.2f  (jobs+CPU %.2f)  CPU exp/layer %.2f  PCIe/layer %.3f  VRAM hits %.2f  cpu_us/exp %.1f' % (
        arm, a['w'], mech[arm]['win'], mech[arm]['gpu'], mech[arm]['jobs'], mech[arm]['cpu'], mech[arm]['jobs+cpu'], mech[arm]['cpu_exp'], mech[arm]['pcie'], mech[arm]['vram'], mech[arm]['cpu_us']))

# per-block startup time + P4 chunk counters
print('\n== startup (load_s) per arm, and P4 chunk counters (last progress line of each block)')
ls = defaultdict(list)
for b in blocks:
    if b['status'] == 'OK' and b['round'] > 0 and b.get('load_s') is not None:
        ls[b['arm']].append(b['load_s'])
for a in arms:
    print(a, 'load_s', ls[a], 'mean %.1f' % st.mean(ls[a]) if ls[a] else '')
cw = {}
for b in blocks:
    if b['arm'].startswith('P4_') and b['status'] == 'OK':
        d = OUT / ('block-%02d-%s-r%d' % (b['block'], b['arm'], b['round']))
        text = (d / 'engine.log').read_text(encoding='utf-8', errors='replace')
        prog = [l for l in text.splitlines() if l.startswith('MISS_OVERLAP progress')]
        if prog:
            g = lambda k: float(re.search(k + r'=([\d.]+)', prog[-1]).group(1))
            wins = sum(r['windows'] or 0 for r in rows if r['block'] == b['block'] and r.get('windows'))
            cw.setdefault(b['arm'], []).append(dict(split=g('split_calls'), chunks=g('chunks_published'), chunk_wait_ms=g('chunk_wait_ms'), windows=wins,
                                                    join_wait_ms=g('join_wait_ms') if 'join_wait_ms=' in prog[-1] else None,
                                                    chunk_wait_ms_per_window=g('chunk_wait_ms') / wins if wins else None))
for a, v in cw.items():
    print(a, 'chunk_wait_ms/window mean %.3f' % st.mean(x['chunk_wait_ms_per_window'] for x in v if x['chunk_wait_ms_per_window'] is not None),
          'chunks_published per block', [int(x['chunks']) for x in v], 'split', [int(x['split']) for x in v])

# CPU_BW_DIAG from existing timing
print('\n== CPU_BW_DIAG (analysis only): effective GB/s of expert bytes streamed by the CPU kernel')
rr = [r for r in rows if (r['arm'], r['round']) in ok_blocks and r.get('ssd_blobs') and r.get('ssd_mb')]
bl = [r['ssd_mb'] / r['ssd_blobs'] for r in rr if r['ssd_blobs'] > 50]
print('mean MB per SSD-read expert blob (per request ssd_mb/ssd_blobs): %.3f (median %.3f)' % (st.mean(bl), st.median(bl)))
share = []
for p in OUT.glob('block-*/engine.log'):
    for m in re.finditer(r'the CPU pool takes (\d+) us per missed expert \(([\d.]+) GB/s of expert bytes\)', p.read_text(encoding='utf-8', errors='replace')):
        share.append((int(m.group(1)), float(m.group(2))))
if share:
    print('engine-reported "CPU pool takes X us per missed expert (Y GB/s)" samples: n=%d, us mean %.0f, GB/s mean %.1f, min %.1f, max %.1f' % (
        len(share), st.mean(s[0] for s in share), st.mean(s[1] for s in share), min(s[1] for s in share), max(s[1] for s in share)))
for a in arms:
    if a in mech:
        print('%-6s cpu_us/expert %.1f -> %.1f GB/s (MB/blob %.3f)' % (a, mech[a]['cpu_us'], st.mean(bl) * 1e6 / (mech[a]['cpu_us'] * 1e-6) / 1e9, st.mean(bl)))

json.dump(dict(res=res, mech=mech), open(OUT / 'analysis.json', 'w'), indent=1, default=str)
