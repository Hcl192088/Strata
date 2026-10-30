"""PINAA confirmation queue (detached, 2026-10-28; copy of the NEXT4 queue, P4 dropped). One API stop window; the live S2K API is restored in finally and verified.
  P4 CHECK (patch4, CHUNK=8 and 16) -> mechanism probes (PIN8, PIN16, AA) -> A/B (S2K control + surviving arms), 5 rounds rotated.
usage: python next4_queue.py <out_root> <patch4_sha256|NONE>
The harness copies in .\\harness identify the live API by the S2K binary (385E...30F5); criteria were pre-registered in
state/EXPERIMENT_LEDGER.md (NEXT4 queue) and are not changed here.
"""
import json, os, re, subprocess, sys, threading, time
from pathlib import Path
import psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'harness'))
import replay_ab_20261027 as rp  # noqa: E402
ns = rp.ns
log = ns.log

NEW_BLOCK_CUTOFF_MIN = 160   # no new block after this (2h40m)
HARD_CAP_MIN = 180           # watchdog kills our own children after this so cleanup + restore always follow
ROUNDS = 8
PROBE_POINTS = ['p04', 'p05', 'p06']
ABOVE_NORMAL = getattr(psutil, 'ABOVE_NORMAL_PRIORITY_CLASS', None)
state = {}
ABORT = threading.Event()
PRIO = []
PRIO_FAIL = threading.Event()

S2K_EXE = 'C:/Users/User/Strata-Adrian-control/runs/miss-overlap-20261027/build/strata.exe'
S2K_SHA = '385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5'
P4_EXE = 'C:/Users/User/Strata-Adrian-control/runs/patch4-20261028/build/strata.exe'
SERVE = 'C:/Users/User/Strata-Adrian/runs/iq3-campaign-020/upstream-v0142'
S2K_ENV = {'STRATA_MISS_OVERLAP': '1', 'STRATA_MISS_OVERLAP_SPIN_US': '2000'}


def mk(exe, sha, env=None, args=None, **kw):
    d = dict(exe=exe, sha=sha, serve_dir=SERVE, env=dict(S2K_ENV, **(env or {})), args=args or {}, strict_capacity=True)
    d.update(kw)
    return d


def make_specs(p4sha):
    s = {
        'S2K': mk(S2K_EXE, S2K_SHA),
        'PIN8': mk(S2K_EXE, S2K_SHA, {'STRATA_PARTIAL_PIN': '1', 'STRATA_PARTIAL_PIN_GIB': '8'}, pin_capacity=True),
        'PIN6': mk(S2K_EXE, S2K_SHA, {'STRATA_PARTIAL_PIN': '1', 'STRATA_PARTIAL_PIN_GIB': '6'}, pin_capacity=True),
        'AA': mk(S2K_EXE, S2K_SHA, args={'--adapt-async': '1'}),
        'PA': mk(S2K_EXE, S2K_SHA, {'STRATA_PARTIAL_PIN': '1', 'STRATA_PARTIAL_PIN_GIB': '8'}, args={'--adapt-async': '1'}, pin_capacity=True),
    }
    if p4sha:
        s['P4CHK8'] = mk(P4_EXE, p4sha, {'STRATA_MISS_OVERLAP_CHECK': '1', 'STRATA_MISS_CHUNK': '8'})
        s['P4CHK16'] = mk(P4_EXE, p4sha, {'STRATA_MISS_OVERLAP_CHECK': '1', 'STRATA_MISS_CHUNK': '16'})
        s['P4_8'] = mk(P4_EXE, p4sha, {'STRATA_MISS_CHUNK': '8'})
        s['P4_16'] = mk(P4_EXE, p4sha, {'STRATA_MISS_CHUNK': '16'})
    return s


# capacity: PIN arms register part of the arena, so "locked" shrinks by exactly what is registered (locked + registered = 20 GiB)
_cap_orig = rp.capacity_ok


def capacity_ok2(arm, spec, facts):
    if not spec.get('pin_capacity'):
        return _cap_orig(arm, spec, facts)
    probs = []
    if str(facts.get('slots')) != '3153':
        probs.append('slots %r' % facts.get('slots'))
    if facts.get('ram_budget_gib') != ns.EXPECT_RAM:
        probs.append('RAM budget %r' % facts.get('ram_budget_gib'))
    try:
        reg = float(facts.get('registered_gib') or 0)
        lk = int(facts.get('locked_mib'))
    except (TypeError, ValueError):
        return False, 'no registered/locked evidence', True
    total = lk + reg * 1024
    facts['pin_total_mib'] = round(total, 1)
    if reg <= 0:
        probs.append('nothing registered')
    if abs(total - 20479.5) > 12:
        probs.append('locked %d + registered %.2f GiB = %.0f MiB != 20.00 GiB' % (lk, reg, total))
    return not probs, '; '.join(probs) + ('' if probs else ' (pin arm: locked %d + registered %.2f GiB = %.0f MiB)' % (lk, reg, total)), True


rp.capacity_ok = capacity_ok2


def save(root):
    (root / 'queue_state.json').write_text(json.dumps(state, indent=2, default=str))


def watchdog(t0):
    while True:
        time.sleep(20)
        if (time.time() - t0) / 60 > HARD_CAP_MIN:
            ABORT.set()
            log('WATCHDOG: hard cap %d min reached; killing own child processes' % HARD_CAP_MIN)
            try:
                for c in psutil.Process().children(recursive=True):
                    try:
                        c.kill()
                    except psutil.Error:
                        pass
            except psutil.Error:
                pass


def prio_watcher():
    seen = {}
    while True:
        time.sleep(2)
        try:
            now = time.time()
            for p in psutil.process_iter(['pid', 'name']):
                if (p.info['name'] or '').lower() != 'strata.exe':
                    continue
                pid = p.info['pid']
                first = seen.setdefault(pid, now)
                ent = next((e for e in PRIO if e['pid'] == pid), None)
                try:
                    if ent is None and now - first >= 10:
                        cls = p.nice()
                        ent = dict(pid=pid, at=now, first_class=str(cls), set_by_queue=False, set_ok=None, readings=[])
                        if cls != ABOVE_NORMAL:
                            ent['set_by_queue'] = True
                            try:
                                p.nice(ABOVE_NORMAL)
                                ent['set_ok'] = (p.nice() == ABOVE_NORMAL)
                            except psutil.Error as e:
                                ent['set_ok'] = False
                                ent['set_error'] = repr(e)
                            if not ent['set_ok']:
                                PRIO_FAIL.set()
                        PRIO.append(ent)
                    if ent is not None and (not ent['readings'] or now - ent['readings'][-1][0] >= 60):
                        ent['readings'].append((now, str(p.nice())))
                except psutil.Error:
                    pass
        except Exception:  # noqa
            pass


def block_text(d):
    f = d / 'engine.log'
    return f.read_text(encoding='utf-8', errors='replace') if f.exists() else ''


def run_one(root, idx, rnd, label, spec, tokens, points=None):
    old = rp.POINTS
    if points:
        rp.POINTS = points
    try:
        t_blk = time.time()
        meta, rows = rp.run_block(root, idx, rnd, label, spec, tokens)
    finally:
        rp.POINTS = old
    meta['engine_priority'] = [e for e in PRIO if e['at'] >= t_blk]
    if meta['status'] == 'PROCESS_GATE':
        raise RuntimeError('process gate tripped; abort (restore follows)')
    if PRIO_FAIL.is_set():
        raise RuntimeError('engine priority could not be set to AboveNormal; abort (restore follows)')
    return meta, rows


def blockdir(root, idx, rnd, label):
    return root / ('block-%02d-%s-r%d' % (idx, label, rnd))


def gate_p4(d, chunk):
    text = block_text(d)
    bad = [l for l in text.splitlines() if 'MISS_OVERLAP_CHECK MISMATCH' in l]
    prog = [l for l in text.splitlines() if l.startswith('MISS_OVERLAP progress')]
    last = prog[-1] if prog else ''
    g = lambda k: (lambda m: int(m.group(1)) if m else None)(re.search(k + r'=(\d+)', last))
    info = dict(mismatch_lines=len(bad), last_progress=last, split_calls=g('split_calls'), check_rows=g('check_rows'),
                check_bad=g('check_mismatch_rows'), chunks_published=g('chunks_published'),
                chunk_wait_ms=(lambda m: float(m.group(1)) if m else None)(re.search(r'chunk_wait_ms=([\d.]+)', last)),
                chunk_line=(re.search(r'(MISS_OVERLAP chunked completion on[^\n]*)', text) or [None, None])[1])
    ok = (not bad and info['check_bad'] == 0 and (info['split_calls'] or 0) >= 20 and (info['check_rows'] or 0) >= 100
          and (info['chunks_published'] or 0) > 0 and info['chunk_line'] is not None and ('CHUNK=%d' % chunk) in info['chunk_line'])
    info['ok'] = ok
    (d / 'gate_p4.json').write_text(json.dumps(info, indent=1))
    log('P4 CHECK gate chunk=%d: %s' % (chunk, json.dumps(info)))
    return info


def gate_pin(d, meta, rows):
    text = block_text(d)
    facts = ns.startup_facts(text)
    reg = float(facts.get('registered_gib') or 0)
    pcie = [r.get('pcie_per_layer_window') for r in rows if r.get('pcie_per_layer_window') is not None]
    info = dict(status=meta['status'], registered_gib=reg, page_lock_refused=facts.get('page_lock_refused'),
                pcie_per_layer_window=pcie, capacity=meta.get('startup', {}).get('capacity_detail'),
                startup_line=(re.search(r'(FileExpertSource: locked resident cache[^\n]*)', text) or [None, None])[1])
    info['ok'] = meta['status'] == 'OK' and reg > 0 and any((x or 0) > 0 for x in pcie)
    (d / 'gate_pin.json').write_text(json.dumps(info, indent=1))
    log('PIN gate: ' + json.dumps(info))
    return info


def gate_aa(d, meta, rows):
    text = block_text(d)
    facts = ns.startup_facts(text)
    ex = re.findall(r'(\d+) exchanged with the VRAM tier', text)
    info = dict(status=meta['status'], async_on_line=facts.get('async_on_line'), async_off_line=facts.get('async_off_line'),
                exchanged_last=int(ex[-1]) if ex else None,
                exchange_pinned_ok=facts.get('async_off_line') is None and facts.get('async_on_line') is not None)
    info['ok'] = (meta['status'] == 'OK' and facts.get('async_on_line') is not None and facts.get('async_off_line') is None
                  and (info['exchanged_last'] or 0) > 0)
    (d / 'gate_aa.json').write_text(json.dumps(info, indent=1))
    log('AA gate: ' + json.dumps(info))
    return info


def rotated(arms, rounds):
    seq = []
    for r in range(rounds):
        k = r % len(arms)
        seq += [(r + 1, a) for a in arms[k:] + arms[:k]]
    return seq


def final_verify(root):
    """After restore: running engine SHA, /health, and the capacity lines of the freshly started live engine."""
    out = {}
    try:
        out['health'] = ns.http_json('/health', 8)
    except Exception as e:  # noqa
        out['health_error'] = repr(e)
    try:
        m = ns.http_json('/metrics', 8)
        out['metrics'] = {k: m['engine'].get(k) for k in ('expert_slots', 'arena_mib', 'pool_workers', 'pcie_frac')}
    except Exception as e:  # noqa
        out['metrics_error'] = repr(e)
    try:
        engs = [p for p in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'create_time']) if (p.info['name'] or '').lower() == 'strata.exe']
        out['engines'] = [dict(pid=p.info['pid'], exe=p.info['exe'], sha=ns.sha(p.info['exe']), serve='--serve' in (p.info['cmdline'] or [])) for p in engs]
    except Exception as e:  # noqa
        out['engine_error'] = repr(e)
    try:
        logp = Path(json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))['log'])
        text = logp.read_text(encoding='utf-8', errors='replace')
        seg = text[text.rfind('engine started:'):]
        f = ns.startup_facts(seg)
        out['live_log'] = {k: f.get(k) for k in ('slots', 'ram_budget_gib', 'locked_mib')}
        out['live_log_started_line'] = seg.splitlines()[0][:120]
        out['miss_overlap_progress_seen'] = 'MISS_OVERLAP' in seg
    except Exception as e:  # noqa
        out['live_log_error'] = repr(e)
    h = out.get('health') or {}
    lg = out.get('live_log') or {}
    out['verified'] = bool(h.get('loaded') and str(lg.get('slots')) == '3153' and lg.get('ram_budget_gib') == '20.00'
                           and lg.get('locked_mib') == '20479' and any(e.get('sha') == S2K_SHA and e.get('serve') for e in out.get('engines', [])))
    (root / 'final_verify.json').write_text(json.dumps(out, indent=2, default=str))
    log('FINAL VERIFY: ' + json.dumps(out, default=str))
    return out


def main():
    root = Path(sys.argv[1])
    p4sha = sys.argv[2].upper() if len(sys.argv) > 2 and sys.argv[2].upper() != 'NONE' else None
    root.mkdir(exist_ok=False)
    ns.log.path = root / 'orchestrator.log'
    assert os.environ.get('COMPUTERNAME', '').upper() == ns.HOSTNAME
    assert ns.sha(ns.EXE_C) == ns.EXE_C_SHA == S2K_SHA, 'S2K SHA mismatch'
    assert ns.sha(ns.CONFIG) == ns.CONFIG_SHA, 'live S2K config changed'
    cfg0 = json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
    assert cfg0['env'].get('STRATA_MISS_OVERLAP') == '1' and cfg0['env'].get('STRATA_MISS_OVERLAP_SPIN_US') == '2000'
    if p4sha:
        assert ns.sha(Path(P4_EXE)) == p4sha, 'patch4 SHA mismatch'
    specs = make_specs(p4sha)
    (root / 'arms.json').write_text(json.dumps(specs, indent=1))
    blocks_all, rows_all = [], []
    verdicts = {}
    stopped = False
    restored = None
    t_start = time.time()
    state['patch4_sha'] = p4sha
    threading.Thread(target=watchdog, args=(t_start,), daemon=True).start()
    threading.Thread(target=prio_watcher, daemon=True).start()
    idx = 0
    try:
        stopped = True
        state['api_was_running'] = ns.stop_api(root)
        state['api_stopped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        ns.ram_start_gate(root)
        t_start = time.time()
        save(root)

        def cutoff(tag):
            if ABORT.is_set() or (time.time() - t_start) / 60 > NEW_BLOCK_CUTOFF_MIN:
                log('%s: cutoff reached, skipping' % tag)
                state.setdefault('cutoff_hit', []).append(tag)
                return True
            return False

        def record(meta):
            blocks_all.append(meta)
            (root / 'blocks.json').write_text(json.dumps(blocks_all, indent=1, default=str))

        # ---- a. P4 CHECK
        for chunk in (8, 16):
            name = 'P4CHK%d' % chunk
            arm = 'P4_%d' % chunk
            if name not in specs:
                verdicts[arm] = 'DROPPED: no patch4 binary (build failed)'
                continue
            if cutoff(name):
                break
            idx += 1
            meta, _ = run_one(root, idx, 0, name, specs[name], 128)
            record(meta)
            info = gate_p4(blockdir(root, idx, 0, name), chunk) if meta['status'] == 'OK' else dict(ok=False, status=meta['status'])
            state['check_%d' % chunk] = info
            if not info['ok']:
                verdicts[arm] = 'DROPPED: CHECK gate failed (%s)' % json.dumps(info, default=str)[:300]
            save(root)
        # ---- b. mechanism probes
        for name, gate in (('PIN6', gate_pin), ('PA', lambda d, m, r: (lambda a, b: dict(ok=bool(a.get('ok')) and bool(b.get('ok')), pin=a, aa=b))(gate_pin(d, m, r), gate_aa(d, m, r)))):
            if cutoff('probe-' + name):
                break
            idx += 1
            label = name + 'probe'
            meta, rows = run_one(root, idx, 0, label, specs[name], 128, PROBE_POINTS)
            record(meta)
            d = blockdir(root, idx, 0, label)
            info = gate(d, meta, rows)
            state['probe_' + name] = info
            if not info['ok']:
                verdicts[name] = 'NOT_APPLICABLE: probe gate not met (%s)' % json.dumps(info, default=str)[:400]
            save(root)
        arms = [a for a in ('S2K', 'PIN8', 'PIN6', 'AA', 'PA') if a not in verdicts]
        state['verdicts_pre'] = verdicts
        state['ab_arms'] = arms
        save(root)
        # ---- c. A/B
        if len(arms) >= 2:
            seq = rotated(arms, ROUNDS)
            log('A/B arms %s; order: %s' % (arms, ' | '.join('r%d:%s' % s for s in seq)))
            state['ab_order'] = seq
            for rnd, arm in seq:
                if cutoff('AB'):
                    break
                idx += 1
                meta, rows = run_one(root, idx, rnd, arm, specs[arm], 512)
                record(meta)
                rows_all.extend(rows)
                (root / 'rows-AB.json').write_text(json.dumps(rows_all, indent=1))
                if meta['status'] != 'OK':
                    state.setdefault('bad_blocks', []).append((idx, arm, rnd, meta['status']))
                save(root)
    except BaseException as e:  # noqa
        log('QUEUE ABORTED: %r' % (e,))
        state['abort'] = repr(e)
        raise
    finally:
        log('finally: restoring API')
        try:
            healthy = bool(ns.http_json('/health', 5).get('loaded')) and bool(ns.api_pids())
        except Exception:  # noqa
            healthy = False
        restored = ns.restore_api(root) if (stopped or not healthy) else dict(restored=True, note='never stopped')
        state['restored'] = restored
        try:
            time.sleep(5)
            state['final_verify'] = final_verify(root)
        except Exception as e:  # noqa
            state['final_verify'] = dict(error=repr(e))
        state['finished'] = time.strftime('%Y-%m-%d %H:%M:%S')
        state['elapsed_min'] = round((time.time() - t_start) / 60, 1)
        save(root)
        (root / 'DONE.json').write_text(json.dumps(dict(finished=state['finished'], api_restored=restored.get('restored'),
                                                        verified=(state.get('final_verify') or {}).get('verified'),
                                                        verdicts_pre=verdicts,
                                                        blocks=[(b['block'], b['arm'], b['status']) for b in blocks_all]), indent=2, default=str))
    return 0 if restored.get('restored') else 2


if __name__ == '__main__':
    import signal
    for s in (signal.SIGTERM, getattr(signal, 'SIGBREAK', signal.SIGTERM)):
        signal.signal(s, lambda *_: (_ for _ in ()).throw(SystemExit(3)))
    sys.exit(main())
