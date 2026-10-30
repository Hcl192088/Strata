import json, statistics as st, math, re
from collections import defaultdict
# two-sided 95% t, df 1..9
T = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262}


def load(f):
    return json.load(open(f))


def blockstats(rows):
    b = defaultdict(lambda: [0, 0.0, {}])
    for r in rows:
        if r.get('error') or not r.get('m_decode_ms'):
            continue
        k = (r['arm'], r['round'])
        b[k][0] += r['m_out_tokens'] or 0
        b[k][1] += r['m_decode_ms']
        b[k][2][r['pid']] = r['m_decode_tok_s']
    return b


def ci(vals):
    n = len(vals)
    m = st.mean(vals)
    s = st.stdev(vals) if n > 1 else float('nan')
    h = T[n - 1] * s / math.sqrt(n)
    return m, s, m - h, m + h, n - 1


def report(rows, rounds, label, x='S2K', y='C0'):
    b = blockstats(rows)
    print('==', label)
    res = {}
    for a in (y, x):
        v = [b[(a, r)][0] / b[(a, r)][1] * 1000 for r in range(1, rounds + 1) if (a, r) in b]
        print(a, 'pooled tok/s per round', [round(q, 1) for q in v], 'mean', round(st.mean(v), 2))
    d = []
    for r in range(1, rounds + 1):
        if (x, r) in b and (y, r) in b:
            d.append((b[(x, r)][0] / b[(x, r)][1] / (b[(y, r)][0] / b[(y, r)][1]) - 1) * 100)
    m, s, lo, hi, df = ci(d)
    print('%s vs %s by-round: mean %+.2f%% sd %.2f 95%%CI [%+.2f,%+.2f] df=%d diffs %s' % (x, y, m, s, lo, hi, df, [round(q, 1) for q in d]))
    res['round'] = (m, lo, hi, df)
    pts = sorted({p for k in b for p in b[k][2]})
    dpt = []
    for p in pts:
        ax = [b[(x, r)][2][p] for r in range(1, rounds + 1) if (x, r) in b and p in b[(x, r)][2]]
        ay = [b[(y, r)][2][p] for r in range(1, rounds + 1) if (y, r) in b and p in b[(y, r)][2]]
        if ax and ay:
            dpt.append((st.mean(ax) / st.mean(ay) - 1) * 100)
    m2, s2, lo2, hi2, df2 = ci(dpt)
    print('   per-point: mean %+.2f%% sd %.2f CI [%+.2f,%+.2f] df=%d' % (m2, s2, lo2, hi2, df2), [round(q, 1) for q in dpt])
    res['point'] = (m2, lo2, hi2, df2)
    return res


g = report(load('out/rows-GREEDY.json'), 8, 'GREEDY 1b')
s = report(load('out/rows-SAMPLING.json'), 3, 'SAMPLING 1c')

# per-arm window timing (window-weighted) from engine.log lines; block->arm via blocks.json
blocks = {('block-%02d-%s-r%d' % (x['block'], x['arm'], x['round'])): x for x in load('out/blocks.json')}
agg = defaultdict(lambda: defaultdict(float))
rx = re.compile(r'(\d+) windows.*?([\d.]+) ms/window = verify ([\d.]+) \(GPU-reach wait ([\d.]+) \+ per-layer host ([\d.]+) \[plan [\d.]+ actq [\d.]+ jobs ([\d.]+) CPU ([\d.]+)\]')
mo = {}
for line in open('timing_lines.txt', encoding='utf-8'):
    name, rest = line.rstrip('\n').split('|', 1)
    if rest.startswith('MO|'):
        mo[name] = rest[3:]
        continue
    m = rx.search(rest)
    if not m or name not in blocks:
        continue
    bl = blocks[name]
    kind = 'MCHK' if bl['arm'] == 'MCHK' else ('GREEDY' if name in [k for k in blocks] and bl['block'] <= 17 else 'SAMPLING')
    w = int(m.group(1))
    key = (kind, bl['arm'])
    a = agg[key]
    a['w'] += w
    for i, nm in enumerate(('win', 'verify', 'gpu', 'host', 'jobs', 'cpu'), 2):
        a[nm] += w * float(m.group(i))
print('== ms/window (window-weighted)')
for key in sorted(agg):
    a = agg[key]
    if key[0] == 'MCHK':
        continue
    print(key, 'windows', int(a['w']), ' '.join('%s %.2f' % (nm, a[nm] / a['w']) for nm in ('win', 'verify', 'gpu', 'host', 'jobs', 'cpu')), 'jobs+cpu %.2f' % ((a['jobs'] + a['cpu']) / a['w']))

# neuro
print('== neuro (4 runs per block; run 1 = warm-up)')
nm = {}
for n in ('1-C0', '2-S2K', '3-S2K', '4-C0'):
    r = load('out/neuro-%s/result.json' % n)
    nm[n] = r
    print(n, r['status'], 'startup_ok', r['startup_ok'], 'tok/s', r['tok_s'], 'measured mean %.2f' % st.mean(r['tok_s'][1:]))
c0 = [x for n in ('1-C0', '4-C0') for x in nm[n]['tok_s'][1:]]
s2 = [x for n in ('2-S2K', '3-S2K') for x in nm[n]['tok_s'][1:]]
print('neuro warm mean: C0 %.2f (n=%d)  S2K %.2f (n=%d)  S2K vs C0 %+.2f%%' % (st.mean(c0), len(c0), st.mean(s2), len(s2), (st.mean(s2) / st.mean(c0) - 1) * 100))
# priority record
print('== priority (first_class 32=Normal, 32768=AboveNormal)')
cnt = defaultdict(int)
for b in load('out/blocks.json'):
    for e in b.get('engine_priority', []):
        cnt[(e['first_class'], e['set_by_queue'], e['set_ok'], tuple(sorted({r[1] for r in e['readings']})))] += 1
print(dict(cnt))
