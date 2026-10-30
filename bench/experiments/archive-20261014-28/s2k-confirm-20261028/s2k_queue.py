"""S2K_PROMOTION_CONFIRM phase 1 (detached). One API stop window; API restored in finally.
1a MCHK gate (S2K settings + CHECK) -> 1b greedy 8 rounds ABBA -> 1c production sampling 3 rounds -> 1d neuro warm (C0,S2K,S2K,C0).
usage: python s2k_queue.py <out_root>   (arms_s2k.json lives next to this script; the harness replay_ab_20261027 is imported unchanged,
only its make_body is replaced for 1c by a sampling variant defined here)
"""
import json, os, re, subprocess, sys, threading, time
from pathlib import Path
import psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, r'C:\Users\User\Strata-Adrian-control\tools')
import replay_ab_20261027 as rp  # noqa: E402
ns = rp.ns
log = ns.log

MARK = 's2k-confirm-20261028'
NEW_BLOCK_CUTOFF_MIN = 150   # no new block/run after this
HARD_CAP_MIN = 175           # watchdog kills our own children after this, so cleanup + restore always follow
NEURO_TIMEOUT_MIN = 15
state = {}
ABORT = threading.Event()
_greedy_body = rp.make_body


def save(root):
    (root / 'queue_state.json').write_text(json.dumps(state, indent=2, default=str))


def sampling_body(pid, max_tokens):
    """Production request exactly as captured (temperature 1.0, top_p 0.95, top_k 20, min_p 0, thinking on, effort medium, seed kept); only max_tokens is set."""
    body = json.loads((rp.REQ_DIR / (pid + '.json')).read_text(encoding='utf-8'))
    body['max_tokens'] = max_tokens
    assert body['temperature'] == 1.0 and body['top_p'] == 0.95 and body['top_k'] == 20 and body['min_p'] == 0.0
    assert body['chat_template_kwargs'] == {'enable_thinking': True, 'reasoning_effort': 'medium'}
    return body


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


PRIO = []   # engine priority readings per strata.exe; the queue sets AboveNormal if the child did not inherit it (both arms identically)
PRIO_FAIL = threading.Event()
ABOVE_NORMAL = getattr(psutil, 'ABOVE_NORMAL_PRIORITY_CLASS', None)


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
                        try:
                            ent['ionice'] = str(p.ionice())
                        except Exception:  # noqa
                            ent['ionice'] = None
                        PRIO.append(ent)
                    if ent is not None and (not ent['readings'] or now - ent['readings'][-1][0] >= 60):
                        ent['readings'].append((now, str(p.nice())))   # shows whether live strata_memory_policy touched it
                except psutil.Error:
                    pass
        except Exception:  # noqa
            pass


def run_blocks(root, specs, arms, rounds, max_tokens, t_start, rows_out, blocks_all, tag):
    seq = rp.schedule(arms, rounds)
    log('%s order: %s' % (tag, ' | '.join('r%d:%s' % s for s in seq)))
    base = len(blocks_all)
    for i, (rnd, arm) in enumerate(seq, 1):
        if ABORT.is_set() or (time.time() - t_start) / 60 > NEW_BLOCK_CUTOFF_MIN:
            log('%s: cutoff reached, skipping remaining blocks' % tag)
            state.setdefault('cutoff_hit', []).append(tag)
            break
        t_blk = time.time()
        meta, rows = rp.run_block(root, base + i, rnd, arm, specs[arm], max_tokens)
        meta['engine_priority'] = [e for e in PRIO if e['at'] >= t_blk]
        blocks_all.append(meta)
        rows_out.extend(rows)
        (root / ('rows-%s.json' % tag)).write_text(json.dumps(rows_out, indent=1))
        (root / 'blocks.json').write_text(json.dumps(blocks_all, indent=1))
        if meta['status'] == 'PROCESS_GATE':
            raise RuntimeError('process gate tripped; abort (restore follows)')
        if PRIO_FAIL.is_set():
            raise RuntimeError('engine priority could not be set to AboveNormal; abort (restore follows)')


def neuro_block(root, name, spec, tokens=1024, runs=4):
    """One engine, `runs` identical GEN requests (1 warm-up + measured)."""
    d = root / ('neuro-' + name)
    d.mkdir()
    exe = Path(spec['exe'])
    assert ns.sha(exe) == spec['sha'].upper()
    cfg = json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
    args, env = ns.build_command('C', cfg)
    for k, v in (spec.get('env') or {}).items():
        env[k] = str(v)
    pre = ns.processes()
    if pre or ns.engines():
        raise RuntimeError('process gate before neuro %s: %s' % (name, json.dumps(pre)))
    prompt = ns.PROMPT.read_text(encoding='utf-8-sig').strip()
    inp, out, err = d / 'stdin.txt', d / 'stdout.log', d / 'stderr.log'
    with open(inp, 'w', encoding='utf-8', newline='\n') as f:
        for _ in range(runs):
            f.write('GEN %d %s\n' % (tokens, prompt))
        f.write('QUIT\n')
    cmdf = d / ('run-%s.cmd' % MARK)
    cmdf.write_text('@echo off\r\ncd /d "%s"\r\n"%s" %s < "%s" > "%s" 2> "%s"\r\n' % (
        exe.parent, exe, ' '.join(a if a.startswith('--') else '"%s"' % a for a in args), inp, out, err))
    (d / 'command.json').write_text(json.dumps(dict(exe=str(exe), sha=ns.sha(exe), args=args,
        env={k: v for k, v in env.items() if k.startswith('STRATA_')}, prompt_sha=ns.sha(ns.PROMPT), tokens=tokens, runs=runs), indent=2))
    proc = subprocess.Popen(['cmd.exe', '/c', str(cmdf)], env=env, creationflags=subprocess.CREATE_NO_WINDOW)
    t0 = time.time()
    rec = dict(name=name, status='STARTED')
    try:
        while proc.poll() is None:
            if time.time() - t0 > NEURO_TIMEOUT_MIN * 60 or ABORT.is_set():
                rec['status'] = 'TIMEOUT'
                break
            time.sleep(5)
    finally:
        for p in psutil.process_iter(['pid', 'name']):
            if (p.info['name'] or '').lower() == 'strata.exe':
                try:
                    if any(MARK in ' '.join(x.cmdline() or []) for x in p.parents()):
                        p.kill()
                except psutil.Error:
                    pass
        try:
            psutil.Process(proc.pid).kill()
        except psutil.Error:
            pass
    text = err.read_text(encoding='utf-8', errors='replace') if err.exists() else ''
    facts = ns.startup_facts(text)
    rec['startup'] = {k: facts.get(k) for k in ('slots', 'ram_budget_gib', 'locked_mib')}
    rec['startup_ok'] = (str(facts.get('slots')) == '3153' and facts.get('ram_budget_gib') == ns.EXPECT_RAM and facts.get('locked_mib') == ns.EXPECT_LOCK)
    rec['decode_timing'] = re.findall(r'strata decode timing: [^\n]*', text)
    gen = re.findall(r'(\d+) generated in ([\d.]+) ms \(([\d.]+) tok/s\)', text)
    rec['generated'] = [dict(n=int(a), ms=float(b), tok_s=float(c)) for a, b, c in gen]
    rec['tok_s'] = [g['tok_s'] for g in rec['generated']]
    rec['done_lines'] = [l for l in out.read_text(encoding='utf-8', errors='replace').splitlines() if l.startswith('DONE ')] if out.exists() else []
    if rec['status'] == 'STARTED':
        rec['status'] = 'OK' if len(gen) >= runs else 'NO_RESULT'
    mo = [l for l in text.splitlines() if l.startswith('MISS_OVERLAP ')]
    rec['miss_overlap_last'] = mo[-1] if mo else None
    rec['engine_priority'] = [e for e in PRIO if e['at'] >= t0]
    (d / 'result.json').write_text(json.dumps(rec, indent=2))
    log('neuro %s: status=%s tok_s=%s startup_ok=%s' % (name, rec['status'], rec['tok_s'], rec['startup_ok']))
    for _ in range(60):
        if not ns.engines():
            break
        time.sleep(1)
    time.sleep(3)
    return rec


def main():
    root = Path(sys.argv[1])
    root.mkdir(exist_ok=False)
    ns.log.path = root / 'orchestrator.log'
    assert os.environ.get('COMPUTERNAME', '').upper() == ns.HOSTNAME
    assert ns.sha(ns.EXE_C) == ns.EXE_C_SHA, 'control SHA mismatch'
    specs = json.loads((HERE / 'arms_s2k.json').read_text())
    assert ns.sha(Path(specs['S2K']['exe'])) == specs['S2K']['sha'].upper(), 'candidate SHA mismatch'
    (root / 'arms.json').write_text(json.dumps(specs, indent=1))
    blocks_all = []
    stopped = False
    restored = None
    t_start = time.time()
    threading.Thread(target=watchdog, args=(t_start,), daemon=True).start()
    threading.Thread(target=prio_watcher, daemon=True).start()
    try:
        stopped = True
        state['api_was_running'] = ns.stop_api(root)
        state['api_stopped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        ns.ram_start_gate(root)
        t_start = time.time()
        save(root)
        # ---- 1a: MCHK gate (failure -> skip everything, straight to cleanup)
        mchk_ok = False
        try:
            t_blk = time.time()
            meta, _rows = rp.run_block(root, 0, 0, 'MCHK', specs['MCHK'], 128)
            meta['engine_priority'] = [e for e in PRIO if e['at'] >= t_blk]
            blocks_all.append(meta)
            if meta['status'] == 'OK':
                rp.check_gate(root / 'block-00-MCHK-r0')
                mchk_ok = not PRIO_FAIL.is_set()
                if PRIO_FAIL.is_set():
                    log('engine priority could not be set to AboveNormal -> stop before A/B')
            state['mchk'] = dict(ok=mchk_ok, status=meta['status'])
        except Exception as e:  # noqa
            state['mchk'] = dict(ok=False, error=repr(e))
            log('MCHK failed: %r -> phase 1 stops (cleanup follows)' % (e,))
            if 'process gate' in repr(e):
                raise
        save(root)
        if mchk_ok:
            # ---- 1b: greedy, 8 rounds, order alternates each round (ABBA)
            rows_b = []
            run_blocks(root, specs, ['C0', 'S2K'], 8, 512, t_start, rows_b, blocks_all, 'GREEDY')
            save(root)
            # ---- 1c: production sampling, 3 rounds interleaved
            rp.make_body = sampling_body
            try:
                rows_c = []
                run_blocks(root, specs, ['C0', 'S2K'], 3, 512, t_start, rows_c, blocks_all, 'SAMPLING')
            finally:
                rp.make_body = _greedy_body
            save(root)
            # ---- 1d: neuro, one engine per block, warm-up 1 + 3 measured
            nres = []
            for j, a in enumerate(['C0', 'S2K', 'S2K', 'C0'], 1):
                if ABORT.is_set() or (time.time() - t_start) / 60 > NEW_BLOCK_CUTOFF_MIN + 10:
                    log('neuro: cutoff, skipping rest')
                    state.setdefault('cutoff_hit', []).append('NEURO')
                    break
                nres.append(neuro_block(root, '%d-%s' % (j, a), specs[a]))
                state['neuro'] = nres
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
        state['finished'] = time.strftime('%Y-%m-%d %H:%M:%S')
        state['elapsed_min'] = round((time.time() - t_start) / 60, 1)
        save(root)
        (root / 'DONE.json').write_text(json.dumps(dict(finished=state['finished'], api_restored=restored.get('restored'),
                                                        blocks=[(b['block'], b['arm'], b['status']) for b in blocks_all]), indent=2))
    return 0 if restored.get('restored') else 2


if __name__ == '__main__':
    import signal
    for s in (signal.SIGTERM, getattr(signal, 'SIGBREAK', signal.SIGTERM)):
        signal.signal(s, lambda *_: (_ for _ in ()).throw(SystemExit(3)))
    sys.exit(main())
