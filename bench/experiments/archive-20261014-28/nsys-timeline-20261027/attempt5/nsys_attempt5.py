"""Diagnostic Nsight Systems timeline of the UNMODIFIED production engine (LUNA-20261012-027 continuation, 2026-10-27).

Runs on the remote desktop under a detached scheduled task. Stops the live API (verified PIDs only, after idle),
runs: ref (untraced) -> A (cuda graph-node trace + CPU sampling + ctxsw) -> B (cuda graph-level only, overhead check),
ALWAYS restores the API in `finally`, then exports sqlite + stats (after restore).
stdin of the engine is a file ("GEN 512 <prompt>" + "QUIT"); nsys cannot forward a pipe. Tracing is started with
`nsys launch` + `nsys start` just before decode and stopped on DONE.
"""
import hashlib, json, os, re, subprocess, sys, time
from pathlib import Path
import psutil

sys.path.insert(0, r'C:\Users\User\Strata-Adrian-control\tools')
import next_steps_ab_20261018 as ns

ROOT = Path(sys.argv[1])
ROOT.mkdir(parents=True, exist_ok=True)
ns.log.path = ROOT / 'run.log'
log = ns.log
NSYS = r'C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.5.1\target-windows-x64\nsys.exe'
EXE = ns.EXE_C
EXE_SHA = ns.EXE_C_SHA
MARK = 'nsys-timeline-20261027'
GEN_TOKENS = 1024
RUN_CAP_S = 15 * 60
PHASES = ['ref', 'W', 'A']
MODES = {'ref': 'none', 'W': 'wpr', 'A': 'full'}
WPR_PROFILES = {'wpr': ['GeneralProfile', 'DiskIO', 'FileIO'], 'full': ['DiskIO', 'FileIO']}
DEADLINE = time.monotonic() + 75 * 60   # whole job (incl. API stop wait) must reach the restore step by then
cfg = json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
CFG_SHA = ns.sha(ns.CONFIG)
results = {}


def save():
    (ROOT / 'results.json').write_text(json.dumps(results, indent=2, default=str))


def own_engine_pids():
    out = set()
    for p in psutil.process_iter(['pid', 'name']):
        if (p.info['name'] or '').lower() == 'strata.exe':
            try:
                for par in p.parents():
                    if MARK in ' '.join(par.cmdline() or []):
                        out.add(p.pid)
            except psutil.Error:
                pass
    return out


def foreign():
    mine = own_engine_pids()
    return [x for x in ns.processes() if x['pid'] not in mine]


def kill_own():
    mine = own_engine_pids()
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        cl = ' '.join(p.info['cmdline'] or [])
        if p.pid == os.getpid():
            continue
        nm = (p.info['name'] or '').lower()
        if (nm in ('cmd.exe', 'nsys.exe') and MARK in cl) or p.pid in mine:
            try:
                log('kill own pid %d %s' % (p.pid, nm))
                p.kill()
            except psutil.Error:
                pass


def nsys(args, timeout=1800, env=None):
    t0 = time.time()
    r = subprocess.run([NSYS] + args, capture_output=True, text=True, timeout=timeout, env=env,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    log('nsys %s -> rc=%s in %.1fs %s' % (' '.join(args[:1]), r.returncode, time.time() - t0,
                                          (r.stdout + r.stderr).strip()[:300].replace('\n', ' | ')))
    return r


def wpr(args, timeout=900):
    t0 = time.time()
    r = subprocess.run(['wpr'] + args, capture_output=True, text=True, timeout=timeout,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    log('wpr %s -> rc=%s in %.1fs %s' % (' '.join(args[:3]), r.returncode, time.time() - t0,
                                         (r.stdout + r.stderr).strip()[-250:].replace('\n', ' | ')))
    return r


def wpr_recording():
    r = subprocess.run(['wpr', '-status'], capture_output=True, text=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
    return 'not recording' not in (r.stdout + r.stderr).lower()


def run_engine(name, mode, ref_prefill_s=None):
    d = ROOT / name
    d.mkdir()
    args, env = ns.build_command('C', cfg)
    assert ns.sha(EXE) == EXE_SHA
    pre = foreign()
    (d / 'process-gate-before.json').write_text(json.dumps(pre, indent=2))
    if pre or ns.engines():
        raise RuntimeError('process gate before %s: %s' % (name, json.dumps(pre)))
    prompt = ns.PROMPT.read_text(encoding='utf-8-sig').strip()
    inp, out, err = d / 'stdin.txt', d / 'stdout.log', d / 'stderr.log'
    with open(inp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('GEN %d %s\nQUIT\n' % (GEN_TOKENS, prompt))
    cmdf = d / ('run-%s.cmd' % MARK)
    cmdf.write_text('@echo off\r\ncd /d "%s"\r\n"%s" %s < "%s" > "%s" 2> "%s"\r\n' % (
        EXE.parent, EXE, ' '.join(a if a.startswith('--') else '"%s"' % a for a in args), inp, out, err))
    stro = {k: v for k, v in env.items() if k.startswith('STRATA_')}
    manifest = dict(name=name, mode=mode, exe=str(EXE), binary_sha256=ns.sha(EXE), args=args, env=stro,
                    prompt_sha256=ns.sha(ns.PROMPT), config_sha256=CFG_SHA,
                    args_env_sha256=hashlib.sha256(json.dumps([args, stro], sort_keys=True).encode()).hexdigest().upper(),
                    gen_tokens=GEN_TOKENS, available_ram_gib=round(psutil.virtual_memory().available / 2**30, 2))
    sess = 'ntl%s' % name
    ev = {}
    rec = dict(manifest=manifest, events=ev, status='STARTED')
    results[name] = rec
    traced = mode == 'full'
    use_wpr = mode in ('wpr', 'full')
    wpr_on = False
    t0 = time.monotonic()
    if traced:
        gran = 'node' if mode == 'full' else 'graph'
        largs = ['launch', '--session-new=' + sess, '--trace=cuda,nvtx', '--cuda-graph-trace=' + gran,
                 'cmd.exe', '/c', str(cmdf)]
        manifest['nsys_launch'] = largs
        # `nsys launch` blocks until the target exits on this system: run it detached, output to files.
        lo, le = open(d / 'nsys-launch.out', 'w'), open(d / 'nsys-launch.err', 'w')
        launch_proc = subprocess.Popen([NSYS] + largs, env=env, stdin=subprocess.DEVNULL, stdout=lo, stderr=le,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(3)
        log('nsys launch started pid %d (poll=%s)' % (launch_proc.pid, launch_proc.poll()))
    else:
        subprocess.Popen(['cmd.exe', '/c', str(cmdf)], env=env, creationflags=subprocess.CREATE_NO_WINDOW)
    (d / 'command.json').write_text(json.dumps(manifest, indent=2))
    off, buf, tokens = 0, '', []
    started_trace = False
    next_gate = 0.0
    status = None
    while True:
        now = time.monotonic() - t0
        if now > RUN_CAP_S or time.monotonic() > DEADLINE:
            status = 'TIMEOUT'
            break
        try:
            with open(out, 'rb') as f:
                f.seek(off)
                chunk = f.read()
            off += len(chunk)
            buf += chunk.decode('utf-8', 'replace')
        except FileNotFoundError:
            pass
        while '\n' in buf:
            line, buf = buf.split('\n', 1)
            line = line.strip()
            tnow = time.monotonic() - t0
            if line.startswith('READY') and 'ready' not in ev:
                ev['ready'] = tnow
                text = err.read_text(encoding='utf-8', errors='replace')
                facts = ns.startup_facts(text)
                ok, why = ns.capacity_verdict('C', facts)
                if traced:
                    # traced phases: nsys injection costs VRAM -> accept slots >= 3135 (-0.57% vs 3153); RAM/lock still strict
                    sl = int(facts['slots'] or 0)
                    ok = sl >= 3135 and facts['ram_budget_gib'] == ns.EXPECT_RAM and facts['locked_mib'] == ns.EXPECT_LOCK
                    why = '' if ok else 'traced gate: slots %s ram %s lock %s' % (facts['slots'], facts['ram_budget_gib'], facts['locked_mib'])
                    facts['traced_slots_note'] = '%d slots = %.2f%% vs 3153 under nsys injection' % (sl, (sl / 3153 - 1) * 100)
                facts.update(capacity_ok=ok, capacity_detail=why)
                (d / 'startup.json').write_text(json.dumps(facts, indent=2))
                rec['startup'] = facts
                log('%s READY %.1fs %s' % (name, tnow, json.dumps({k: facts[k] for k in ('slots', 'ram_budget_gib', 'locked_mib', 'pool_line')})))
                if not ok:
                    status = 'ENV_BLOCKED_CAPACITY: ' + why
                    break
            elif line.startswith('T ') and line.split()[1].lstrip('-').isdigit():
                if 'first_t' not in ev:
                    ev['first_t'] = tnow
                tokens.append(int(line.split()[1]))
            elif line.startswith('DONE '):
                ev['done'] = tnow
                ev['done_line'] = line
            elif line.startswith('ERR '):
                status = 'ERR ' + line
                break
        if status:
            break
        if (traced or use_wpr) and not started_trace and 'ready' in ev:
            trig = ev['ready'] + max(0.0, (ref_prefill_s or 0) - 2.5)
            if 'first_t' in ev or now >= trig:
                ev['start_cmd_at'] = now
                if use_wpr:
                    pa = []
                    for pf in WPR_PROFILES[mode]:
                        pa += ['-start', pf]
                    rw = wpr(pa + ['-filemode'], 300)
                    ev['wpr_start_done'] = time.monotonic() - t0
                    ev['wpr_start_utc'] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
                    wpr_on = rw.returncode == 0
                    if not wpr_on:
                        status = 'WPR_START_FAILED rc=%s %s' % (rw.returncode, (rw.stdout + rw.stderr)[:300])
                        break
                if traced:
                    sargs = ['start', '--session=' + sess, '-o', str(ROOT / ('trace-' + name)),
                             '--force-overwrite=true', '--stats=false',
                             '--sample=process-tree', '--cpuctxsw=process-tree', '--backtrace=auto',
                             '--sampling-frequency=1000']
                    rec['nsys_start'] = sargs
                    r = nsys(sargs, 120)
                    ev['start_cmd_done'] = time.monotonic() - t0
                    ev['first_t_seen_before_start'] = 'first_t' in ev
                    started_trace = r.returncode == 0
                    if not started_trace:
                        status = 'NSYS_START_FAILED rc=%s %s' % (r.returncode, (r.stdout + r.stderr)[:300])
                        break
                else:
                    started_trace = True
        if 'done' in ev:
            break
        if now >= next_gate:
            other = foreign()
            (d / 'live-process-gate.json').write_text(json.dumps(other, indent=2))
            if other:
                status = 'LIVE_PROCESS_GATE ' + json.dumps(other)
                break
            next_gate = now + 5
            if now > 30 and not own_engine_pids():
                status = 'ENGINE_GONE'
                break
        time.sleep(0.05)
    if status is None and traced:
        ev['stop_cmd_at'] = time.monotonic() - t0
        r = nsys(['stop', '--session=' + sess], 1800)
        ev['stop_cmd_done'] = time.monotonic() - t0
        if r.returncode != 0:
            status = 'NSYS_STOP_FAILED rc=%s %s' % (r.returncode, (r.stdout + r.stderr)[:300])
    if wpr_on:
        ev['wpr_stop_at'] = time.monotonic() - t0
        rw = wpr(['-stop', str(ROOT / ('wpr-' + name + '.etl')), '-skipPdbGen'], 1200)
        ev['wpr_stop_done'] = time.monotonic() - t0
        wpr_on = False
        rec['wpr_stop_rc'] = rw.returncode
        etl = ROOT / ('wpr-' + name + '.etl')
        if etl.exists():
            rec['etl_size'] = etl.stat().st_size
        if rw.returncode != 0 and status is None:
            status = 'WPR_STOP_FAILED rc=%s' % rw.returncode
    for _ in range(120):
        if not own_engine_pids():
            break
        time.sleep(1)
    if own_engine_pids():
        log('%s engine still alive after QUIT; killing own tree' % name)
        kill_own()
    if traced:
        try:
            nsys(['shutdown', '--session=' + sess], 60)
        except Exception as e:  # noqa
            log('shutdown: %r' % e)
    kill_own()
    if wpr_on:
        wpr(['-cancel'], 120)
    time.sleep(1.0)
    text = err.read_text(encoding='utf-8', errors='replace') if err.exists() else ''
    rec['request'] = ns.parse_request(text)
    rec['done_parse'] = ns.parse_done(ev.get('done_line', 'DONE'))
    (d / 'tokens.json').write_text(json.dumps(tokens))
    rec['output_tokens'] = len(tokens)
    rec['token_sha256'] = ns.sha(d / 'tokens.json')
    rec['binary_sha_after'] = ns.sha(EXE)
    left = []
    for _ in range(60):
        left = foreign()
        if not left:
            break
        time.sleep(1)
    (d / 'process-gate-after.json').write_text(json.dumps(left, indent=2))
    rec['residual_after'] = left
    rec['status'] = status or ('OK' if len(tokens) == GEN_TOKENS and 'done' in ev else 'INCOMPLETE')
    log('%s status=%s tokens=%d request=%s' % (name, rec['status'], len(tokens), json.dumps(
        {k: rec['request'].get(k) for k in ('decode_tok_s', 'ms_window', 'tokens_per_window', 'gpu_wait_ms', 'cpu_ms', 'jobs_ms', 'prefill_ms')})))
    save()
    return rec


def main():
    assert ns.sha(EXE) == EXE_SHA
    assert ns.sha(ns.PROMPT) == ns.PROMPT_SHA
    assert subprocess.check_output(['hostname'], text=True).strip().upper() == ns.HOSTNAME
    assert Path(NSYS).exists()
    assert not wpr_recording(), 'WPR already recording'
    results['identity'] = dict(binary_sha_before=ns.sha(EXE), config_sha=CFG_SHA, prompt_sha=ns.sha(ns.PROMPT),
                               nsys=subprocess.check_output([NSYS, '--version'], text=True).strip(),
                               started=time.strftime('%Y-%m-%d %H:%M:%S'))
    ref_prefill = None
    try:
        stopped = ns.stop_api(ROOT)
        results['identity']['api_was_running'] = stopped
        results['identity']['api_stopped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        save()
        for name in PHASES:
            rec = run_engine(name, MODES[name], ref_prefill) if (name == 'ref' or DEADLINE - time.monotonic() > 8 * 60) else None
            if rec is None:
                log('phase %s skipped: overall 75 min cap' % name)
                break
            if name == 'ref':
                ref_prefill = (rec['request'].get('prefill_ms') or 0) / 1000.0
                if 'first_t' not in rec['events'] or 'ready' not in rec['events']:
                    log('ref did not show live READY/T lines in stdout; aborting traced phases')
                    break
            if rec['status'] != 'OK':
                log('phase %s status %s; stopping further phases' % (name, rec['status']))
                break
    except Exception as e:  # noqa
        log('EXCEPTION %r' % (e,))
        results['exception'] = repr(e)
    finally:
        kill_own()
        try:
            if wpr_recording():
                wpr(['-cancel'], 120)
        except Exception as e:  # noqa
            log('wpr cancel check: %r' % e)
        results['identity']['binary_sha_after'] = ns.sha(EXE)
        results['identity']['config_sha_after'] = ns.sha(ns.CONFIG)
        res = ns.restore_api(ROOT)
        results['restore'] = res
        results['identity']['api_restored_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        save()
    for name in ('A',):
        rep = ROOT / ('trace-%s.nsys-rep' % name)
        if not rep.exists():
            continue
        try:
            results.setdefault('exports', {})[name] = dict(rep_size=rep.stat().st_size, rep_sha256=ns.sha(rep))
            nsys(['export', '--type', 'sqlite', '--force-overwrite=true', '-o', str(ROOT / ('trace-%s.sqlite' % name)), str(rep)], 3600)
            sq = ROOT / ('trace-%s.sqlite' % name)
            if sq.exists():
                results['exports'][name]['sqlite_size'] = sq.stat().st_size
            for rpt in ('cuda_gpu_kern_sum', 'cuda_gpu_mem_time_sum', 'cuda_api_sum', 'cuda_gpu_sum',
                        'cuda_kern_exec_sum', 'nvtx_sum', 'osrt_sum', 'cuda_gpu_mem_size_sum'):
                r = nsys(['stats', '--report', rpt, '--format', 'csv', '--force-export=false',
                          '--force-overwrite=true', str(rep)], 1800)
                (ROOT / ('stats-%s-%s.csv' % (name, rpt))).write_text(
                    r.stdout + ('\n#STDERR\n' + r.stderr if r.returncode else ''), encoding='utf-8')
        except Exception as e:  # noqa
            log('export %s failed %r' % (name, e))
            results.setdefault('exports', {}).setdefault(name, {})['error'] = repr(e)
        save()
    for name in ('W', 'A'):
        etl = ROOT / ('wpr-%s.etl' % name)
        if etl.exists():
            try:
                t1 = time.time()
                r = subprocess.run(['tracerpt', str(etl), '-o', str(ROOT / ('wpr-%s.csv' % name)), '-of', 'CSV',
                                    '-summary', str(ROOT / ('wpr-%s-summary.txt' % name)), '-y'],
                                   capture_output=True, text=True, timeout=3600, cwd=str(ROOT),
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                log('tracerpt %s rc=%s %.1fs %s' % (name, r.returncode, time.time() - t1, (r.stdout + r.stderr)[-200:].replace('\n', ' | ')))
                results.setdefault('etl', {})[name] = dict(etl_sha256=ns.sha(etl), etl_size=etl.stat().st_size, tracerpt_rc=r.returncode)
            except Exception as e:  # noqa
                log('tracerpt %s failed %r' % (name, e))
        save()
    results['identity']['finished'] = time.strftime('%Y-%m-%d %H:%M:%S')
    save()
    log('ALL DONE')


if __name__ == '__main__':
    main()
