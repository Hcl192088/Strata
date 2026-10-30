#!/usr/bin/env python
# Strata nsys attempt5 (long-tail layers): local, stdlib only. Run: python -I analyze_timeline_attempt5.py stage1|stage2
# stage1: parse layers from trace-A.sqlite, collect samples of strata threads (with call stacks) in post phases, write rvas.json
# stage2: add symbols (symres.json) + ETL I/O (etlA.*.csv) and compute the long-tail attribution -> analysis5.json
import sqlite3, bisect, json, collections, statistics, sys, os, pickle, csv, time

W = r'D:/strata/state/nsys-timeline-20261027/attempt5/work/'
OUTD = r'D:/strata/state/nsys-timeline-20261027/attempt5/'
SPIN = 'wait_flag_ge_kernel'
STRATA_BASE = 0x7FF764B80000      # confirmed from ETW Image rows (see etlA.images.csv)


def pct(a, p):
    if not a:
        return None
    a = sorted(a)
    return a[min(len(a) - 1, int(p / 100.0 * len(a)))]


def stage1():
    t_start = time.time()
    c = sqlite3.connect('file:' + W + 'trace-A.sqlite?mode=ro', uri=True)
    names = dict(c.execute('select id,value from StringIds').fetchall())
    sess = c.execute('select utcEpochNs,systemClockNs from TARGET_INFO_SESSION_START_TIME').fetchone()
    K = c.execute('select k.start,k.end,k.streamId,s.value,k.graphId,k.correlationId from CUPTI_ACTIVITY_KIND_KERNEL k '
                  'join StringIds s on s.id=k.shortName order by k.start').fetchall()
    print('kernels', len(K), time.time() - t_start, flush=True)
    byc = collections.defaultdict(list)
    for k in K:
        byc[k[5]].append(k)
    launches = sorted(byc.values(), key=lambda l: l[0][0])
    big = [l for l in launches if len(l) > 2000]
    bigs = [(min(x[0] for x in l), max(x[1] for x in l)) for l in big]
    T0, T1 = bigs[0][0], bigs[-1][1]
    nwin = len(big)
    layers = []   # (win, li, Dst, Den, R, Dnext)  (Dnext None for last)
    wins = []
    for wi, (l, (ls, le)) in enumerate(zip(big, bigs)):
        ks = sorted(l, key=lambda x: x[0])
        D = [k for k in ks if k[3] == 'doorbell_publish_res_kernel']
        CR = [k for k in ks if k[3] == 'copy_rows_from_mapped_kernel']
        if len(D) != 48 or len(CR) != 48:
            continue
        wins.append((wi, ls, le, l[0][4]))
        for i in range(48):
            layers.append((wi, i, D[i][0], D[i][1], CR[i][0], D[i + 1][0] if i < 47 else None))
    print('windows', len(wins), 'layers', len(layers), 'range_s', T0 / 1e9, T1 / 1e9, flush=True)
    # host thread: runtime thread with most cudaGraphLaunch time
    rt = c.execute('select start,end,globalTid,nameId from CUPTI_ACTIVITY_KIND_RUNTIME where end>? and start<?', (T0, T1)).fetchall()
    api = collections.defaultdict(float)
    for s, e, t, n in rt:
        if names[n].startswith('cudaGraphLaunch'):
            api[t] += e - s
    host = max(api, key=api.get)
    gpid = c.execute("select globalPid from PROCESSES where name='strata.exe'").fetchone()[0]
    # swap memcpy (stream 21) intervals
    MC = c.execute('select start,end,streamId,bytes,copyKind from CUPTI_ACTIVITY_KIND_MEMCPY order by start').fetchall()
    # samples of strata threads in range
    cnt = collections.Counter()
    S = []
    for sid, st, tid, state in c.execute('select id,start,globalTid,threadState from COMPOSITE_EVENTS where start>=? and start<? and globalTid>? and globalTid<?',
                                          (T0, T1, gpid, gpid + (1 << 24))):
        S.append((sid, st, tid, state))
        cnt[tid] += 1
    print('strata samples in range', len(S), 'threads', len(cnt), 'host', host - gpid, flush=True)
    dur_s = (T1 - T0) / 1e9
    thr = {t: n for t, n in cnt.items() if n > 0.2 * dur_s * 1000}
    print('busy threads', len(thr), sorted(thr.values(), reverse=True), flush=True)
    # which samples need frames: those inside a post interval (host + workers)
    post_iv = sorted((r[3], r[4], idx) for idx, r in enumerate(layers))
    pst = [p[0] for p in post_iv]
    keep = {}
    for sid, st, tid, state in S:
        if tid not in thr:
            continue
        j = bisect.bisect_right(pst, st) - 1
        if j >= 0 and st < post_iv[j][1]:
            keep[sid] = (st, tid, post_iv[j][2], state)
    print('kept samples', len(keep), flush=True)
    # stream callchains
    symip = {}
    modinfo = {}
    stk = collections.defaultdict(list)
    n = 0
    for sid, sym, mod, depth, kern in c.execute('select id,symbol,module,stackDepth,kernelMode from SAMPLING_CALLCHAINS'):
        if sid not in keep:
            continue
        ip = symip.get(sym)
        if ip is None:
            v = names.get(sym, '')
            ip = int(v, 16) if v.startswith('0x') else -1
            symip[sym] = ip
        m = modinfo.get(mod)
        if m is None:
            p = names.get(mod, '').lower()
            m = ('strata' if p.endswith('strata.exe') else 'ntoskrnl' if 'ntoskrnl' in p else 'nvcuda' if 'nvcuda' in p else
                 'cupti' if 'cupti' in p or 'injection' in p else 'vcruntime' if 'vcruntime' in p else 'ntdll' if 'ntdll' in p else
                 'ntfs' if 'ntfs' in p else 'fltmgr' if 'fltmgr' in p else 'nvlddmkm' if 'nvlddmkm' in p else
                 'wdfilter' if 'wdfilter' in p else 'kernelbase' if 'kernelbase' in p or 'kernel32' in p else 'other:' + p.split('\\')[-1])
            modinfo[mod] = m
        stk[sid].append((depth, ip, m, kern))
        n += 1
    print('callchain rows used', n, time.time() - t_start, flush=True)
    for sid in stk:
        stk[sid].sort()
    rvas = set()
    for sid, fr in stk.items():
        for d, ip, m, k in fr:
            if m == 'strata' and ip >= STRATA_BASE:
                rvas.add(ip - STRATA_BASE)
    json.dump(sorted(rvas), open(W + 'rvas.json', 'w'))
    print('unique strata rvas', len(rvas), flush=True)
    names_small = {}
    # memcpy and misc for later
    pickle.dump(dict(sess=sess, K_summary=None, T0=T0, T1=T1, nwin=nwin, wins=wins, layers=layers, host=host, gpid=gpid, thr=thr, S_kept=keep,
                     stk=dict(stk), MC=MC, bigs=bigs), open(W + 'stage1.pkl', 'wb'), protocol=4)
    # also dump non-spin kernel intervals for per-layer GPU-busy (compact)
    nons = [(k[0], k[1]) for k in K if k[3] != SPIN and k[1] > T0 and k[0] < T1]
    pickle.dump(nons, open(W + 'nons.pkl', 'wb'), protocol=4)
    print('stage1 done', time.time() - t_start)



# ====================================================================== stage 2
class U:
    """union of intervals + fast overlap query"""
    def __init__(self, iv):
        iv = sorted(iv)
        out = []
        for a, b in iv:
            if b <= a:
                continue
            if out and a <= out[-1][1]:
                if b > out[-1][1]:
                    out[-1][1] = b
            else:
                out.append([a, b])
        self.u = out
        self.st = [x[0] for x in out]
        self.cum = [0]
        for a, b in out:
            self.cum.append(self.cum[-1] + b - a)

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


def load_io(path, sess, base_off):
    """ETW rows -> nsys time (ns).  ft(100ns FILETIME) -> qpc ticks -> ns - systemClockNs."""
    sysclk = sess[1]
    conv = lambda ft: (int(ft) - base_off) * 100 - sysclk
    rows = collections.defaultdict(list)
    for r in csv.reader(open(path, encoding='utf-8')):
        k = r[0]
        if k == 'FWRITE':
            continue
        rows[k].append(r)
    return rows, conv


def stage2():
    t0 = time.time()
    d = pickle.load(open(W + 'stage1.pkl', 'rb'))
    sym = json.load(open(W + 'symres.json'))
    nons = pickle.load(open(W + 'nons.pkl', 'rb'))
    layers, keep, stk, host, gpid, T0, T1, nwin = d['layers'], d['S_kept'], d['stk'], d['host'], d['gpid'], d['T0'], d['T1'], len(d['wins'])
    sess = d['sess']
    BASE_OFF = 134374190870760500
    res = {}
    post = [(r[4] - r[3]) for r in layers]
    res['layers'] = {'n': len(layers), 'windows_parsed': nwin, 'post_total_ms_per_window': sum(post) / 1e6 / nwin}
    cls = lambda p: 'short' if p < 250e3 else 'mid' if p < 1e6 else 'long'
    cc = collections.Counter(cls(p) for p in post)
    ct = collections.Counter()
    for p in post:
        ct[cls(p)] += p
    res['post_classes'] = {k: {'layers': cc[k], 'ms_per_window': ct[k] / 1e6 / nwin, 'pct_layers': 100 * cc[k] / len(post), 'pct_post': 100 * ct[k] / sum(post)} for k in cc}
    # ---------------- host scheduling timeline
    c = sqlite3.connect('file:' + W + 'trace-A.sqlite?mode=ro', uri=True)
    ev = c.execute('select start,isSchedIn,cpu,threadBlock,threadState from SCHED_EVENTS where globalTid=? and start between ? and ? order by start', (host, T0 - 10**7, T1 + 10**7)).fetchall()
    on, off = [], []   # on-CPU intervals, off-CPU intervals (+cpu,reason)
    cur_in = None
    cur_out = None
    for t, isin, cpu, blk, st in ev:
        if isin:
            if cur_out is not None:
                off.append((cur_out[0], t, cur_out[1], cur_out[2], cpu))
                cur_out = None
            cur_in = t
        else:
            if cur_in is not None:
                on.append((cur_in, t))
                cur_in = None
            if cur_out is None:
                cur_out = (t, cpu, blk)
    Uon = U(on)
    res['host_sched'] = {'on_ms_per_window': Uon.cov(T0, T1) / 1e6 / nwin, 'off_events': len(off),
                         'off_ms_per_window': sum(min(b, T1) - max(a, T0) for a, b, _, _, _ in off if b > T0 and a < T1) / 1e6 / nwin}
    # ---------------- ETW I/O (rows -> nsys time)
    rows, conv = load_io(W + 'etlA.io.csv', sess, BASE_OFF)
    fr = rows['FREAD']
    fend = collections.defaultdict(list)
    for r in rows['FEND']:
        fend[r[4]].append(int(r[1]))
    for k in fend:
        fend[k].sort()
    reads = []   # (tid, t_issue_ns, t_end_ns, size, offset, filekey)
    for r in fr:
        irp = r[6]
        t_ft = int(r[1])
        lst = fend.get(irp)
        te = None
        if lst:
            j = bisect.bisect_left(lst, t_ft)
            if j < len(lst):
                te = lst[j]
        if te is None:
            continue
        reads.append((int(r[8]), conv(t_ft), conv(te), int(r[5]), int(r[4]), r[10] if len(r) > 10 else ''))
    hf = []
    for r in rows['HFAULT']:
        tt = int(r[8], 16)
        hf.append((tt, conv(r[4]), conv(r[1]), int(r[9]), int(r[5], 16), r[7]))
    dreads = [(int(r[8]), conv(r[1]), int(r[7]) * 100, int(r[4])) for r in rows['DREAD']]   # tid, t_complete_ns, resp_ns(assumed 100 ns units), bytes
    res['etw_counts'] = {'FREAD': len(fr), 'FREAD_matched_end': len(reads), 'HFAULT': len(hf), 'DREAD': len(dreads)}
    # calibration of ETW->nsys clock: host off-CPU vs host I/O intervals
    host_io = [(a, b) for tid, a, b, sz, _, _ in reads if tid == host - gpid and b - a > 150e3] + [(a, b) for tid, a, b, _, _, _ in hf if tid == host - gpid and b - a > 150e3]
    Uoff = U([(a, b) for a, b, _, _, _ in off])
    best = None
    scores = []
    for shift_us in range(-3000, 3001, 50):
        sh = shift_us * 1000
        tot = ov = 0
        for a, b in host_io:
            if a + sh < T0 or a + sh > T1:
                continue
            tot += b - a
            ov += Uoff.cov(a + sh, b + sh)
        sc_ = ov / tot if tot else 0
        scores.append((shift_us, sc_))
        if best is None or sc_ > best[1]:
            best = (shift_us, sc_)
    res['clock_calibration'] = {'host_io_intervals': len(host_io), 'best_shift_us': best[0], 'best_overlap_frac': best[1],
                                'zero_shift_overlap_frac': dict(scores).get(0), 'scores_sample': scores[::10]}
    SH = best[0] * 1000
    htid = host - gpid
    BASE = STRATA_BASE
    # ---------------- host I/O interval sets (shifted to nsys clock)
    def sh_iv(lst):
        return [(a + SH, b + SH) for a, b in lst]
    big_iv = [(a, b) for tid, a, b, sz, _, _ in reads if tid == htid and sz >= 500000]
    smallr_iv = [(a, b) for tid, a, b, sz, _, _ in reads if tid == htid and sz < 500000]
    hf_iv = [(a, b) for tid, a, b, _, _, _ in hf if tid == htid]
    Ubig, Ush, Uhf = U(sh_iv(big_iv)), U(sh_iv(smallr_iv)), U(sh_iv(hf_iv))
    Uio = U(sh_iv(big_iv + smallr_iv + hf_iv))
    inr = lambda a: T0 <= a + SH < T1
    bigr = [r for r in reads if r[0] == htid and r[3] >= 500000 and inr(r[1])]
    durs = [(r[2] - r[1]) / 1e3 for r in bigr]
    res['host_big_reads'] = {'n_in_decode': len(bigr), 'GB': sum(r[3] for r in bigr) / 1e9, 'per_window': len(bigr) / nwin,
                             'MB_per_window': sum(r[3] for r in bigr) / 1e6 / nwin,
                             'avg_MB': sum(r[3] for r in bigr) / 1e6 / max(1, len(bigr)),
                             'dur_us': {q: pct(durs, q) for q in (5, 25, 50, 75, 90, 99)}, 'dur_mean_us': statistics.mean(durs),
                             'dur_sum_ms_per_window': sum(durs) / 1e3 / nwin, 'dur_ge_5ms': sum(1 for x in durs if x >= 5000),
                             'throughput_GBps_sync': sum(r[3] for r in bigr) / (sum(durs) * 1e3)}
    res['host_big_reads']['top_sizes'] = collections.Counter(r[3] for r in bigr).most_common(6)
    hfr = [h for h in hf if h[0] == htid and inr(h[1])]
    hd = [(h[2] - h[1]) / 1e3 for h in hfr]
    res['host_hard_faults'] = {'n': len(hfr), 'per_window': len(hfr) / nwin, 'MB': sum(h[3] for h in hfr) / 1e6, 'dur_us_p50': pct(hd, 50), 'dur_us_p90': pct(hd, 90),
                               'dur_us_p99': pct(hd, 99), 'sum_ms_per_window': sum(hd) / 1e3 / nwin}
    smr = [r for r in reads if r[0] == htid and r[3] < 500000 and inr(r[1])]
    res['host_small_reads'] = {'n': len(smr), 'MB': sum(r[3] for r in smr) / 1e6, 'sizes_top': collections.Counter(r[3] for r in smr).most_common(5)}
    oth = collections.Counter()
    othhf = collections.Counter()
    for r in reads:
        if r[0] != htid and inr(r[1]):
            oth[r[0]] += r[3]
    for h in hf:
        if h[0] != htid and inr(h[1]):
            othhf[h[0]] += 1
    res['other_threads_io'] = {'read_MB_by_tid': {str(k): v / 1e6 for k, v in oth.most_common(6)}, 'hardfaults_by_tid': {str(k): v for k, v in othhf.most_common(6)}}
    dr = [x for x in dreads if x[3] >= 500000 and inr(x[1])]
    res['disk_big_reads_service'] = {'n': len(dr), 'resp_us_p50': pct([x[2] / 1e3 for x in dr], 50), 'resp_us_p90': pct([x[2] / 1e3 for x in dr], 90),
                                      'resp_us_p99': pct([x[2] / 1e3 for x in dr], 99), 'note': 'DiskIo HighResResponseTime assumed in 100 ns units (inferred)'}
    # ---------------- per layer accounting
    sym_name = lambda ip: (sym.get(str(ip - BASE)) or [None])[0] or 'unk'

    def catof(fr):
        names_ = [sym_name(f[1]) for f in fr if f[2] == 'strata' and f[1] >= BASE]
        for n in names_:
            if 'read_direct' in n or 'FileExpertSource' in n:
                return 'read_direct (ReadFile submit + kernel copy)'
        for n in names_:
            if 'PleReader' in n:
                return 'PleReader::collect'
        for n in names_:
            if 'ExpertPool::wait_done' in n:
                return 'ExpertPool::wait_done'
        for n in names_:
            if 'ExpertPool::publish' in n:
                return 'ExpertPool::publish'
        for n in names_:
            if n.startswith('ggml_') or 'vnni' in n or 'rows<' in n:
                return 'ggml/vnni expert compute (host joins)'
        for n in names_:
            if 'Verifier::run' in n:
                return 'Verifier::run (other)'
        if names_:
            return 'strata other: ' + names_[0][:60]
        return 'non-strata (kernel/driver only)'
    Uoff_all = U([(a, b) for a, b, _, _, _ in off])
    by_reason = collections.defaultdict(list)
    for a, b, cpu, blk, cpu2 in off:
        by_reason[blk].append((a, b))
    Ur = {k: U(v) for k, v in by_reason.items()}
    cats = collections.defaultdict(lambda: collections.defaultdict(float))
    hs = collections.defaultdict(list)
    for sid, (st, tid, li, state) in keep.items():
        if tid == host:
            hs[li].append(sid)
    CLASSES = ['short', 'mid', 'long']
    acc = {c_: collections.defaultdict(float) for c_ in CLASSES}
    per_layer_rows = []
    offst = Uoff_all.st
    for li, (wi, i, Dst, Den, R, Dn) in enumerate(layers):
        p = R - Den
        c_ = cls(p)
        a_ = acc[c_]
        a_['n'] += 1
        a_['post_ns'] += p
        on_ns = Uon.cov(Den, R)
        a_['host_on_ns'] += on_ns
        a_['host_off_ns'] += p - on_ns
        io_ns = Uio.cov(Den, R)
        off_io = 0
        j0 = max(0, bisect.bisect_left(offst, Den) - 1)
        for x in Uoff_all.u[j0:]:
            if x[0] >= R:
                break
            if x[1] > Den:
                off_io += Uio.cov(max(x[0], Den), min(x[1], R))
        a_['host_off_io_ns'] += off_io
        a_['io_any_ns'] += io_ns
        a_['io_big_ns'] += Ubig.cov(Den, R)
        a_['io_hf_ns'] += Uhf.cov(Den, R)
        for blk, u_ in Ur.items():
            a_['off_reason_%s_ns' % blk] += u_.cov(Den, R)
        nb = [r for r in bigr if Den <= r[1] + SH < R]
        a_['big_reads'] += len(nb)
        a_['big_bytes'] += sum(r[3] for r in nb)
        if len(nb):
            a_['layers_with_big_read'] += 1
        sl = hs.get(li, [])
        if sl:
            w = on_ns / len(sl)
            for sid in sl:
                cats[c_][catof(stk.get(sid, []))] += w
        else:
            cats[c_]['(no host sample)'] += on_ns
        per_layer_rows.append((c_, p, on_ns, off_io, io_ns, len(nb), sum(r[3] for r in nb)))
    out = {}
    for c_ in CLASSES:
        a_ = acc[c_]
        out[c_] = {k: (v / 1e6 / nwin if k.endswith('_ns') else v) for k, v in a_.items()}
    res['class_accounting_ms_per_window_for_ns_keys'] = out
    res['host_on_categories_ms_per_window'] = {c_: {k: v / 1e6 / nwin for k, v in sorted(cats[c_].items(), key=lambda x: -x[1])[:14]} for c_ in CLASSES}
    lng = [r for r in per_layer_rows if r[0] == 'long']
    res['long_layers'] = {'n': len(lng), 'with_big_read_pct': 100 * sum(1 for r in lng if r[5] > 0) / len(lng),
                          'io_ge_50pct_of_post_pct': 100 * sum(1 for r in lng if r[4] >= 0.5 * r[1]) / len(lng),
                          'big_reads_per_layer_hist': sorted(collections.Counter(min(r[5], 8) for r in lng).items()),
                          'mean_MB': statistics.mean(r[6] for r in lng) / 1e6, 'mean_post_ms': statistics.mean(r[1] for r in lng) / 1e6,
                          'mean_io_over_post': sum(r[4] for r in lng) / sum(r[1] for r in lng)}
    xs = [r[6] / 1e6 for r in per_layer_rows]
    ys = [r[1] / 1e6 for r in per_layer_rows]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    bq = sxy / sxx
    res['regress_post_vs_MB'] = {'slope_ms_per_MB': bq, 'intercept_ms': my - bq * mx, 'implied_GBps': 1.0 / bq, 'corr': sxy / (sxx * syy) ** 0.5}
    nl = [r for r in per_layer_rows if r[5] == 0]
    res['no_read_layers'] = {'n': len(nl), 'long_among_them': sum(1 for r in nl if r[0] == 'long'),
                             'post_ms_per_window': sum(r[1] for r in nl) / 1e6 / nwin, 'long_post_ms_per_window': sum(r[1] for r in nl if r[0] == 'long') / 1e6 / nwin}
    wr = [r for r in per_layer_rows if r[5] > 0]
    res['read_layers'] = {'n': len(wr), 'post_ms_per_window': sum(r[1] for r in wr) / 1e6 / nwin, 'mean_post_ms': statistics.mean(r[1] for r in wr) / 1e6,
                          'by_nreads': {str(k): {'layers': sum(1 for r in wr if min(r[5], 6) == k),
                                                 'mean_post_ms': statistics.mean([r[1] for r in wr if min(r[5], 6) == k] or [0]) / 1e6} for k in range(1, 7)}}
    # ---------------- whole decode: host off-CPU by reason
    offw = [(max(a, T0), min(b, T1), blk, cpu) for a, b, cpu, blk, _ in off if b > T0 and a < T1]
    rs = collections.defaultdict(lambda: [0, 0.0])
    for a, b, blk, cpu in offw:
        rs[blk][0] += 1
        rs[blk][1] += b - a
    res['host_off_by_reason_decode'] = {str(k): {'events': v[0], 'ms_per_window': v[1] / 1e6 / nwin} for k, v in sorted(rs.items(), key=lambda x: -x[1][1])}
    offio = offtot = 0
    for a, b, blk, cpu in offw:
        offtot += b - a
        offio += Uio.cov(a, b)
    res['host_off_decode'] = {'total_ms_per_window': offtot / 1e6 / nwin, 'io_overlap_ms_per_window': offio / 1e6 / nwin, 'io_overlap_frac': offio / offtot,
                              'on_ms_per_window': Uon.cov(T0, T1) / 1e6 / nwin}
    cpus = collections.defaultdict(list)
    for a, b, blk, cpu in offw:
        if blk == 0 and b - a >= 20000 and Uio.cov(a, b) < 0.2 * (b - a):
            cpus[cpu].append((a, b))
    pre_by, pre_n = collections.Counter(), collections.Counter()
    pn = dict(c.execute('select globalPid,name from PROCESSES').fetchall())
    for cpu, lst in cpus.items():
        evs = c.execute('select start,globalTid from SCHED_EVENTS where cpu=? and isSchedIn=1 and start between ? and ? order by start', (cpu, T0, T1 + 10**8)).fetchall()
        sts = [e[0] for e in evs]
        for a, b in lst:
            j = bisect.bisect_left(sts, a)
            who = 'unknown'
            if j < len(evs) and evs[j][0] <= a + 50000:
                tid_ = evs[j][1]
                who = pn.get(tid_ & ~0xFFFFFF, 'pid?%x' % (tid_ & ~0xFFFFFF))
                if (tid_ & ~0xFFFFFF) == (gpid & ~0xFFFFFF):
                    who = 'strata.exe (other thread)'
            pre_by[who] += b - a
            pre_n[who] += 1
    res['host_preempted_not_io'] = {'events': sum(pre_n.values()), 'ms_per_window': sum(pre_by.values()) / 1e6 / nwin,
                                    'by_who_ms_per_window': {k: [pre_n[k], v / 1e6 / nwin] for k, v in pre_by.most_common(10)}}
    json.dump(res, open(OUTD + 'analysis5.json', 'w'), indent=1, default=str, ensure_ascii=False)
    print(json.dumps(res, indent=1, default=str, ensure_ascii=False)[:14000])
    print('stage2 done', time.time() - t0)


if __name__ == '__main__':
    {'stage1': stage1, 'stage2': stage2}[sys.argv[1]]()
