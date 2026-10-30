#!/usr/bin/env python
# Strata nsys timeline analysis (attempt3). Local only, stdlib only. Run with: python -I analyze_timeline_20261027.py
# Reads trace-A.sqlite / trace-B.sqlite read-only, writes attempt3/analysis.json
import sqlite3, bisect, json, collections, statistics, sys, os

BASE = r'D:/strata/state/nsys-timeline-20261027/attempt3/'
OUT = BASE + 'analysis.json'
SPIN = 'wait_flag_ge_kernel'


def pct(a, p):
    if not a:
        return None
    a = sorted(a)
    return a[min(len(a) - 1, int(p / 100.0 * len(a)))]


def union(iv):
    iv = sorted(iv)
    out = []
    cs, ce = iv[0]
    for s, e in iv[1:]:
        if s <= ce:
            if e > ce:
                ce = e
        else:
            out.append((cs, ce))
            cs, ce = s, e
    out.append((cs, ce))
    return out


class U:
    """union of intervals with fast range-coverage query"""
    def __init__(self, iv):
        self.u = union(iv) if iv else []
        self.st = [s for s, e in self.u]
        self.cum = [0]
        for s, e in self.u:
            self.cum.append(self.cum[-1] + e - s)

    def cov(self, a, b):
        if b <= a or not self.u:
            return 0
        i = bisect.bisect_right(self.st, a) - 1
        tot = 0
        if i >= 0 and self.u[i][1] > a:
            tot += min(self.u[i][1], b) - a
        j = i + 1
        k = bisect.bisect_left(self.st, b)
        if k > j:
            tot += self.cum[k] - self.cum[j]
            if self.u[k - 1][1] > b:
                tot -= self.u[k - 1][1] - b
        return tot


def ulen(iv):
    return sum(e - s for s, e in union(iv)) if iv else 0


CAT = {}
def setcat(cat, names):
    for n in names.split():
        CAT[n] = cat

setcat('GDN(線性注意力)', 'gdn_step_norm_multi_kernel gdn_step_commit_kernel gdn_ab_multi_kernel gdn_conv_l2_multi_kernel gdn_conv_commit_kernel')
setcat('QSA 注意力(含 KV/rope)', 'attn_chunk_kernel attn_merge_kernel block_scores_multi_kernel block_topk_reg_kernel resolve_kernel copy_kernel kv_append_q4_kernel append fwht256_kernel norm_rope_kernel copy_from_mapped_kernel copy_indexed_kernel')
setcat('稠密投影 MMVQ/MMVF', 'native_mmvq_il_kernel native_mmvq_multi_kernel mmvq_multi_kernel native_q5_k_mmvq_kernel native_q6_k_mmvq_kernel native_q4_k_mmvq_kernel native_iq4_xs_mmvq_kernel native_small_mmvq_kernel native_q2_0_mmvq_kernel bf16_f32_mmvf_kernel native_quantize_q8_1_kernel native_q8_1_interleave_kernel')
setcat('router/topk/doorbell', 'route route_multi gate gate_kernel doorbell_publish_res_kernel bf16_f32_mmvf_multi_kernel copy_i32_from_mapped_kernel')
setcat('gr_*(hc/hyper-connection，推測)', 'gr_norm_split_kernel gr_up_multi_kernel gr_down_staged_kernel')
setcat('norm/elementwise', 'norm weighted_rms_norm post conv_residual_kernel history_advance_kernel sigmoid_scale_rows_vec4_kernel swiglu_quantize_q8_0_scaled_kernel quantize_q8_0_scaled_kernel native_swiglu_quantize_q8_1_kernel')
setcat('VRAM 路由專家(fork stream)', 'native_gu_multi_kernel native_down_multi_kernel swiglu_q8_1_entries_kernel quantize_q8_1_kernel fetch_blobs_kernel rebase_ptrs_kernel')
setcat('CPU 結果併回(copy_rows/add_hits/combine)', 'copy_rows_from_mapped_kernel add_hits_kernel combine_k10_vec4')
setcat('head/MTP/embed', 'argmax_rows_kernel mtp_select_kernel embed_rows_kernel row_top_prob_split_kernel norm_grouped copy_row_to_first_kernel add_streams_broadcast_kernel window_ids_kernel gu_grouped_t_kernel down_grouped_t_kernel group_resident_kernel')
SHARED_NAMES = set('native_quantize_q8_1_kernel native_mmvq_multi_kernel mmvq_multi_kernel native_swiglu_quantize_q8_1_kernel bf16_f32_mmvf_multi_kernel sigmoid_scale_rows_vec4_kernel'.split())
SH = '共享專家(主 stream，doorbell 後)'


def main():
    res = {}
    cA = sqlite3.connect('file:' + BASE + 'trace-A.sqlite?mode=ro', uri=True)
    names = dict(cA.execute('select id,value from StringIds').fetchall())
    K = cA.execute('select k.start,k.end,k.streamId,s.value,k.graphId,k.correlationId from CUPTI_ACTIVITY_KIND_KERNEL k join StringIds s on s.id=k.shortName order by k.start').fetchall()
    MC = cA.execute('select start,end,streamId,bytes,copyKind from CUPTI_ACTIVITY_KIND_MEMCPY order by start').fetchall()
    res['schema'] = {'kernels': len(K), 'memcpy': len(MC)}

    # ---- launches (kernels of one graph launch share a correlationId)
    byc = collections.defaultdict(list)
    for k in K:
        byc[k[5]].append(k)
    launches = sorted(byc.values(), key=lambda l: l[0][0])
    big = [l for l in launches if len(l) > 2000]
    small = [l for l in launches if len(l) <= 2000]
    res['launches'] = {'total': len(launches), 'big_window_graphs': len(big), 'small_graphs': len(small)}
    bigs = [(min(x[0] for x in l), max(x[1] for x in l)) for l in big]
    T0, T1 = bigs[0][0], bigs[-1][1]
    nwin = len(big)
    res['decode_range_s'] = {'start': T0 / 1e9, 'end': T1 / 1e9, 'len_s': (T1 - T0) / 1e9, 'windows': nwin,
                              'ms_per_window': (T1 - T0) / 1e6 / nwin}
    gv = collections.defaultdict(list)
    for l, (s, e) in zip(big, bigs):
        gv[l[0][4]].append((e - s) / 1e6)
    res['big_graph_variants'] = {str(g): {'n': len(v), 'span_ms_mean': statistics.mean(v), 'span_ms_p50': pct(v, 50)} for g, v in gv.items()}
    for l in big:
        res['big_graph_variants'][str(l[0][4])]['kernels'] = len(l)

    # ---- GPU union / idle gaps over decode range
    nons = [(max(k[0], T0), min(k[1], T1)) for k in K if k[3] != SPIN and k[1] > T0 and k[0] < T1]
    allk = [(max(k[0], T0), min(k[1], T1)) for k in K if k[1] > T0 and k[0] < T1]
    mcs = [(max(m[0], T0), min(m[1], T1)) for m in MC if m[1] > T0 and m[0] < T1]
    spin_total = sum(min(k[1], T1) - max(k[0], T0) for k in K if k[3] == SPIN and k[1] > T0 and k[0] < T1)
    U_all = U(allk + mcs)
    U_non = U(nons + mcs)
    U_nonk = U(nons)
    U_spin = U([(k[0], k[1]) for k in K if k[3] == SPIN])
    rng = T1 - T0
    busy_all = U_all.cum[-1]
    busy_non = U_non.cum[-1]
    res['gpu_union'] = {
        'range_ms': rng / 1e6,
        'busy_any_incl_spin_ms': busy_all / 1e6, 'busy_any_pct': 100.0 * busy_all / rng,
        'busy_nonspin_ms': busy_non / 1e6, 'busy_nonspin_pct': 100.0 * busy_non / rng,
        'busy_nonspin_kernels_only_ms': U_nonk.cum[-1] / 1e6,
        'spin_kernel_sum_ms_raw': spin_total / 1e6,
        'spin_union_ms': U_spin.cum[-1] / 1e6,
        'no_kernel_at_all_ms': (rng - busy_all) / 1e6,
        'per_window_ms': {'busy_any': busy_all / 1e6 / nwin, 'busy_nonspin': busy_non / 1e6 / nwin,
                          'no_kernel': (rng - busy_all) / 1e6 / nwin, 'spin_only': (busy_all - busy_non) / 1e6 / nwin},
    }

    def gaps(u, lo, hi):
        g = []
        prev = lo
        for s, e in u.u:
            if e <= lo:
                continue
            if s >= hi:
                break
            if s > prev:
                g.append(s - prev)
            prev = max(prev, e)
        if hi > prev:
            g.append(hi - prev)
        return g

    def gapstats(g):
        g2 = [x / 1e3 for x in g]
        bins = [(0, 10), (10, 100), (100, 1000), (1000, 5000), (5000, 1e12)]
        lab = ['<10us', '10-100us', '0.1-1ms', '1-5ms', '>5ms']
        b = {}
        for (a, c), n in zip(bins, lab):
            sel = [x for x in g2 if a <= x < c]
            b[n] = {'count': len(sel), 'total_ms': sum(sel) / 1e3}
        return {'count': len(g2), 'total_ms': sum(g2) / 1e3, 'p50_us': pct(g2, 50), 'p90_us': pct(g2, 90), 'p99_us': pct(g2, 99),
                'max_us': max(g2) if g2 else None, 'bins': b}
    res['idle_gaps_no_kernel'] = gapstats(gaps(U_all, T0, T1))
    res['idle_gaps_nonspin'] = gapstats(gaps(U_non, T0, T1))

    # ---- per-layer parse of big launches
    phase_iv = []
    wins = []
    catsum = collections.defaultdict(float)
    catn = collections.Counter()
    streams_ov = collections.defaultdict(float)
    sh_ov = 0.0
    sh_tot = 0.0
    fk_tot = 0.0
    long_wait_sum = 0.0
    long_wait_n = 0
    post_all = []
    for wi, (l, (ls, le)) in enumerate(zip(big, bigs)):
        ks = sorted(l, key=lambda x: x[0])
        D = [k for k in ks if k[3] == 'doorbell_publish_res_kernel']
        CR = [k for k in ks if k[3] == 'copy_rows_from_mapped_kernel']
        if len(D) != 48 or len(CR) != 48:
            res.setdefault('layer_parse_anomalies', []).append({'win': wi, 'D': len(D), 'CR': len(CR)})
            continue
        M = D[0][2]
        Fs = CR[0][2]
        nsk = [k for k in ks if k[3] != SPIN]
        nsU = U([(k[0], k[1]) for k in nsk])
        R = [c[0] for c in CR]
        Dst = [d[0] for d in D]
        Den = [d[1] for d in D]
        w = {'gid': l[0][4], 'ls': ls, 'le': le, 'pre': 0, 'post': 0, 'post_gpu_covered': 0, 'post_gpu_busy': 0, 'exposed': 0, 'pre_gpu_busy': 0,
             'head_in': Dst[0] - ls, 'tail': le - R[-1]}
        w['head_in_busy'] = nsU.cov(ls, Dst[0])
        w['tail_busy'] = nsU.cov(R[-1], le)
        phase_iv.append((ls, Dst[0], 'head'))
        post_rng = []
        for i in range(48):
            a, b = Den[i], R[i]
            post_rng.append((Dst[i], b))
            post_all.append((a, b))
            post_k = [k for k in nsk if k[0] >= Dst[i] and k[0] < b]
            Gend = a
            for k in post_k:
                if k[1] > Gend and k[1] <= b + 2000:
                    Gend = k[1]
            Gend = min(Gend, b)
            w['post'] += b - a
            w['post_gpu_busy'] += nsU.cov(a, b)
            w['post_gpu_covered'] += Gend - a
            w['exposed'] += b - Gend
            phase_iv.append((Dst[i], b, 'post'))
            fk = [(k[0], k[1]) for k in post_k if k[2] == Fs]
            mk = [(k[0], k[1]) for k in post_k if k[2] == M]
            if fk and mk:
                sh_ov += ulen(fk) + ulen(mk) - ulen(fk + mk)
            sh_tot += ulen(mk) if mk else 0
            fk_tot += ulen(fk) if fk else 0
            for k in post_k:
                if k[2] == M and k[3] in SHARED_NAMES:
                    c = SH
                else:
                    c = CAT.get(k[3], 'other:' + k[3])
                catsum[c] += k[1] - k[0]
                catn[c] += 1
            ws = [k for k in ks if k[3] == SPIN and k[2] == Fs and k[1] > b - 3000 and k[1] <= b + 3000]
            if ws:
                long_wait_sum += max(k[1] - k[0] for k in ws)
                long_wait_n += 1
            if i < 47:
                a2, b2 = R[i], Dst[i + 1]
                w['pre'] += b2 - a2
                w['pre_gpu_busy'] += nsU.cov(a2, b2)
                phase_iv.append((a2, b2, 'pre'))
        phase_iv.append((R[-1], le, 'tail'))
        wins.append(w)
        starts = [a for a, b in post_rng]
        for k in nsk:
            j = bisect.bisect_right(starts, k[0]) - 1
            if j >= 0 and k[0] < post_rng[j][1]:
                continue
            c = CAT.get(k[3], 'other:' + k[3])
            catsum[c] += k[1] - k[0]
            catn[c] += 1
        ev = []
        for k in nsk:
            ev.append((k[0], 1, k[2]))
            ev.append((k[1], -1, k[2]))
        ev.sort()
        act = collections.Counter()
        last = ev[0][0]
        for t, d, s in ev:
            n = sum(1 for v in act.values() if v > 0)
            streams_ov[n] += t - last
            last = t
            act[s] += d

    cyc = []
    for i in range(len(bigs)):
        a = bigs[i][0]
        b = bigs[i + 1][0] if i + 1 < len(bigs) else bigs[i][1]
        cyc.append((a, b))
    per = collections.defaultdict(list)
    for (a, b), (s, e) in zip(cyc, bigs):
        per['cycle_ms'].append((b - a) / 1e6)
        per['big_graph_span'].append((e - s) / 1e6)
        per['busy_nonspin'].append(U_non.cov(a, b) / 1e6)
        per['busy_any'].append(U_all.cov(a, b) / 1e6)
        per['no_kernel'].append((b - a - U_all.cov(a, b)) / 1e6)
        per['spin_only'].append((U_all.cov(a, b) - U_non.cov(a, b)) / 1e6)
        per['between_graphs'].append((b - e) / 1e6)
        per['between_graphs_busy_nonspin'].append(U_non.cov(e, b) / 1e6)
    st = lambda a: {'mean': statistics.mean(a), 'p50': pct(a, 50), 'p90': pct(a, 90), 'min': min(a), 'max': max(a)}
    res['per_window_cycle'] = {k: st(v) for k, v in per.items()}

    nw = len(wins)
    def avg(key):
        return sum(w[key] for w in wins) / nw / 1e6
    res['layer_cycle'] = {
        'windows_parsed': nw,
        'per_window_ms': {k: avg(k) for k in ['head_in', 'pre', 'post', 'post_gpu_busy', 'post_gpu_covered', 'exposed', 'pre_gpu_busy', 'tail', 'head_in_busy', 'tail_busy']},
        'per_layer_us': {'pre': avg('pre') * 1e3 / 47, 'post': avg('post') * 1e3 / 48, 'exposed': avg('exposed') * 1e3 / 48,
                         'post_covered': avg('post_gpu_covered') * 1e3 / 48},
        'long_final_wait_mean_us': long_wait_sum / max(1, long_wait_n) / 1e3,
        'long_final_wait_total_ms_per_window': long_wait_sum / 1e6 / nw,
    }
    lc = res['layer_cycle']['per_window_ms']
    lc['sum_check'] = lc['head_in'] + lc['pre'] + lc['post'] + lc['tail']
    res['layer_cycle']['post_dur_us_dist'] = None
    res['categories_ms_per_window'] = {k: v / 1e6 / nw for k, v in sorted(catsum.items(), key=lambda x: -x[1])}
    res['categories_kernel_counts_per_window'] = {k: catn[k] / nw for k in res['categories_ms_per_window']}
    res['categories_note'] = 'big window graphs only; kernel time sums (concurrent streams double count); wait_flag spin excluded'
    sm = collections.defaultdict(float)
    smspan = 0
    for l in small:
        for k in l:
            if k[3] != SPIN:
                sm[k[3]] += k[1] - k[0]
        smspan += max(x[1] for x in l) - min(x[0] for x in l)
    res['small_graphs'] = {'count': len(small), 'per_window': len(small) / nwin, 'span_ms_per_window_sum': smspan / 1e6 / nwin,
                           'nonspin_kernel_ms_per_window': sum(sm.values()) / 1e6 / nwin,
                           'top': {k: v / 1e6 / nwin for k, v in sorted(sm.items(), key=lambda x: -x[1])[:10]}}
    res['concurrency_ms_per_window'] = {'streams_active_%s' % k: v / 1e6 / nw for k, v in sorted(streams_ov.items())}
    res['shared_expert_overlap'] = {'main_post_nonspin_union_ms_per_window': sh_tot / 1e6 / nw, 'fork_post_nonspin_union_ms_per_window': fk_tot / 1e6 / nw,
                                    'overlap_main_fork_ms_per_window': sh_ov / 1e6 / nw}

    # ---- memcpy
    mc = collections.defaultdict(lambda: [0, 0, 0])
    for m in MC:
        if m[1] > T0 and m[0] < T1:
            r = mc[(m[2], m[4])]
            r[0] += 1
            r[1] += m[3]
            r[2] += m[1] - m[0]
    res['memcpy_in_range'] = {'stream%d_kind%d' % k: {'n': v[0], 'GB': v[1] / 1e9, 'ms': v[2] / 1e6, 'n_per_window': v[0] / nwin, 'ms_per_window': v[2] / 1e6 / nwin} for k, v in mc.items()}
    mo = collections.Counter()
    for m in MC:
        if m[1] > T0 and m[0] < T1 and m[2] == 21:
            mo['copy_ns'] += m[1] - m[0]
            mo['overlap_nonspin_kernels'] += U_nonk.cov(m[0], m[1])
            mo['overlap_spin'] += U_spin.cov(m[0], m[1])
    res['swap_copy_overlap_ms_per_window'] = {k: v / 1e6 / nwin for k, v in mo.items()}

    # ---- runtime API by thread
    rt = cA.execute('select start,end,globalTid,nameId from CUPTI_ACTIVITY_KIND_RUNTIME where end>? and start<?', (T0, T1)).fetchall()
    api = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for s, e, t, n in rt:
        nm = names[n].split('_v')[0]
        r = api[t][nm]
        r[0] += 1
        r[1] += e - s
    host_tid = max(api, key=lambda t: api[t]['cudaGraphLaunch'][1])
    res['host_thread_tid'] = host_tid
    res['host_api_per_window'] = {}
    for t, d in api.items():
        for nm, (n, ns) in d.items():
            if ns > 5e6:
                res['host_api_per_window'].setdefault(str(t), {})[nm] = {'calls_per_win': n / nwin, 'ms_per_win': ns / 1e6 / nwin, 'avg_us': ns / n / 1e3}

    # ---- CPU sampling
    samp_rows = cA.execute('select e.start,e.globalTid,s.symbol,s.module from COMPOSITE_EVENTS e join SAMPLING_CALLCHAINS s on s.id=e.id where e.start>=? and e.start<?', (T0, T1)).fetchall()
    sc = []
    for t, tid, sym, mod in samp_rows:
        nmv = names[sym]
        ip = int(nmv, 16) if nmv.startswith('0x') else -1
        sc.append((t, tid, ip, 'strata.exe' in names[mod]))
    cnt = collections.Counter(s[1] for s in sc)
    thr = [t for t, n in cnt.items() if n > 0.3 * (T1 - T0) / 1e6]
    workers = [t for t in thr if t != host_tid]
    res['cpu_threads'] = {'busy_threads': len(thr), 'workers': len(workers), 'host': host_tid,
                          'sampling_hz': 1000, 'samples_in_range': {str(t): cnt[t] for t in thr},
                          'expected_samples_if_always_running': (T1 - T0) / 1e6}
    phase_iv.sort()
    pst = [p[0] for p in phase_iv]
    def phase_of(t):
        j = bisect.bisect_right(pst, t) - 1
        if j >= 0 and t < phase_iv[j][1]:
            return phase_iv[j][2]
        return 'between'
    wset = set(workers)
    hist = {'workers': collections.defaultdict(collections.Counter), 'host': collections.defaultdict(collections.Counter)}
    for t, tid, ip, ok in sc:
        if tid in wset:
            who = 'workers'
        elif tid == host_tid:
            who = 'host'
        else:
            continue
        hist[who][phase_of(t)][ip >> 8 if ok else -1] += 1
    phase_time = collections.Counter()
    for a, b, lab in phase_iv:
        phase_time[lab] += b - a
    phase_time['between'] = (T1 - T0) - sum(phase_time.values())
    res['phase_time_ms_per_window'] = {k: v / 1e6 / nwin for k, v in phase_time.items()}
    res['sample_page_by_phase'] = {}
    for who in hist:
        res['sample_page_by_phase'][who] = {}
        for ph, c in hist[who].items():
            tot = sum(c.values())
            res['sample_page_by_phase'][who][ph] = {'n': tot, 'top_pages': [[hex(k << 8) if k >= 0 else 'non-strata', round(v / tot, 4)] for k, v in c.most_common(10)]}

    def split(who_set, lo, hi):
        r_ = collections.defaultdict(collections.Counter)
        for t, tid, ip, ok in sc:
            if tid not in who_set:
                continue
            ph = phase_of(t)
            if ok and lo <= ip < hi:
                r_[ph]['spin'] += 1
            elif ok:
                r_[ph]['strata_other'] += 1
            else:
                r_[ph]['non_strata'] += 1
        return r_
    w_lo = split(wset, 0x7ff764e10800, 0x7ff764e10900)
    w_hi = split(wset, 0x7ff764e10800, 0x7ff764e10a00)
    totw = sum(sum(c.values()) for c in w_hi.values())
    res['workers_classified'] = {
        'note': 'sample = 1 ms of one worker thread; spin pages inferred from address (no symbols). lo = page 0x..e10800 only; hi = e10800+e10900',
        'total_samples': totw, 'samples_per_window': totw / nwin,
        'by_phase_lo': {ph: dict(c) for ph, c in w_lo.items()},
        'by_phase_hi': {ph: dict(c) for ph, c in w_hi.items()},
    }
    res['worker_thread_ms_per_window'] = {
        'compute_if_e10900_is_spin': sum(c['strata_other'] for c in w_hi.values()) / nwin,
        'compute_if_e10900_is_compute': sum(c['strata_other'] for c in w_lo.values()) / nwin,
        'spin_lo': sum(c['spin'] for c in w_lo.values()) / nwin,
        'spin_hi': sum(c['spin'] for c in w_hi.values()) / nwin,
        'non_strata(kernel/OS)': sum(c['non_strata'] for c in w_hi.values()) / nwin,
    }
    hh = collections.defaultdict(collections.Counter)
    for t, tid, ip, ok in sc:
        if tid == host_tid:
            hh[phase_of(t)][(hex((ip >> 8) << 8) if ok else 'non-strata')] += 1
    res['host_pages'] = {ph: {'n': sum(c.values()), 'top': [[k, v] for k, v in c.most_common(8)]} for ph, c in hh.items()}

    se = cA.execute('select start,isSchedIn,globalTid from SCHED_EVENTS where globalTid in (%s) order by globalTid,start' % ','.join(str(t) for t in thr)).fetchall()
    run = collections.Counter()
    lastin = {}
    for s, isin, tid in se:
        if isin:
            lastin[tid] = s
        elif tid in lastin:
            a, b = max(lastin[tid], T0), min(s, T1)
            if b > a:
                run[tid] += b - a
            del lastin[tid]
    res['sched_running_pct'] = {str(t): 100.0 * run[t] / (T1 - T0) for t in thr}

    # ---- trace B cross-check (graph level)
    cB = sqlite3.connect('file:' + BASE + 'trace-B.sqlite?mode=ro', uri=True)
    G = cB.execute('select start,end,streamId,graphId from CUPTI_ACTIVITY_KIND_GRAPH_TRACE order by start').fetchall()
    MB = cB.execute('select start,end,streamId,bytes,copyKind from CUPTI_ACTIVITY_KIND_MEMCPY order by start').fetchall()
    gb = [g for g in G if g[1] - g[0] > 5e6 and g[2] == 19]
    TB0, TB1 = gb[0][0], gb[-1][1]
    nwB = len(gb)
    UB_g = U([(g[0], g[1]) for g in G])
    UB_gm = U([(g[0], g[1]) for g in G] + [(m[0], m[1]) for m in MB])
    rB = TB1 - TB0
    spans = [(g[1] - g[0]) / 1e6 for g in gb]
    bvar = collections.defaultdict(list)
    for g in gb:
        bvar[g[3]].append((g[1] - g[0]) / 1e6)
    res['trace_B'] = {'big_windows': nwB, 'range_ms': rB / 1e6, 'ms_per_window': rB / 1e6 / nwB,
                      'graph_busy_pct': 100.0 * UB_g.cov(TB0, TB1) / rB,
                      'graph_or_memcpy_busy_pct': 100.0 * UB_gm.cov(TB0, TB1) / rB,
                      'no_graph_ms_per_window': (rB - UB_g.cov(TB0, TB1)) / 1e6 / nwB,
                      'big_graph_span_ms_per_window': sum(spans) / nwB,
                      'small_graphs_per_window': (len(G) - nwB) / nwB,
                      'variants': {str(k): {'n': len(v), 'span_ms_mean': statistics.mean(v)} for k, v in bvar.items()}}
    gapsB = []
    prev = TB0
    for s, e in UB_g.u:
        if e <= TB0:
            continue
        if s >= TB1:
            break
        if s > prev:
            gapsB.append(s - prev)
        prev = max(prev, e)
    res['trace_B']['gaps_no_graph'] = gapstats(gapsB)
    GA = [(min(x[0] for x in l), max(x[1] for x in l)) for l in launches]
    UA_g = U(GA)
    res['trace_A_graph_level'] = {'graph_busy_pct': 100.0 * UA_g.cov(T0, T1) / (T1 - T0),
                                  'no_graph_ms_per_window': ((T1 - T0) - UA_g.cov(T0, T1)) / 1e6 / nwin,
                                  'big_graph_span_ms_per_window': sum((e - s) for s, e in bigs) / 1e6 / nwin,
                                  'small_graphs_per_window': len(small) / nwin}
    # ================= extra analyses =================
    # 1) per graph variant (T inferred: mean T from variant counts matches engine avg T 1.94)
    byv = collections.defaultdict(list)
    for w in wins:
        byv[w['gid']].append(w)
    order = sorted(byv, key=lambda g: len(big[[x[0][4] for x in big].index(g)]))
    res['variants_table'] = {}
    for rank, g in enumerate(order, 1):
        v = byv[g]
        n = len(v)
        m = lambda key: sum(x[key] for x in v) / n / 1e6
        res['variants_table'][str(g)] = {'rank_by_kernels': rank, 'n': n, 'span_ms': sum(x['le'] - x['ls'] for x in v) / n / 1e6,
                                          'pre_ms': m('pre'), 'post_ms': m('post'), 'post_gpu_busy_ms': m('post_gpu_busy'),
                                          'pre_gpu_busy_ms': m('pre_gpu_busy')}
    cnts = {g: len(byv[g]) for g in order}
    # 2) post-duration heavy tail
    pd_ = sorted((b - a) / 1e3 for a, b in post_all)
    tot_ = sum(pd_)
    res['post_tail'] = {'n_layers': len(pd_), 'mean_us': tot_ / len(pd_),
                        'pcts_us': {str(q): pd_[min(len(pd_) - 1, int(len(pd_) * q / 100.0))] for q in (5, 25, 50, 75, 90, 95, 99, 99.9)},
                        'thresholds': {}}
    for th in (250, 500, 1000, 2000, 5000, 10000):
        sel = [x for x in pd_ if x >= th]
        res['post_tail']['thresholds'][str(th)] = {'layers': len(sel), 'layer_pct': 100.0 * len(sel) / len(pd_), 'post_time_pct': 100.0 * sum(sel) / tot_,
                                                  'ms_per_window': sum(sel) / 1e3 / nw}
    # 3) post bucket x sample classification
    post_sorted = sorted(post_all)
    pst2 = [a for a, b in post_sorted]
    def bucket(d):
        d /= 1e3
        return '<250us' if d < 250 else '250-1000us' if d < 1000 else '1-5ms' if d < 5000 else '>5ms'
    btime = collections.Counter()
    bn = collections.Counter()
    for a, b in post_sorted:
        btime[bucket(b - a)] += b - a
        bn[bucket(b - a)] += 1
    agg = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    mod_name = {}
    for t, tid, ip, ok in sc:
        j = bisect.bisect_right(pst2, t) - 1
        if j < 0 or t >= post_sorted[j][1]:
            continue
        bk = bucket(post_sorted[j][1] - post_sorted[j][0])
        if tid in wset:
            cls = 'spin' if (ok and 0x7ff764e10800 <= ip < 0x7ff764e10a00) else ('compute' if ok else 'nonstrata')
            agg[bk]['workers'][cls] += 1
        elif tid == host_tid:
            if not ok:
                cls = 'nonstrata'
            elif 0x7ff764e10300 <= ip < 0x7ff764e10400:
                cls = 'e103xx'
            elif 0x7ff764cb4000 <= ip < 0x7ff764cb4200:
                cls = 'gpu_poll_cb4xxx'
            elif 0x7ff764e10800 <= ip < 0x7ff764e10a00:
                cls = 'spin'
            else:
                cls = 'compute_other'
            agg[bk]['host'][cls] += 1
    res['post_buckets'] = {}
    for bk in ['<250us', '250-1000us', '1-5ms', '>5ms']:
        wm = btime[bk] / 1e6
        wk = agg[bk]['workers']
        hs = agg[bk]['host']
        res['post_buckets'][bk] = {
            'layers': bn[bk], 'wall_ms_per_window': wm / nw,
            'worker_compute_thread_ms_per_window': wk['compute'] / nw, 'worker_spin_thread_ms_per_window': wk['spin'] / nw,
            'worker_compute_share': wk['compute'] / max(1, sum(wk.values())),
            'host_running_thread_per_wall': sum(hs.values()) / wm,
            'host_class_share': {k: v / max(1, sum(hs.values())) for k, v in hs.items()},
            'stall_ms_per_window': wm / nw - wk['compute'] / nw / 9.0}
    wc_tot = sum(res['post_buckets'][b]['worker_compute_thread_ms_per_window'] for b in res['post_buckets'])
    res['cpu_compute_summary'] = {'worker_compute_thread_ms_per_window': wc_tot,
                                  'balanced_wall_ms_if_9_workers': wc_tot / 9.0,
                                  'post_wall_ms_per_window': sum(res['post_buckets'][b]['wall_ms_per_window'] for b in res['post_buckets']),
                                  'host_compute_other_thread_ms_per_window': sum(agg[b]['host']['compute_other'] for b in agg) / nw,
                                  'host_e103xx_thread_ms_per_window': sum(agg[b]['host']['e103xx'] for b in agg) / nw}
    res['cpu_compute_summary']['non_compute_wall_ms'] = res['cpu_compute_summary']['post_wall_ms_per_window'] - res['cpu_compute_summary']['balanced_wall_ms_if_9_workers']
    # 4) overlap sample-based: P(GPU non-spin busy | worker compute sample)
    hit = 0.0
    ncs = 0
    hit_all = 0.0
    for t, tid, ip, ok in sc:
        if tid in wset and ok and not (0x7ff764e10800 <= ip < 0x7ff764e10a00) and T0 <= t < T1:
            ncs += 1
            hit += U_non.cov(t, t + 2000) / 2000.0
            hit_all += U_all.cov(t, t + 2000) / 2000.0
    res['overlap_samples'] = {'worker_compute_samples': ncs, 'p_gpu_nonspin_busy_given_cpu_compute': hit / ncs, 'p_gpu_any_kernel_given_cpu_compute': hit_all / ncs}
    # GPU non-spin busy that lies inside post phases / total
    res['overlap_phase'] = {'gpu_nonspin_busy_in_post_ms_per_window': lc['post_gpu_busy'],
                            'share_of_gpu_nonspin_busy': lc['post_gpu_busy'] / (busy_non / 1e6 / nwin),
                            'share_of_post_time_gpu_busy': lc['post_gpu_busy'] / lc['post']}
    # 5) swaps in between-graph gaps
    M21 = [m for m in MC if m[2] == 21]
    ms21 = [m[0] for m in M21]
    swg, nswg = [], []
    for i in range(len(bigs) - 1):
        e, s_ = bigs[i][1], bigs[i + 1][0]
        a = bisect.bisect_left(ms21, e)
        b = bisect.bisect_left(ms21, s_)
        (swg if b > a else nswg).append(((s_ - e) / 1e6, b - a, (M21[b - 1][1] - M21[a][0]) / 1e6 if b > a else 0))
    inside = sum(1 for m in M21 if any(False for _ in ()))
    res['swap_gap'] = {'swap_windows': len(swg), 'no_swap_windows': len(nswg),
                       'gap_ms_mean_swap': statistics.mean(x[0] for x in swg), 'gap_ms_median_swap': statistics.median(x[0] for x in swg),
                       'gap_ms_mean_noswap': statistics.mean(x[0] for x in nswg), 'gap_ms_median_noswap': statistics.median(x[0] for x in nswg),
                       'copies_per_swap_window': statistics.mean(x[1] for x in swg), 'copy_burst_ms_mean': statistics.mean(x[2] for x in swg),
                       'avg_cost_ms_per_window': (statistics.mean(x[0] for x in swg) - statistics.mean(x[0] for x in nswg)) * len(swg) / nwin}
    bs = [b[0] for b in bigs]
    res['swap_gap']['copies_starting_inside_window_graph'] = sum(1 for m in M21 if (lambda j: j >= 0 and m[0] < bigs[j][1])(bisect.bisect_right(bs, m[0]) - 1))
    # 6) head stall vs cudaGraphLaunch call
    glaunch = {}
    for s, e, t, n in rt:
        if names[n].startswith('cudaGraphLaunch'):
            pass
    rtall = cA.execute('select start,end,correlationId,nameId from CUPTI_ACTIVITY_KIND_RUNTIME').fetchall()
    glc = {r[2]: r for r in rtall if names[r[3]].startswith('cudaGraphLaunch')}
    rows_ = []
    for l in big:
        corr = l[0][5]
        if corr not in glc:
            continue
        g = glc[corr]
        ks = sorted(l, key=lambda x: x[0])
        best = (0, 0)
        for i in range(1, 60):
            d = ks[i][0] - ks[i - 1][1]
            if d > best[0]:
                best = (d, i)
        rows_.append(((g[1] - g[0]) / 1e3, best[0] / 1e3, best[1], (ks[best[1]][0] - g[1]) / 1e3))
    cB2 = cB
    namesB = dict(cB2.execute('select id,value from StringIds').fetchall())
    rtB = {r[4]: r for r in cB2.execute('select start,end,globalTid,nameId,correlationId from CUPTI_ACTIVITY_KIND_RUNTIME').fetchall() if namesB[r[3]].startswith('cudaGraphLaunch')}
    GB = cB2.execute('select start,end,streamId,graphId,correlationId from CUPTI_ACTIVITY_KIND_GRAPH_TRACE').fetchall()
    bcalls = [(rtB[g[4]][1] - rtB[g[4]][0]) / 1e3 for g in GB if g[1] - g[0] > 5e6 and g[2] == 19 and g[4] in rtB]
    scalls = [(rtB[g[4]][1] - rtB[g[4]][0]) / 1e3 for g in GB if not (g[1] - g[0] > 5e6 and g[2] == 19) and g[4] in rtB]
    res['head_stall'] = {'A_big_launch_call_us_mean': statistics.mean(r[0] for r in rows_), 'A_big_launch_call_us_p50': statistics.median(r[0] for r in rows_),
                         'A_head_gap_us_mean': statistics.mean(r[1] for r in rows_), 'A_head_gap_us_p50': statistics.median(r[1] for r in rows_),
                         'A_gap_after_kernel_index_mode': collections.Counter(r[2] for r in rows_).most_common(2),
                         'A_gap_end_minus_launch_return_us_mean': statistics.mean(r[3] for r in rows_),
                         'B_big_launch_call_us_mean': statistics.mean(bcalls), 'B_big_launch_call_us_p50': statistics.median(bcalls),
                         'B_small_launch_call_us_mean': statistics.mean(scalls)}
    # 7) host off-CPU
    ev = cA.execute('select start,isSchedIn from SCHED_EVENTS where globalTid=? and start between ? and ? order by start', (host_tid, T0, T1)).fetchall()
    outs = [(ev[i][0], ev[i + 1][0]) for i in range(len(ev) - 1) if ev[i][1] == 0 and ev[i + 1][1] == 1]
    dist = [(b - a) / 1e3 for a, b in outs]
    res['host_offcpu'] = {'events': len(outs), 'ms_per_window': sum(dist) / 1e3 / nwin,
                          'ge_1ms_events': sum(1 for d in dist if d >= 1000), 'ge_1ms_ms_per_window': sum(d for d in dist if d >= 1000) / 1e3 / nwin}
    # 8) bounds
    gp = res['gpu_union']['per_window_ms']
    lcw = res['layer_cycle']['per_window_ms']
    cyc_mean = res['per_window_cycle']['cycle_ms']['mean']
    tokw = 1024.0 / nwin
    base_tps = tokw / cyc_mean * 1000
    between_busy = res['per_window_cycle']['between_graphs_busy_nonspin']['mean']
    between = res['per_window_cycle']['between_graphs']['mean']
    acct = {'GPU critical busy (pre+head busy+tail+draft/small graphs)': lcw['pre_gpu_busy'] + lcw['head_in_busy'] + lcw['tail_busy'] + between_busy,
            'post (CPU-bound, GPU busy 3.5 hidden inside)': lcw['post'],
            'head launch stall (GPU idle until cudaGraphLaunch returns)': lcw['head_in'] - lcw['head_in_busy'],
            'between-graph idle (swap copies + residual host)': between - between_busy,
            'doorbell kernels + rounding': cyc_mean - (lcw['pre_gpu_busy'] + lcw['head_in_busy'] + lcw['tail_busy'] + between_busy) - lcw['post'] - (lcw['head_in'] - lcw['head_in_busy']) - (between - between_busy)}
    res['accounting_ms_per_window'] = acct
    gcrit = acct['GPU critical busy (pre+head busy+tail+draft/small graphs)']
    def tps(ms):
        return tokw / ms * 1000
    bounds = {'base': {'ms': cyc_mean, 'tok_s': base_tps}}
    for f in (0.2, 0.4):
        ms = cyc_mean - f * gcrit
        bounds['gpu_critical_minus_%d%%' % int(f * 100)] = {'saves_ms': f * gcrit, 'ms': ms, 'tok_s': tps(ms), 'gain_pct': 100 * (tps(ms) / base_tps - 1)}
    sw_cost = res['swap_gap']['avg_cost_ms_per_window']
    stall = acct['head launch stall (GPU idle until cudaGraphLaunch returns)']
    for nm, x in (('fill_swap_copies_in_gap', sw_cost), ('remove_head_stall_A_artifact_upper', stall), ('head_stall_realistic_0.4ms', 0.4)):
        ms = cyc_mean - x
        bounds[nm] = {'saves_ms': x, 'ms': ms, 'tok_s': tps(ms), 'gain_pct': 100 * (tps(ms) / base_tps - 1)}
    cs = res['cpu_compute_summary']
    cc = cs['balanced_wall_ms_if_9_workers'] + cs['host_compute_other_thread_ms_per_window'] / 10.0 * 0
    for nm, x in (('cpu_compute_minus20_compute_only', 0.2 * cs['balanced_wall_ms_if_9_workers']), ('cpu_post_minus20_whole', 0.2 * cs['post_wall_ms_per_window']),
                  ('cpu_stall_ge1ms_halved', 0.5 * (res['post_buckets']['1-5ms']['stall_ms_per_window'] + res['post_buckets']['>5ms']['stall_ms_per_window']))):
        ms = cyc_mean - x
        bounds[nm] = {'saves_ms': x, 'ms': ms, 'tok_s': tps(ms), 'gain_pct': 100 * (tps(ms) / base_tps - 1)}
    need = cyc_mean * (1 - 37.6 / 50.0)
    bounds['target_hermes_equivalent'] = {'required_window_cut_ms_for_37.6to50': need, 'required_cut_pct': 100 * (1 - 37.6 / 50.0)}
    G_ = busy_non / 1e6 / nwin
    C_ = lcw['post']
    idle_ = acct['head launch stall (GPU idle until cudaGraphLaunch returns)'] + acct['between-graph idle (swap copies + residual host)']
    bounds['serial_vs_max'] = {'gpu_nonspin_busy': G_, 'cpu_post': C_, 'idle': idle_, 'serial_sum': G_ + C_ + idle_, 'perfect_overlap_max': max(G_, C_) + idle_,
                               'observed': cyc_mean, 'overlap_achieved_ms': G_ + C_ + idle_ - cyc_mean,
                               'perfect_overlap_tok_s': tps(max(G_, C_) + idle_)}
    res['bounds'] = bounds
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)
    print('written', OUT)


if __name__ == '__main__':
    main()
