"""Recompute POOL_WORKER_SKEW statistics from the raw wskew.json dumps. usage: python analyze_wskew.py <dir with run-*/wskew.json> [out.json]"""
import json, sys
from pathlib import Path

root = Path(sys.argv[1])
P_LPS = {2, 4, 6, 8, 10}
E_LPS = {12, 13, 14, 15}
KINDS = {0: 'plain', 1: 'overlap-hit', 2: 'overlap-miss', 3: 'check'}
MODES = {0: 'gate/up', 1: 'down'}


def load(path):
    d = json.loads(Path(path).read_text())
    return d


def merge(dumps):
    """sum the counters of several dumps (same pool layout)"""
    first = dumps[0]
    thr, phase, call = {}, {}, {}
    for d in dumps:
        assert d['lps'] == first['lps']
        for r in d['thr']:
            k = tuple(r[:4]); thr[k] = [a + b for a, b in zip(thr.get(k, [0] * (len(r) - 4)), r[4:])]
        for r in d['phase']:
            k = tuple(r[:3]); v = phase.get(k, [0] * (len(r) - 3)); n = [a + b for a, b in zip(v, r[3:])]
            n[-2], n[-1] = r[-2], r[-1]
            phase[k] = n
        for r in d['call']:
            k = tuple(r[:2]); call[k] = [a + b for a, b in zip(call.get(k, [0] * (len(r) - 2)), r[2:])]
    return dict(n=first['n_workers'], lps=first['lps'], hw=first['host_works'], thr=thr, phase=phase, call=call,
                micro=[d.get('micro') for d in dumps])


def lp_type(lp):
    return 'P' if lp in P_LPS else ('E' if lp in E_LPS else ('host' if lp == 0 else '?'))


def analyze(m, label):
    n, lps = m['n'], m['lps']
    out = dict(label=label, n_workers=n, lps=lps, per_T={})
    Ts = sorted({k[0] for k in m['thr']})
    for T in Ts + ['all']:
        sel = (lambda k: True) if T == 'all' else (lambda k, T=T: k[0] == T)
        calls = {k: v for k, v in m['call'].items() if sel(k)}
        # CPU layer-windows = plain calls + overlap pass-2 calls (every layer-window with CPU work has exactly one of them)
        lw = sum(v[0] for k, v in calls.items() if k[1] in (0, 2))
        ncalls = sum(v[0] for v in calls.values())
        call_ns = sum(v[1] for v in calls.values())
        quant_ns = sum(v[2] for v in calls.values())
        nexp = sum(v[3] for v in calls.values())
        sum_nt = sum(v[4] for v in calls.values())
        hist = [sum(v[6 + h] for v in calls.values()) for h in range(9)]
        ph = {k: v for k, v in m['phase'].items() if sel(k)}
        phases = sum(v[0] for v in ph.values())
        wall = sum(v[1] for v in ph.values()); drain = sum(v[2] for v in ph.values())
        wait = sum(v[3] for v in ph.values()); repark = sum(v[4] for v in ph.values())
        min_last = sum(v[5] for v in ph.values()); max_last = sum(v[6] for v in ph.values())
        ntasks = sum(v[7] for v in ph.values()); nparts = sum(v[8] for v in ph.values())
        e = dict(layer_windows_cpu=lw, pool_calls=ncalls, phases=phases, experts_per_call=nexp / ncalls if ncalls else None,
                 nt_mean=sum_nt / nexp if nexp else None, nt_hist=hist,
                 call_ms_per_cpu_layer_window=call_ns / 1e6 / lw if lw else None,
                 quant_share_of_call=quant_ns / call_ns if call_ns else None,
                 phase_wall_share_of_call=wall / call_ns if call_ns else None,
                 host_drain_share_of_call=drain / call_ns if call_ns else None,
                 host_wait_share_of_call=wait / call_ns if call_ns else None,
                 host_wait_share_of_phase_wall=wait / wall if wall else None,
                 repark_share_of_call=repark / call_ns if call_ns else None,
                 mean_phase_wall_us=wall / phases / 1e3 if phases else None,
                 mean_min_finish_us=min_last / phases / 1e3 if phases else None, mean_max_finish_us=max_last / phases / 1e3 if phases else None,
                 tasks_per_phase=ntasks / phases if phases else None, participants_per_phase=nparts / phases if phases else None)
        # per-thread
        threads = []
        for i in range(n + 1 if m['hw'] else n):
            rows = [v for k, v in m['thr'].items() if k[3] == i and sel(k)]
            if not rows:
                continue
            cp = sum(r[0] for r in rows); ci = sum(r[1] for r in rows)
            tk = sum(r[2] for r in rows); busy = sum(r[3] for r in rows); nr = sum(r[4] for r in rows)
            tokr = sum(r[5] for r in rows); by = sum(r[7] for r in rows)
            first = sum(r[8] for r in rows); last = sum(r[9] for r in rows); gap = sum(r[10] for r in rows); tail = sum(r[11] for r in rows)
            lp = lps[i]
            threads.append(dict(thr=i, lp=lp, type=lp_type(lp), participation=cp / (cp + ci) if cp + ci else None,
                                busy_ms_per_cpu_lw=busy / 1e6 / lw if lw else None,
                                idle_ms_per_cpu_lw=(wall - busy) / 1e6 / lw if lw else None,
                                tasks_per_phase=tk / phases if phases else None,
                                us_per_task=busy / tk / 1e3 if tk else None,
                                rows_share=nr, mean_nt=tokr / nr if nr else None,
                                gbs_busy=by / busy if busy else None,       # bytes per ns == GB/s
                                mean_first_start_us=first / cp / 1e3 if cp else None,
                                mean_finish_us=last / cp / 1e3 if cp else None,
                                mean_gap_to_fastest_us=gap / cp / 1e3 if cp else None,
                                mean_tail_idle_us=tail / cp / 1e3 if cp else None))
        tot_rows = sum(t['rows_share'] for t in threads) or 1
        for t in threads:
            t['rows_share'] = t['rows_share'] / tot_rows
        e['threads'] = threads
        grp = {}
        for g in ('P', 'E', 'host'):
            ts = [t for t in threads if t['type'] == g]
            if not ts:
                continue
            f = lambda key: sum(t[key] for t in ts if t[key] is not None) / len(ts)
            grp[g] = dict(n=len(ts), mean_finish_us=f('mean_finish_us'), mean_gap_us=f('mean_gap_to_fastest_us'),
                          mean_busy_ms_lw=f('busy_ms_per_cpu_lw'), mean_gbs_busy=f('gbs_busy'), mean_us_per_task=f('us_per_task'),
                          mean_tasks_per_phase=f('tasks_per_phase'), rows_share_total=sum(t['rows_share'] for t in ts),
                          mean_first_start_us=f('mean_first_start_us'), mean_tail_idle_us=f('mean_tail_idle_us'))
        e['groups'] = grp
        if 'P' in grp and 'E' in grp and grp['P']['mean_finish_us']:
            e['E_vs_P_finish_pct'] = (grp['E']['mean_finish_us'] / grp['P']['mean_finish_us'] - 1) * 100
            e['E_vs_P_gbs_pct'] = (grp['E']['mean_gbs_busy'] / grp['P']['mean_gbs_busy'] - 1) * 100 if grp['P']['mean_gbs_busy'] else None
        out['per_T'][str(T)] = e
    return out


def verdict(a):
    e = a['per_T']['all']
    f20 = e.get('E_vs_P_finish_pct')
    w25 = e['host_wait_share_of_call']
    return dict(E_vs_P_finish_pct=f20, host_wait_share_of_call=w25, cond_finish_ge_20pct=bool(f20 is not None and f20 >= 20),
                cond_wait_ge_25pct=bool(w25 is not None and w25 >= 0.25),
                POOL_WORKER_SKEW_pass=bool(f20 is not None and f20 >= 20 and w25 is not None and w25 >= 0.25))


def micro_summary(dumps):
    acc = {}
    for d in dumps:
        for r in d.get('micro', []) or []:
            nt = r[0]
            a = acc.setdefault(nt, dict(n=0, gc=0, gw=0, rd=0, dn=0, bg=r[6], bd=r[7]))
            a['n'] += r[1]; a['gc'] += r[2]; a['gw'] += r[3]; a['rd'] += r[4]; a['dn'] += r[5]
    out = {}
    for nt, a in acc.items():
        n = a['n']
        out[nt] = dict(samples=n, bytes_gu=a['bg'], bytes_down=a['bd'], gu_cold_us=a['gc'] / n / 1e3, gu_warm_us=a['gw'] / n / 1e3,
                       read_cold_us=a['rd'] / n / 1e3, down_cold_us=a['dn'] / n / 1e3,
                       gu_cold_gbs=a['bg'] * n / a['gc'] if a['gc'] else None, gu_warm_gbs=a['bg'] * n / a['gw'] if a['gw'] else None,
                       read_cold_gbs=a['bg'] * n / a['rd'] if a['rd'] else None, down_cold_gbs=a['bd'] * n / a['dn'] if a['dn'] else None)
    return out


if __name__ == '__main__':
    runs = {p.parent.name.replace('run-', ''): load(p) for p in sorted(root.glob('run-*/wskew.json'))}
    res = dict(runs={})
    groups = {k: [v] for k, v in runs.items()}
    on = [v for k, v in runs.items() if k in ('ON1', 'ON2')]
    if on:
        groups['ON1+ON2'] = on
    allon = [v for k, v in runs.items() if k in ('ON1', 'ON2', 'MIC')]
    if allon:
        groups['ON1+ON2+MIC'] = allon
    for k, ds in groups.items():
        m = merge(ds)
        a = analyze(m, k)
        a['verdict'] = verdict(a)
        res['runs'][k] = a
    mic = [v for k, v in runs.items() if k == 'MIC']
    res['micro'] = micro_summary(mic) if mic else None
    outp = Path(sys.argv[2]) if len(sys.argv) > 2 else root / 'analysis.json'
    outp.write_text(json.dumps(res, indent=1))
    print('wrote', outp)
