"""Overnight 2026-10-20: deterministic Hermes replay A/B harness (fresh serve.server + engine per block).

Reuses the proven helpers of next_steps_ab_20261018.py (API stop/restore, process gates, parsers).
For every block: a private serve.server (127.0.0.1:8081) with a config COPY (exe/cwd/log/env/args of the arm) starts a fresh engine,
the 10 prepared Hermes requests are sent sequentially with greedy decoding (temperature 0, max_tokens N), raw responses are saved,
engine-log deltas (decode timing, SSD MB, cache hit, drafts, route-tail-skip) are parsed per request.

  python replay_ab_20261020.py <run_root> --arms-file arms.json --arms C,B02 --rounds 3 [--max-tokens 512] [--cap-min 100]
The live API is stopped (verified PIDs only) for the whole campaign and ALWAYS restored in finally (ns.restore_api).
"""
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import urllib.request

import psutil

sys.path.insert(0, str(Path(__file__).resolve().parent))
import next_steps_ab_20261018 as ns  # noqa: E402

PY = r'C:\Users\User\Strata\archive\legacy\20261009\Strata-lm-run-2026-09-28\.venv\Scripts\python.exe'
REQ_DIR = Path(r'C:\Users\User\Strata-Adrian-control\runs\overnight-20261020-inputs\requests')
SERVE_V0142 = r'C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\upstream-v0142'
PORT = 8081
POINTS = ['p%02d' % i for i in range(1, 11)]
log = ns.log


def own_pids():
    me = psutil.Process()
    return {c.pid for c in me.children(recursive=True)}


def foreign_processes():
    mine = own_pids()
    return [p for p in ns.processes() if p['pid'] not in mine]


def http_local(path, body=None, timeout=900):
    url = 'http://127.0.0.1:%d%s' % (PORT, path)
    if body is None:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.load(r)
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def kill_tree(proc):
    try:
        parent = psutil.Process(proc.pid)
        kids = parent.children(recursive=True)
    except psutil.Error:
        return
    allp = kids + [parent]
    for k in allp:
        try:
            k.terminate()
        except psutil.Error as e:
            log('kill_tree: terminate pid %s failed: %r' % (k.pid, e))
    try:
        gone, alive = psutil.wait_procs(allp, timeout=30)
    except psutil.Error:
        alive = []
    for a in alive:
        try:
            a.kill()
        except psutil.Error as e:
            log('kill_tree: kill pid %s failed: %r' % (a.pid, e))


def build_cfg(arm, spec, blockdir):
    cfg = json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
    exe = Path(spec['exe'])
    cfg['exe'] = str(exe)
    cfg['cwd'] = str(exe.parent)
    cfg['log'] = str(blockdir / 'engine.log')
    cfg['open_browser'] = False
    args = list(cfg['args'])
    for flag, value in (spec.get('args') or {}).items():
        if value is None:                      # remove flag + value
            i = args.index(flag)
            del args[i:i + 2]
        elif flag in args:
            args[args.index(flag) + 1] = value
        else:
            args += [flag, value]
    cfg['args'] = args
    env = dict(cfg.get('env') or {})
    for k, v in (spec.get('env') or {}).items():
        if v is None:
            env.pop(k, None)
        else:
            env[k] = str(v).replace('{BLOCKDIR}', str(blockdir))
    assert 'STRATA_VERIFY_PROFILE' not in env
    cfg['env'] = env
    p = blockdir / 'config.json'
    p.write_text(json.dumps(cfg, indent=1))
    return p, cfg


def read_from(path, off):
    with open(path, 'rb') as f:
        f.seek(off)
        return f.read().decode('utf-8', errors='replace'), f.tell()


def parse_tail(tail):
    r = ns.parse_request(tail)
    r.pop('adapt_lines', None)
    m = re.findall(r'files (\d+) blobs ([\d.]+) MB read', tail)
    r['files_blobs_cum'] = int(m[-1][0]) if m else None
    r['files_mb_cum'] = float(m[-1][1]) if m else None
    m = re.findall(r'since the start RAM (\d+) blobs', tail)
    r['ram_blobs_cum'] = int(m[-1]) if m else None
    m = re.findall(r'route tail skip: (\d+) missed experts skipped', tail)
    r['tail_skip_cum'] = int(m[-1]) if m else None
    m = re.findall(r'GPU (\d+) hits this request', tail)
    r['gpu_hits'] = int(m[-1]) if m else None
    m = re.findall(r'suffix drafts: (\d+) windows, (\d+) of (\d+) drafts accepted', tail)
    r['suffix'] = list(m[-1]) if m else None
    for key in ('GATESKIP', 'GATECOUNT', 'ROUTEPRIOR', 'cold reads'):
        hits = [l.strip() for l in tail.splitlines() if key in l]
        if hits:
            r[key.lower().replace(' ', '_') + '_lines'] = hits[-6:]
    return r


def make_body(pid, max_tokens):
    body = json.loads((REQ_DIR / (pid + '.json')).read_text(encoding='utf-8'))
    for k in ('top_p', 'top_k', 'min_p', 'presence_penalty', 'seed', 'frequency_penalty', 'repetition_penalty'):
        body.pop(k, None)
    body['temperature'] = 0
    body['max_tokens'] = max_tokens
    return body


def capacity_ok(arm, spec, facts):
    """Control-family arms (current-best binary) must match the established gate; others only record."""
    if Path(spec['exe']) == ns.EXE_C or spec.get('strict_capacity'):
        lo, hi = 3153, 3153
        problems = []
        try:
            s = int(facts['slots'])
        except (TypeError, ValueError):
            return False, 'no slots evidence', True
        if not lo <= s <= hi:
            problems.append('slots %d' % s)
        if facts['ram_budget_gib'] != ns.EXPECT_RAM:
            problems.append('RAM budget %r' % facts['ram_budget_gib'])
        if facts['locked_mib'] != ns.EXPECT_LOCK:
            problems.append('locked %r' % facts['locked_mib'])
        return not problems, '; '.join(problems), True
    return True, 'recorded only (not control binary): slots=%s ram=%s locked=%s resident=%s' % (
        facts.get('slots'), facts.get('ram_budget_gib'), facts.get('locked_mib'), facts.get('resident_gib')), False


def run_block(root, index, rnd, arm, spec, max_tokens):
    d = root / ('block-%02d-%s-r%d' % (index, arm, rnd))
    d.mkdir()
    exe = Path(spec['exe'])
    meta = dict(block=index, round=rnd, arm=arm, binary=str(exe), status='STARTED')
    if not exe.exists():
        meta['status'] = 'NO_BINARY'
        (d / 'meta.json').write_text(json.dumps(meta, indent=2))
        return meta, []
    meta['binary_sha256'] = ns.sha(exe)
    if spec.get('sha') and meta['binary_sha256'] != spec['sha'].upper():
        meta['status'] = 'BINARY_MISMATCH'
        (d / 'meta.json').write_text(json.dumps(meta, indent=2))
        return meta, []
    if ns.engines():
        raise RuntimeError('strata.exe already running: %r' % ns.engines())
    left = ns.processes()
    if left:
        raise RuntimeError('process gate before block: %s' % json.dumps(left))
    ns.log_heavy('%s r%d pre-block' % (arm, rnd), d / 'heavy-processes.json')
    cfgp, cfg = build_cfg(arm, spec, d)
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('STRATA_')}
    cmd = [PY, '-u', '-m', 'serve.server', '--engine', 'strata', '--config', str(cfgp), '--host', '127.0.0.1', '--port', str(PORT)]
    (d / 'command.json').write_text(json.dumps(dict(cmd=cmd, cwd=spec['serve_dir'], exe_sha=meta['binary_sha256'],
                                                    engine_args=cfg['args'], engine_env=cfg['env'],
                                                    available_ram_gib=round(psutil.virtual_memory().available / 2**30, 2),
                                                    power_plan=subprocess.run(['powercfg', '/getactivescheme'], capture_output=True, text=True).stdout.strip()), indent=1))
    rows = []
    srv = None
    try:
        with open(d / 'server.stdout.log', 'w') as so, open(d / 'server.stderr.log', 'w') as se:
            srv = subprocess.Popen(cmd, cwd=spec['serve_dir'], env=env, stdout=so, stderr=se, creationflags=subprocess.CREATE_NO_WINDOW)
            t0 = time.time()
            ready = False
            while time.time() - t0 < 900:
                if srv.poll() is not None:
                    raise RuntimeError('server exited rc=%s' % srv.returncode)
                live_log = d / 'engine.log'
                if live_log.exists() and 'DIRECT_SHADOW FATAL' in live_log.read_text(encoding='utf-8', errors='replace'):
                    raise RuntimeError('DIRECT_SHADOW FATAL: candidate refused source/read; no fallback')
                try:
                    h = http_local('/health', timeout=5)
                    if h.get('loaded'):
                        ready = True
                        break
                except Exception:  # noqa
                    pass
                time.sleep(3)
            if not ready:
                raise RuntimeError('engine not loaded within 900 s')
            owned_engines = [p for p in psutil.Process(srv.pid).children(recursive=True) if p.name().lower() == 'strata.exe']
            assert len(owned_engines) == 1, 'engine ownership mismatch'
            engine = owned_engines[0]
            assert ns.sha(Path(engine.exe())) == meta['binary_sha256'], 'running binary mismatch'
            engine.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
            assert engine.nice() == psutil.ABOVE_NORMAL_PRIORITY_CLASS
            effective = engine.environ()
            assert effective.get('STRATA_IQ3S_MT1') == '1' and not effective.get('STRATA_IQ_MT_MIN')
            assert effective.get('STRATA_DIRECT_SHADOW_FIRST') == (spec.get('env') or {}).get('STRATA_DIRECT_SHADOW_FIRST')
            meta['priority_gate'] = dict(pid=engine.pid, created=engine.create_time(), priority=engine.nice(), verified_at=time.time(), before_first_request=True)
            meta['load_s'] = round(time.time() - t0, 1)
            elog = d / 'engine.log'
            text = elog.read_text(encoding='utf-8', errors='replace')
            facts = ns.startup_facts(text)
            ok, why, strict = capacity_ok(arm, spec, facts)
            facts.update(capacity_ok=ok, capacity_detail=why, strict=strict)
            meta['startup'] = facts
            (d / 'startup.json').write_text(json.dumps(facts, indent=1))
            log('%s r%d READY in %.0fs %s' % (arm, rnd, meta['load_s'], json.dumps({k: facts[k] for k in ('slots', 'ram_budget_gib', 'locked_mib')})))
            if not ok:
                meta['status'] = 'ENV_BLOCKED_CAPACITY'
                meta['detail'] = why
                log('%s r%d ENV_BLOCKED_CAPACITY %s' % (arm, rnd, why))
            else:
                off = elog.stat().st_size
                prev_mb = prev_blobs = prev_ram = prev_skip = 0.0
                for pid in POINTS:
                    other = foreign_processes()
                    if other:
                        raise RuntimeError('live process gate: ' + json.dumps(other))
                    assert engine.is_running() and engine.nice() == psutil.ABOVE_NORMAL_PRIORITY_CLASS, 'priority/ownership changed'
                    body = make_body(pid, max_tokens)
                    t1 = time.time()
                    try:
                        resp = http_local('/v1/chat/completions', body)
                        err = None
                    except Exception as e:  # noqa
                        resp, err = None, repr(e)
                    wall = time.time() - t1
                    tail = ''
                    for _ in range(10):
                        time.sleep(0.5)
                        tail, newoff = read_from(elog, off)
                        if 'generated in' in tail and 'expert tiers' in tail:
                            time.sleep(0.5)
                            tail, newoff = read_from(elog, off)
                            break
                    off = newoff if tail else off
                    row = dict(block=index, round=rnd, arm=arm, pid=pid, wall_s=round(wall, 2), error=err)
                    row.update(parse_tail(tail))
                    if row.get('files_mb_cum') is not None:
                        row['ssd_mb'] = round(row['files_mb_cum'] - prev_mb, 1)
                        row['ssd_blobs'] = row['files_blobs_cum'] - prev_blobs
                        prev_mb, prev_blobs = row['files_mb_cum'], row['files_blobs_cum']
                    if row.get('ram_blobs_cum') is not None:
                        row['ram_blobs'] = row['ram_blobs_cum'] - prev_ram
                        prev_ram = row['ram_blobs_cum']
                    if row.get('tail_skip_cum') is not None:
                        row['tail_skip'] = row['tail_skip_cum'] - prev_skip
                        prev_skip = row['tail_skip_cum']
                    try:
                        mr = http_local('/metrics', timeout=10)['requests'][0]
                        row['m_file_mb'] = mr.get('file_mb')
                        row['m_file_blobs'] = mr.get('file_blobs')
                        row['m_ram_blobs'] = mr.get('ram_blobs')
                        row['m_hit_rate'] = mr.get('hit_rate')
                        row['m_decode_ms'] = mr.get('decode_ms')
                        row['m_decode_tok_s'] = mr.get('decode_tok_s')
                        row['m_prompt_ms'] = mr.get('prompt_ms')
                        row['m_out_tokens'] = mr.get('engine_generated')
                        row['m_prompt_tokens'] = mr.get('prompt_tokens')
                        row['m_reused'] = mr.get('reused')
                        row['m_drafts'] = [mr.get('drafts_offered'), mr.get('drafts_accepted')]
                    except Exception as e:  # noqa
                        row['m_error'] = repr(e)
                    if resp:
                        ch = resp['choices'][0]
                        msg = ch['message']
                        row.update(finish=ch['finish_reason'], completion_tokens=resp['usage']['completion_tokens'],
                                   prompt_tokens=resp['usage']['prompt_tokens'],
                                   cached_tokens=resp['usage'].get('prompt_tokens_details', {}).get('cached_tokens'),
                                   timings=resp.get('timings'))
                        (d / ('resp-%s.json' % pid)).write_text(json.dumps(resp, ensure_ascii=False, indent=1), encoding='utf-8')
                    (d / ('tail-%s.log' % pid)).write_text(tail, encoding='utf-8')
                    rows.append(row)
                    log('%s r%d %s tok=%s %.1f tok/s ssd=%s MB (blobs %s) ram_blobs=%s hit=%s err=%s' % (arm, rnd, pid, row.get('completion_tokens'),
                        row.get('m_decode_tok_s') or 0, row.get('m_file_mb'), row.get('m_file_blobs'), row.get('m_ram_blobs'), row.get('m_hit_rate'), err))
                meta['status'] = 'OK' if all(not r['error'] for r in rows) else 'INCOMPLETE'
    except Exception as e:  # noqa
        meta['status'] = meta['status'] if meta['status'] == 'ENV_BLOCKED_CAPACITY' else 'ERROR'
        meta['error'] = repr(e)
        log('%s r%d block error: %r' % (arm, rnd, e))
        if str(e).startswith('live process gate'):
            meta['status'] = 'PROCESS_GATE'
    finally:
        if srv is not None:
            kill_tree(srv)
    for _ in range(60):
        if not ns.engines():
            break
        time.sleep(1)
    if ns.engines():
        raise RuntimeError('engine left behind after block: %r' % ns.engines())
    meta['rows'] = len(rows)
    (d / 'results.json').write_text(json.dumps(rows, indent=1))
    (d / 'meta.json').write_text(json.dumps(meta, indent=2))
    time.sleep(3)
    return meta, rows


def schedule(arms, rounds):
    seq = []
    n = len(arms)
    for r in range(rounds):
        k = (r * max(1, n // 3)) % n if n > 1 else 0
        seq += [(r + 1, a) for a in arms[k:] + arms[:k]]
    return seq


def check_gate(d):
    """MISS_OVERLAP_CHECK block: any mismatch line or counter, or no split call at all, stops the campaign."""
    text = (d / 'engine.log').read_text(encoding='utf-8', errors='replace')
    bad_lines = [l for l in text.splitlines() if 'MISS_OVERLAP_CHECK MISMATCH' in l]
    prog = [l for l in text.splitlines() if l.startswith('MISS_OVERLAP ')]
    last = prog[-1] if prog else ''
    m = re.search(r'split_calls=(\d+).*check_rows=(\d+) check_mismatch_rows=(\d+)', last)
    info = dict(mismatch_lines=len(bad_lines), last_progress=last, split_calls=int(m.group(1)) if m else 0,
                check_rows=int(m.group(2)) if m else 0, check_bad=int(m.group(3)) if m else -1)
    (d / 'check_gate.json').write_text(json.dumps(info, indent=1))
    log('CHECK gate: ' + json.dumps(info))
    if bad_lines or info['check_bad'] != 0 or info['split_calls'] < 20 or info['check_rows'] < 100:
        raise RuntimeError('MISS_OVERLAP CHECK gate failed: ' + json.dumps(info))


def campaign(root, arms_file, arms, rounds, max_tokens, cap_min, pre_arm=None, pre_tokens=128):
    root.mkdir(exist_ok=False)
    ns.log.path = root / 'orchestrator.log'
    import faulthandler
    faulthandler.dump_traceback_later(600, repeat=True, file=open(root / 'stack.log', 'w'))
    assert os.environ.get('COMPUTERNAME', '').upper() == ns.HOSTNAME
    assert ns.sha(ns.EXE_C) == ns.EXE_C_SHA, 'control SHA mismatch'
    specs = json.loads(Path(arms_file).read_text())
    for a in arms + ([pre_arm] if pre_arm else []):
        assert a in specs, a
    seq = schedule(arms, rounds)
    log('run root %s arms %s rounds %d blocks %d' % (root, arms, rounds, len(seq)))
    log('order: ' + ' | '.join('r%d:%s' % s for s in seq))
    (root / 'arms.json').write_text(json.dumps({a: specs[a] for a in arms}, indent=1))
    blocks, allrows = [], []
    stopped = False
    restored = None
    try:
        stopped = True
        api_was_running = ns.stop_api(root)
        log('api_was_running=%s' % api_was_running)
        ns.ram_start_gate(root)
        t_start = time.time()
        if pre_arm:
            meta, rows = run_block(root, 0, 0, pre_arm, specs[pre_arm], pre_tokens)
            blocks.append(meta)
            allrows += rows
            if meta['status'] != 'OK':
                raise RuntimeError('pre-arm block failed: %s' % json.dumps(meta, default=str))
            check_gate(root / ('block-00-%s-r0' % pre_arm))
        for index, (rnd, arm) in enumerate(seq, 1):
            if time.time() - t_start > cap_min * 60:
                log('campaign cap reached; skipping remaining blocks')
                break
            meta, rows = run_block(root, index, rnd, arm, specs[arm], max_tokens)
            blocks.append(meta)
            allrows += rows
            (root / 'rows.json').write_text(json.dumps(allrows, indent=1))
            (root / 'blocks.json').write_text(json.dumps(blocks, indent=1))
            if meta['status'] == 'PROCESS_GATE':
                raise RuntimeError('process gate tripped; abort (restore follows)')
    except BaseException as e:  # noqa
        log('CAMPAIGN ABORTED: %r' % (e,))
        (root / 'abort.txt').write_text(repr(e))
        raise
    finally:
        log('finally: checking API health / restoring')
        try:
            healthy = bool(ns.http_json('/health', 5).get('loaded')) and bool(ns.api_pids())
        except Exception:  # noqa
            healthy = False
        restored = ns.restore_api(root) if (stopped or not healthy) else dict(restored=True, note='never stopped')
        (root / 'DONE.json').write_text(json.dumps(dict(finished=time.strftime('%Y-%m-%d %H:%M:%S'), api_restored=restored.get('restored'),
                                                        blocks=[(b['block'], b['arm'], b['status']) for b in blocks]), indent=2))
    return 0 if restored.get('restored') else 2


def main():
    argv = sys.argv[1:]
    def opt(name, default=None, cast=str):
        if name in argv:
            i = argv.index(name)
            v = cast(argv[i + 1])
            del argv[i:i + 2]
            return v
        return default
    arms_file = opt('--arms-file')
    arms = opt('--arms').split(',')
    rounds = opt('--rounds', 3, int)
    max_tokens = opt('--max-tokens', 512, int)
    cap_min = opt('--cap-min', 100, int)
    pre_arm = opt('--pre-arm', None)
    pre_tokens = opt('--pre-tokens', 128, int)
    for s in (signal.SIGTERM, getattr(signal, 'SIGBREAK', signal.SIGTERM)):
        signal.signal(s, lambda *_: (_ for _ in ()).throw(SystemExit(3)))
    return campaign(Path(argv[0]), arms_file, arms, rounds, max_tokens, cap_min, pre_arm, pre_tokens)


if __name__ == '__main__':
    sys.exit(main())
