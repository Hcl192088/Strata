"""IQ3S_MT1_AB queue (detached, 2026-10-28; adapted from the PINAA queue). One API stop window; the live S2K API is restored in finally and verified.
  mechanism probe (MT1, 3 points x 128 tokens) -> A/B: S2K / MT1 (STRATA_IQ3S_MT1=1) / S2KB (A/A copy), 10 rounds rotated, 10 Hermes points x 512 tokens greedy.
usage: python iq3s_queue.py <out_root>
Verdict rule pre-registered in state/EXPERIMENT_LEDGER.md (IQ3S_MT1_AB); not changed here.
"""
import json, os, re, subprocess, sys, threading, time
from pathlib import Path
import psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'harness'))
import replay_ab_20261027 as rp  # noqa: E402
ns = rp.ns
log = ns.log

NEW_BLOCK_CUTOFF_MIN = 150   # no new block after this
HARD_CAP_MIN = 175           # watchdog kills our own children after this so cleanup + restore always follow
ROUNDS = 10
PROBE_POINTS = ['p04', 'p05', 'p06']
ABOVE_NORMAL = getattr(psutil, 'ABOVE_NORMAL_PRIORITY_CLASS', None)
state = {}
ABORT = threading.Event()
PRIO = []
PRIO_FAIL = threading.Event()

S2K_EXE = 'C:/Users/User/Strata-Adrian-control/runs/miss-overlap-20261027/build/strata.exe'
S2K_SHA = '385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5'
SERVE = 'C:/Users/User/Strata-Adrian/runs/iq3-campaign-020/upstream-v0142'
S2K_ENV = {'STRATA_MISS_OVERLAP': '1', 'STRATA_MISS_OVERLAP_SPIN_US': '2000'}


def mk(exe, sha, env=None, args=None, **kw):
    d = dict(exe=exe, sha=sha, serve_dir=SERVE, env=dict(S2K_ENV, **(env or {})), args=args or {}, strict_capacity=True)
    d.update(kw)
    return d


def make_specs():
    return {
        'S2K': mk(S2K_EXE, S2K_SHA),
        'MT1': mk(S2K_EXE, S2K_SHA, {'STRATA_IQ3S_MT1': '1'}),
        'S2KB': mk(S2K_EXE, S2K_SHA),
    }


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
                        try:
                            ev = p.environ()
                            ent['env'] = {k: v for k, v in ev.items() if k.upper().startswith('STRATA_')}
                        except Exception as e:  # noqa
                            ent['env_error'] = repr(e)
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


def gate_mt1(d, meta, rows):
    """Mechanism gate: engine env really has STRATA_IQ3S_MT1=1 (and not STRATA_IQ_MT_MIN), capacity strict; record any kernel/ISA lines."""
    text = block_text(d)
    cmdj = json.loads((d / 'command.json').read_text())
    cfg_env = cmdj.get('engine_env') or {}
    ents = meta.get('engine_priority') or []
    live_env = [e.get('env') for e in ents if e.get('env') is not None]
    kern = [l.strip()[:220] for l in text.splitlines() if re.search(r'iq256|iq3|gather|vnni|avx|kernel|isa\b|simd|cpu feature', l, re.I)]
    info = dict(status=meta['status'], config_env_has_mt1=cfg_env.get('STRATA_IQ3S_MT1') == '1', config_env_has_mt_min=('STRATA_IQ_MT_MIN' in cfg_env),
                live_process_env=live_env, live_env_errors=[e.get('env_error') for e in ents if e.get('env_error')],
                capacity=meta.get('startup', {}).get('capacity_detail'),
                capacity_ok=meta.get('startup', {}).get('capacity_ok'), kernel_isa_lines=kern[:40],
                tok_s=[r.get('m_decode_tok_s') for r in rows])
    env_ok = all(e.get('STRATA_IQ3S_MT1') == '1' and 'STRATA_IQ_MT_MIN' not in e for e in live_env) if live_env else None
    info['live_env_ok'] = env_ok
    info['ok'] = (meta['status'] == 'OK' and info['config_env_has_mt1'] and not info['config_env_has_mt_min']
                  and bool(info['capacity_ok']) and env_ok is not False)
    (d / 'gate_mt1.json').write_text(json.dumps(info, indent=1))
    log('MT1 gate: ' + json.dumps(info))
    return info


def rotated(arms, rounds):
    seq = []
    for r in range(rounds):
        k = r % len(arms)
        seq += [(r + 1, a) for a in arms[k:] + arms[:k]]
    return seq


def _cmdline(p):
    try:
        cl = p.cmdline()
        if cl:
            return cl
    except Exception:  # noqa
        pass
    try:
        r = ns.ps("(Get-CimInstance Win32_Process -Filter 'ProcessId=%d').CommandLine" % p.pid, check=False)
        return r.stdout.strip().split() if r.stdout.strip() else []
    except Exception:  # noqa
        return []


def final_verify_once():
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
    engs = []
    try:
        for p in psutil.process_iter(['pid', 'name']):
            if (p.info['name'] or '').lower() != 'strata.exe':
                continue
            e = dict(pid=p.pid)
            try:
                e['exe'] = p.exe()
                e['sha'] = ns.sha(e['exe'])
            except Exception as ex:  # noqa
                e['exe_error'] = repr(ex)
            cl = _cmdline(p)
            e['serve'] = any(c == '--serve' for c in cl)
            e['cmdline_head'] = ' '.join(cl)[:160]
            try:
                e['priority'] = str(p.nice())
                e['above_normal'] = (p.nice() == ABOVE_NORMAL)
            except Exception as ex:  # noqa
                e['priority_error'] = repr(ex)
            try:
                ev = p.environ()
                e['env'] = {k: ev.get(k) for k in ('STRATA_MISS_OVERLAP', 'STRATA_MISS_OVERLAP_SPIN_US', 'STRATA_IQ3S_MT1', 'STRATA_IQ_MT_MIN')}
            except Exception as ex:  # noqa
                e['env_error'] = repr(ex)
            engs.append(e)
    except Exception as e:  # noqa
        out['engine_error'] = repr(e)
    out['engines'] = engs
    try:
        logp = Path(json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))['log'])
        text = logp.read_text(encoding='utf-8', errors='replace')
        seg = text[text.rfind('engine started:'):]
        f = ns.startup_facts(seg)
        out['live_log'] = {k: f.get(k) for k in ('slots', 'ram_budget_gib', 'locked_mib')}
        out['live_log_started_line'] = seg.splitlines()[0][:120]
    except Exception as e:  # noqa
        out['live_log_error'] = repr(e)
    h = out.get('health') or {}
    lg = out.get('live_log') or {}
    good = [e for e in engs if e.get('sha') == S2K_SHA and e.get('serve') and e.get('above_normal')
            and (e.get('env') or {}).get('STRATA_MISS_OVERLAP') == '1' and (e.get('env') or {}).get('STRATA_MISS_OVERLAP_SPIN_US') == '2000'
            and not (e.get('env') or {}).get('STRATA_IQ3S_MT1') and not (e.get('env') or {}).get('STRATA_IQ_MT_MIN')]
    out['checks'] = dict(loaded=bool(h.get('loaded')), slots=str(lg.get('slots')) == '3153', ram=lg.get('ram_budget_gib') == '20.00',
                         locked=lg.get('locked_mib') == '20479', one_good_engine=(len(good) == 1 and len(engs) == 1))
    out['verified'] = all(out['checks'].values())
    return out


def final_verify(root):
    """After restore: loaded, SHA + --serve, AboveNormal, capacity lines, live env. Retries up to 4x (engine may still be settling)."""
    out = {}
    for i in range(4):
        out = final_verify_once()
        out['attempt'] = i + 1
        if out.get('verified'):
            break
        time.sleep(15)
    (root / 'final_verify.json').write_text(json.dumps(out, indent=2, default=str))
    log('FINAL VERIFY: ' + json.dumps(out, default=str))
    return out


def main():
    root = Path(sys.argv[1])
    root.mkdir(exist_ok=False)
    ns.log.path = root / 'orchestrator.log'
    assert os.environ.get('COMPUTERNAME', '').upper() == ns.HOSTNAME
    assert ns.sha(ns.EXE_C) == ns.EXE_C_SHA == S2K_SHA, 'S2K SHA mismatch'
    assert ns.sha(ns.CONFIG) == ns.CONFIG_SHA, 'live S2K config changed'
    cfg0 = json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
    assert cfg0['env'].get('STRATA_MISS_OVERLAP') == '1' and cfg0['env'].get('STRATA_MISS_OVERLAP_SPIN_US') == '2000'
    specs = make_specs()
    assert 'STRATA_IQ_MT_MIN' not in specs['MT1']['env'] and 'STRATA_IQ_MT_MIN' not in cfg0['env']
    (root / 'arms.json').write_text(json.dumps(specs, indent=1))
    blocks_all, rows_all = [], []
    stopped = False
    restored = None
    t_start = time.time()
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

        # ---- a. mechanism probe (MT1)
        idx += 1
        meta, rows = run_one(root, idx, 0, 'MT1probe', specs['MT1'], 128, PROBE_POINTS)
        record(meta)
        info = gate_mt1(blockdir(root, idx, 0, 'MT1probe'), meta, rows)
        state['probe_MT1'] = info
        save(root)
        if not info['ok']:
            raise RuntimeError('MT1 mechanism gate failed: %s' % json.dumps(info, default=str)[:600])
        # ---- b. A/B
        arms = ['S2K', 'MT1', 'S2KB']
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
                                                        blocks=[(b['block'], b['arm'], b['status']) for b in blocks_all]), indent=2, default=str))
    return 0 if restored.get('restored') else 2


if __name__ == '__main__':
    import signal
    for s in (signal.SIGTERM, getattr(signal, 'SIGBREAK', signal.SIGTERM)):
        signal.signal(s, lambda *_: (_ for _ in ()).throw(SystemExit(3)))
    sys.exit(main())
