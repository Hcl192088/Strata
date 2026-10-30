"""POOL_WORKER_SKEW diagnostic queue (detached, 2026-10-28). One API stop window; the live S2K API is ALWAYS restored in finally and verified.
Runs the instrumented diagnostic binary (runs\\worker-skew-20261028\\build\\strata.exe, built from a COPY of the S2K source + timing only)
with the S2K env on the neuro prompt, 1024 tokens, one GEN per fresh engine (the pool-split-r3 protocol), engines AboveNormal:
  ON1, ON2  : STRATA_WSKEW=1 (per-worker timing)
  MIC       : STRATA_WSKEW=1 + STRATA_WSKEW_MICRO=1 (adds a single-thread kernel microbenchmark on the host thread)
  OFF       : instrumentation compiled in but env off (overhead / sanity reference)
usage: python wskew_queue.py <out_root> <diag_sha256>
Criteria were pre-registered in state/EXPERIMENT_LEDGER.md (POOL_WORKER_SKEW) and are not changed here."""
import json, os, re, subprocess, sys, threading, time
from pathlib import Path
import psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'harness'))
import next_steps_ab_20261018 as ns  # noqa: E402

log = ns.log
HARD_CAP_MIN = 45
BLOCK_CAP_S = 8 * 60
ABOVE_NORMAL = psutil.ABOVE_NORMAL_PRIORITY_CLASS
S2K_SHA = '385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5'
DIAG_EXE = Path(r'C:\Users\User\Strata-Adrian-control\runs\worker-skew-20261028\build\strata.exe')
state = {}
ABORT = threading.Event()
RUNS = [('ON1', {'STRATA_WSKEW': '1'}), ('ON2', {'STRATA_WSKEW': '1'}),
        ('MIC', {'STRATA_WSKEW': '1', 'STRATA_WSKEW_MICRO': '1'}), ('OFF', {})]


def save(root):
    (root / 'queue_state.json').write_text(json.dumps(state, indent=2, default=str))


def watchdog(t0):
    while True:
        time.sleep(20)
        if (time.time() - t0) / 60 > HARD_CAP_MIN:
            ABORT.set()
            log('WATCHDOG: hard cap %d min; killing own child processes' % HARD_CAP_MIN)
            try:
                for c in psutil.Process().children(recursive=True):
                    try:
                        c.kill()
                    except psutil.Error:
                        pass
            except psutil.Error:
                pass


def run_one(root, name, extra_env, prompt, cfg, diag_sha):
    d = root / ('run-' + name)
    d.mkdir()
    meta = dict(name=name, status='STARTED', binary=str(DIAG_EXE), binary_sha256=diag_sha)
    args = ['--serve'] + list(cfg['args'])
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('STRATA_')}
    cenv = dict(cfg['env'])
    cenv['STRATA_ROUTE_TAIL_SKIP'] = '7'        # as ns.build_command / serve do
    env.update(cenv)
    out_file = d / 'wskew.json'
    env.update(extra_env)
    if extra_env.get('STRATA_WSKEW') == '1':
        env['STRATA_WSKEW_OUT'] = str(out_file)
    assert 'STRATA_VERIFY_PROFILE' not in env
    if ns.engines():
        raise RuntimeError('strata.exe already running: %r' % ns.engines())
    left = ns.processes()
    if left:
        raise RuntimeError('process gate before run: %s' % json.dumps(left))
    ns.log_heavy('%s pre-run' % name, d / 'heavy-processes.json')
    meta['env'] = {k: v for k, v in env.items() if k.startswith('STRATA_')}
    (d / 'command.json').write_text(json.dumps(dict(exe=str(DIAG_EXE), sha=diag_sha, args=args, env=meta['env'], prompt_sha256=ns.PROMPT_SHA), indent=2))
    err_path = d / 'stderr.log'
    tokens, done, p, timer = [], None, None, None
    ready = False
    try:
        with err_path.open('w', encoding='utf-8') as err, (d / 'stdout.log').open('w', encoding='utf-8') as out:
            p = subprocess.Popen([str(DIAG_EXE)] + args, env=env, cwd=str(DIAG_EXE.parent), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=err, text=True, encoding='utf-8',
                                 creationflags=subprocess.CREATE_NO_WINDOW | subprocess.ABOVE_NORMAL_PRIORITY_CLASS)
            timer = threading.Timer(BLOCK_CAP_S, lambda: p.poll() is None and p.kill())
            timer.start()
            next_gate = 0.0
            for line in p.stdout:
                out.write(line)
                out.flush()
                if time.monotonic() >= next_gate:
                    other = [x for x in ns.processes() if x['pid'] != p.pid]
                    (d / 'live-process-gate.json').write_text(json.dumps(dict(owned_pid=p.pid, processes=other), indent=2))
                    if other:
                        raise RuntimeError('live process gate: ' + json.dumps(other))
                    next_gate = time.monotonic() + 5
                if line.startswith('READY'):
                    text = err_path.read_text(encoding='utf-8', errors='replace')
                    facts = ns.startup_facts(text)
                    ok, why = ns.capacity_verdict('C', facts)
                    facts.update(capacity_ok=ok, capacity_detail=why)
                    (d / 'startup.json').write_text(json.dumps(facts, indent=2))
                    meta['startup'] = facts
                    try:
                        meta['priority_class'] = str(psutil.Process(p.pid).nice())
                        meta['priority_ok'] = psutil.Process(p.pid).nice() == ABOVE_NORMAL
                    except psutil.Error as e:
                        meta['priority_class'] = repr(e)
                        meta['priority_ok'] = False
                    log('%s READY %s prio=%s' % (name, json.dumps({k: facts[k] for k in ('slots', 'ram_budget_gib', 'locked_mib', 'pool_line')}), meta.get('priority_class')))
                    if not ok or not meta['priority_ok']:
                        meta['status'] = 'ENV_BLOCKED'
                        meta['detail'] = why if not ok else 'engine priority %s' % meta.get('priority_class')
                        p.stdin.write('QUIT\n')
                        p.stdin.flush()
                        break
                    ready = True
                    p.stdin.write('GEN 1024 %s\n' % prompt)
                    p.stdin.flush()
                elif line.startswith('T '):
                    tokens.append(int(line.split()[1]))
                elif line.startswith('DONE '):
                    done = line.strip()
                    tail = ''
                    for _ in range(20):
                        time.sleep(0.5)
                        tail = err_path.read_text(encoding='utf-8', errors='replace')
                        if 'generated in' in tail and 'decode timing' in tail:
                            break
                    meta.update(ns.parse_done(line))
                    meta['request'] = ns.parse_request(tail)
                    p.stdin.write('QUIT\n')
                    p.stdin.flush()
                    break
                elif line.startswith('ERR '):
                    raise RuntimeError(line.strip())
            if meta['status'] == 'STARTED':
                meta['status'] = 'OK' if done else ('NO_READY' if not ready else 'INCOMPLETE')
            try:
                p.stdin.close()
            except OSError:
                pass
            for line in p.stdout:
                out.write(line)
            meta['exit_code'] = p.wait(timeout=90)
    except Exception as e:  # noqa
        meta['status'] = 'NO_READY' if not ready else 'INCOMPLETE'
        meta['error'] = repr(e)
        log('%s error: %r' % (name, e))
        if isinstance(e, RuntimeError) and str(e).startswith('live process gate'):
            meta['status'] = 'PROCESS_GATE'
    finally:
        if timer:
            timer.cancel()
        if p is not None and p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=60)
            except Exception:  # noqa
                p.kill()
    for _ in range(40):
        if not ns.engines():
            break
        time.sleep(1)
    if ns.engines():
        raise RuntimeError('engine left behind after run: %r' % ns.engines())
    (d / 'tokens.json').write_text(json.dumps(tokens))
    meta['output_tokens'] = len(tokens)
    meta['token_sha256'] = ns.sha(d / 'tokens.json')
    meta['wskew_file'] = out_file.exists()
    if meta['wskew_file']:
        meta['wskew_bytes'] = out_file.stat().st_size
    (d / 'meta.json').write_text(json.dumps(meta, indent=2, default=str))
    log('%s done: %s' % (name, json.dumps({k: meta.get(k) for k in ('status', 'done', 'output_tokens', 'wskew_file', 'exit_code')})))
    time.sleep(3)
    return meta


def final_verify(root):
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
    for p in psutil.process_iter(['pid', 'name']):
        if (p.info['name'] or '').lower() != 'strata.exe':
            continue
        e = dict(pid=p.info['pid'])
        try:
            e['exe'] = p.exe()
            e['sha'] = ns.sha(e['exe'])
            e['serve'] = '--serve' in p.cmdline()
            e['priority'] = str(p.nice())
            e['env_miss_overlap'] = [x for x in p.environ().items() if x[0].startswith('STRATA_MISS_OVERLAP')]
        except Exception as ex:  # noqa
            e['error'] = repr(ex)
        engs.append(e)
    out['engines'] = engs
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
                           and lg.get('locked_mib') == '20479' and any(e.get('sha') == S2K_SHA and e.get('serve') for e in engs))
    (root / 'final_verify.json').write_text(json.dumps(out, indent=2, default=str))
    log('FINAL VERIFY: ' + json.dumps(out, default=str))
    return out


def main():
    root = Path(sys.argv[1])
    diag_sha = sys.argv[2].upper()
    root.mkdir(exist_ok=False)
    ns.log.path = root / 'orchestrator.log'
    assert os.environ.get('COMPUTERNAME', '').upper() == ns.HOSTNAME
    assert ns.sha(ns.EXE_C) == ns.EXE_C_SHA == S2K_SHA, 'S2K SHA mismatch'
    assert ns.sha(ns.CONFIG) == ns.CONFIG_SHA, 'live S2K config changed'
    assert ns.sha(DIAG_EXE) == diag_sha, 'diagnostic binary SHA mismatch'
    cfg = json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
    assert cfg['env'].get('STRATA_MISS_OVERLAP') == '1' and cfg['env'].get('STRATA_MISS_OVERLAP_SPIN_US') == '2000'
    prompt = ns.PROMPT.read_text(encoding='utf-8-sig').strip()
    assert ns.sha(ns.PROMPT) == ns.PROMPT_SHA
    metas, stopped, restored = [], False, None
    t_start = time.time()
    state['diag_sha'] = diag_sha
    threading.Thread(target=watchdog, args=(t_start,), daemon=True).start()
    try:
        stopped = True
        state['api_was_running'] = ns.stop_api(root)
        state['api_stopped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        ns.ram_start_gate(root)
        t_start = time.time()
        save(root)
        for name, extra in RUNS:
            if ABORT.is_set() or (time.time() - t_start) / 60 > HARD_CAP_MIN - 8:
                log('%s: cutoff reached, skipping' % name)
                state.setdefault('cutoff_hit', []).append(name)
                continue
            m = run_one(root, name, extra, prompt, cfg, diag_sha)
            metas.append(m)
            (root / 'blocks.json').write_text(json.dumps(metas, indent=1, default=str))
            if m['status'] == 'PROCESS_GATE':
                raise RuntimeError('process gate tripped; abort (restore follows)')
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
                                                        runs=[(m['name'], m['status']) for m in metas]), indent=2, default=str))
    return 0 if restored.get('restored') else 2


if __name__ == '__main__':
    import signal
    for s in (signal.SIGTERM, getattr(signal, 'SIGBREAK', signal.SIGTERM)):
        signal.signal(s, lambda *_: (_ for _ in ()).throw(SystemExit(3)))
    sys.exit(main())
