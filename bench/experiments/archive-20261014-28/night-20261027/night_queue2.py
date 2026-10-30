"""Overnight queue 2026-10-27 (detached). One API stop window, hard restore cap, API restored in finally.
Items: 1 MCHK gate -> 2 MISS_OVERLAP A/B (C0,D0,M x5) -> 3 spin variants (only if M not clearly negative) -> 4 untraced neuro decode baseline.
usage: python night_queue_20261027.py <out_root>   (arms_night2.json lives next to this script)
"""
import json, os, re, subprocess, sys, time
from pathlib import Path
import psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, r'C:\Users\User\Strata-Adrian-control\tools')
import replay_ab_20261027 as rp  # noqa: E402
ns = rp.ns
log = ns.log

NEW_BLOCK_CUTOFF_MIN = 135   # no new block after this; worst case block ~25 min -> restore well inside 180 min
ROUNDS_AB = 5
MARK = 'night-20261027'
state = {}


def save(root):
    (root / 'queue_state.json').write_text(json.dumps(state, indent=2, default=str))


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def paired_ratio(rows, a, b):
    """mean over points of (mean-over-rounds tok/s of a / that of b - 1)."""
    def per_point(arm):
        d = {}
        for r in rows:
            if r['arm'] == arm and r.get('m_decode_tok_s') and not r.get('error'):
                d.setdefault(r['pid'], []).append(r['m_decode_tok_s'])
        return {k: mean(v) for k, v in d.items()}
    pa, pb = per_point(a), per_point(b)
    common = sorted(set(pa) & set(pb))
    return mean([pa[k] / pb[k] - 1 for k in common]) if common else None


def run_blocks(root, specs, arms, rounds, max_tokens, t_start, rows_out, blocks_all, tag):
    seq = rp.schedule(arms, rounds)
    log('%s order: %s' % (tag, ' | '.join('r%d:%s' % s for s in seq)))
    base = len(blocks_all)
    for i, (rnd, arm) in enumerate(seq, 1):
        if (time.time() - t_start) / 60 > NEW_BLOCK_CUTOFF_MIN:
            log('%s: cutoff reached, skipping remaining blocks' % tag)
            state.setdefault('cutoff_hit', []).append(tag)
            break
        meta, rows = rp.run_block(root, base + i, rnd, arm, specs[arm], max_tokens)
        blocks_all.append(meta)
        rows_out.extend(rows)
        (root / ('rows-%s.json' % tag)).write_text(json.dumps(rows_out, indent=1))
        (root / 'blocks.json').write_text(json.dumps(blocks_all, indent=1))
        if meta['status'] == 'PROCESS_GATE':
            raise RuntimeError('process gate tripped; abort (restore follows)')


def neuro_run(root, name, spec, tokens=1024):
    d = root / ('neuro-' + name)
    d.mkdir()
    exe = Path(spec['exe'])
    assert ns.sha(exe) == spec['sha'].upper()
    cfg = json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
    args, env = ns.build_command('C', cfg)
    for k, v in spec.get('env', {}).items():
        env[k] = str(v)
    pre = ns.processes()
    if pre or ns.engines():
        raise RuntimeError('process gate before neuro %s: %s' % (name, json.dumps(pre)))
    prompt = ns.PROMPT.read_text(encoding='utf-8-sig').strip()
    inp, out, err = d / 'stdin.txt', d / 'stdout.log', d / 'stderr.log'
    with open(inp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('GEN %d %s\nQUIT\n' % (tokens, prompt))
    cmdf = d / ('run-%s.cmd' % MARK)
    cmdf.write_text('@echo off\r\ncd /d "%s"\r\n"%s" %s < "%s" > "%s" 2> "%s"\r\n' % (
        exe.parent, exe, ' '.join(a if a.startswith('--') else '"%s"' % a for a in args), inp, out, err))
    (d / 'command.json').write_text(json.dumps(dict(exe=str(exe), sha=ns.sha(exe), args=args,
        env={k: v for k, v in env.items() if k.startswith('STRATA_')}, prompt_sha=ns.sha(ns.PROMPT), tokens=tokens), indent=2))
    proc = subprocess.Popen(['cmd.exe', '/c', str(cmdf)], env=env, creationflags=subprocess.CREATE_NO_WINDOW)
    t0 = time.time()
    rec = dict(name=name, status='STARTED')
    try:
        while proc.poll() is None:
            if time.time() - t0 > 15 * 60:
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
    m = re.search(r'strata decode timing: [^\n]*', text)
    rec['decode_timing'] = m.group(0) if m else None
    m = re.search(r'(\d+) generated in ([\d.]+) ms \(([\d.]+) tok/s\)', text)
    rec['generated'] = m.group(0) if m else None
    rec['tok_s'] = float(m.group(3)) if m else None
    if rec['status'] == 'STARTED':
        rec['status'] = 'OK' if m else 'NO_RESULT'
    mo = [l for l in text.splitlines() if l.startswith('MISS_OVERLAP ')]
    rec['miss_overlap_last'] = mo[-1] if mo else None
    (d / 'result.json').write_text(json.dumps(rec, indent=2))
    log('neuro %s: %s' % (name, json.dumps(rec)[:600]))
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
    specs = json.loads((HERE / 'arms_night2.json').read_text())
    (root / 'arms.json').write_text(json.dumps(specs, indent=1))
    blocks_all = []
    stopped = False
    restored = None
    t_start = time.time()
    try:
        stopped = True
        state['api_was_running'] = ns.stop_api(root)
        state['api_stopped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        ns.ram_start_gate(root)
        t_start = time.time()
        save(root)
        rows_ab = []
        run_blocks(root, specs, ['C0', 'M', 'S2K', 'S500'], 5, 512, t_start, rows_ab, blocks_all, 'CONF')
        save(root)
        # ---- item 4: untraced neuro decode baseline (C0/M interleaved twice if the family is alive)
        order = ['C0', 'S2K', 'S2K', 'C0']
        nres = []
        for j, a in enumerate(order, 1):
            if (time.time() - t_start) / 60 > NEW_BLOCK_CUTOFF_MIN + 10:
                log('neuro: cutoff, skipping rest')
                break
            nres.append(neuro_run(root, '%d-%s' % (j, a), specs[a]))
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
