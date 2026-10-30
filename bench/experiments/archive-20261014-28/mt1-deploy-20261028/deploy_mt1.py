"""2026-10-28 MT1 deployment (user-authorized): live API S2K -> S2K + STRATA_IQ3S_MT1=1.

New files only (originals untouched): config server-task020-8080-v0142-s2k-mt1.json (copy of the S2K config + one env
key + its own engine log), launcher start_task020_api_s2k_mt1.ps1 (copy of the S2K launcher pointing at the new config).
Then: process gate -> idle -> stop the verified API stack (watcher stays) -> task action -> new launcher -> start ->
verify. On failure preserve the receipt and stop; no automatic fallback or rollback.
    python deploy_mt1.py <root>
"""
import json
import os
from pathlib import Path
import sys
import time
import traceback
import urllib.request

import psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'harness'))
import next_steps_ab_20261018 as ns  # noqa: E402

TASK = 'Strata-Task020-API'
TOOLS = Path(r'C:\Users\User\Strata-Adrian-control\tools')
S2K_LAUNCHER = TOOLS / 'start_task020_api_s2k.ps1'
S2K_LAUNCHER_SHA = '50B9D745E980409E397FCBF18A94B87AC97B49F56DD12B5F4CA80A0AD60B42CB'
NEW_LAUNCHER = TOOLS / 'start_task020_api_s2k_mt1.ps1'
S2K_CONFIG = ns.CONFIG
NEW_CONFIG = S2K_CONFIG.with_name('server-task020-8080-v0142-s2k-mt1.json')
NEW_LOG = r'C:\Users\User\Strata-Adrian-control\runs\miss-overlap-20261027\s2k-mt1-api.engine.log'
S2K_SHA = ns.EXE_C_SHA
ABOVE_NORMAL = getattr(psutil, 'ABOVE_NORMAL_PRIORITY_CLASS', None)
REQ_DIR = Path(r'C:\Users\User\Strata-Adrian-control\runs\overnight-20261020-inputs\requests')
rec = {}


def ps(cmd):
    return ns.ps("$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; " + cmd, check=True).stdout.strip()


def set_action(script):
    arg = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File %s' % script
    return ps("$a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '%s'; Set-ScheduledTask -TaskName '%s' -Action $a | Out-Null; "
              "$t = Get-ScheduledTask -TaskName '%s'; $t.Actions[0].Arguments + ' | prio=' + $t.Settings.Priority" % (arg, TASK, TASK))


def stop_stack():
    """Stop the verified API stack, whichever launcher/config is live (S2K or MT1); the --watch process stays."""
    # Recheck all relevant processes immediately before stopping the authorized S2K API.
    api = ns.api_pids()
    allowed = {pid for _, pid, _ in api} | set(ns.watch_pids())
    bad = [p for p in ns.processes() if p['pid'] not in allowed]
    assert not bad, 'PROCESS_GATE_STOP: %r' % bad
    assert len([p for p in api if p[0] == 0]) == 1, 'expected one S2K engine'
    live = ns.http_json('/metrics')['live']
    assert live['state'] == 'idle' and live.get('queued', 0) == 0, 'API no longer idle'
    frozen = []
    for _, pid, cl in api:
        p = psutil.Process(pid)
        assert ' '.join(p.cmdline()).lower() == cl.lower()
        if p.name().lower() == 'strata.exe':
            assert ns.sha(p.exe()) == S2K_SHA
        frozen.append((pid, p.create_time(), p.name(), cl))
    rec['pre_stop_processes'] = frozen
    rec['stop_started_at'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    (Path(sys.argv[1]) / 'deploy_receipt.json').write_text(json.dumps(rec, indent=2))
    ps('Stop-ScheduledTask -TaskName %s' % TASK)
    time.sleep(2)
    killed = []
    for pid, created, name, cl in frozen:
        try:
            p = psutil.Process(pid)
            assert p.create_time() == created and p.name() == name
            assert ' '.join(p.cmdline()).lower() == cl.lower(), 'PID identity changed'
            p.terminate()
            killed.append((pid, name, cl))
        except psutil.NoSuchProcess:
            pass
    time.sleep(3)
    assert not ns.engines(), 'engine remains after authorized stop'
    remaining = [p for p in ns.processes() if p['pid'] not in set(ns.watch_pids())]
    assert not remaining, 'unexpected process after stop: %r' % remaining
    return killed


def wait_health(limit=420):
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            if ns.http_json('/health', 5).get('loaded'):
                return True
        except Exception:  # noqa
            pass
        time.sleep(4)
    return False


def verify(expect_mt1, log_path):
    out = {}
    try:
        out['health'] = ns.http_json('/health', 8)
    except Exception as e:  # noqa
        out['health_error'] = repr(e)
    engs = []
    for p in psutil.process_iter(['pid', 'name']):
        if (p.info['name'] or '').lower() != 'strata.exe':
            continue
        e = dict(pid=p.pid)
        try:
            e['sha'] = ns.sha(p.exe())
            e['serve'] = '--serve' in (p.cmdline() or [])
            e['above_normal'] = p.nice() == ABOVE_NORMAL
            ev = p.environ()
            e['env'] = {k: ev.get(k) for k in ('STRATA_MISS_OVERLAP', 'STRATA_MISS_OVERLAP_SPIN_US', 'STRATA_IQ3S_MT1', 'STRATA_IQ_MT_MIN')}
        except Exception as ex:  # noqa
            e['error'] = repr(ex)
        engs.append(e)
    out['engines'] = engs
    try:
        text = Path(log_path).read_text(encoding='utf-8', errors='replace')
        seg = text[text.rfind('engine started:'):]
        f = ns.startup_facts(seg)
        out['log'] = {k: f.get(k) for k in ('slots', 'ram_budget_gib', 'locked_mib')}
    except Exception as e:  # noqa
        out['log_error'] = repr(e)
    lg = out.get('log') or {}

    def good(e):
        env = e.get('env') or {}
        return (e.get('sha') == S2K_SHA and e.get('serve') and e.get('above_normal') and env.get('STRATA_MISS_OVERLAP') == '1'
                and env.get('STRATA_MISS_OVERLAP_SPIN_US') == '2000' and not env.get('STRATA_IQ_MT_MIN')
                and (env.get('STRATA_IQ3S_MT1') == '1') == expect_mt1)
    out['checks'] = dict(loaded=bool((out.get('health') or {}).get('loaded')), one_good_engine=len(engs) == 1 and good(engs[0]),
                         slots=str(lg.get('slots')) == '3153', ram=lg.get('ram_budget_gib') == '20.00', locked=str(lg.get('locked_mib')) == '20479')
    out['verified'] = all(out['checks'].values())
    return out


def smoke():
    res = []
    for pid in ('p01', 'p02', 'p03'):
        body = json.loads((REQ_DIR / (pid + '.json')).read_text(encoding='utf-8'))
        body['max_tokens'] = 128
        req = urllib.request.Request(ns.API_URL + '/v1/chat/completions', data=json.dumps(body).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                j = json.load(r)
            msg = j['choices'][0]['message']
            res.append(dict(pid=pid, ok=True, s=round(time.time() - t0, 1), finish=j['choices'][0].get('finish_reason'),
                            completion_tokens=(j.get('usage') or {}).get('completion_tokens'),
                            content_head=(msg.get('content') or '')[:80], has_tool_calls=bool(msg.get('tool_calls'))))
        except Exception as e:  # noqa
            res.append(dict(pid=pid, ok=False, error=repr(e)))
    return res


def main():
    root = Path(sys.argv[1])
    root.mkdir(exist_ok=False)
    save = lambda: (root / 'deploy_receipt.json').write_text(json.dumps(rec, indent=2, default=str))  # noqa: E731
    assert os.environ.get('COMPUTERNAME', '').upper() == ns.HOSTNAME
    assert ns.sha(ns.EXE_C) == S2K_SHA
    assert ns.sha(S2K_CONFIG) == ns.CONFIG_SHA, 'S2K config changed'
    assert ns.sha(S2K_LAUNCHER) == S2K_LAUNCHER_SHA, 'S2K launcher changed'
    assert not NEW_CONFIG.exists() and not NEW_LAUNCHER.exists(), 'new files already exist'
    rec['started_at'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    rec['authorization'] = 'User explicitly requested MT1 deployment and current-best update in this chat.'
    rec['baseline'] = verify(False, json.loads(S2K_CONFIG.read_text(encoding='utf-8-sig'))['log'])
    assert rec['baseline']['verified'], 'baseline identity/capacity mismatch'
    (root / 'scheduled_task.before.xml').write_text(ps("Export-ScheduledTask -TaskName '%s'" % TASK), encoding='utf-8')
    (root / 's2k-config.before.json').write_bytes(S2K_CONFIG.read_bytes())
    (root / 's2k-launcher.before.ps1').write_bytes(S2K_LAUNCHER.read_bytes())
    # process gate: only the verified API stack + watcher
    api = {p[1] for p in ns.api_pids()}
    watch = set(ns.watch_pids())
    rec['api_pids'] = sorted(api)
    rec['watch_pids'] = sorted(watch)
    rec['unclassified'] = [p for p in ns.processes() if p['pid'] not in api and p['pid'] not in watch]
    if rec['unclassified'] or not any(k == 0 for k, _, _ in ns.api_pids()):
        rec['result'] = 'PROCESS_GATE_STOP'
        save()
        sys.exit(3)
    # idle
    for _ in range(90):
        live = ns.http_json('/metrics')['live']
        if live['state'] == 'idle' and live.get('queued', 0) == 0:
            break
        time.sleep(10)
    else:
        rec['result'] = 'API_NEVER_IDLE'
        save()
        sys.exit(4)
    # new files
    cfg = json.loads(S2K_CONFIG.read_text(encoding='utf-8-sig'))
    assert 'STRATA_IQ3S_MT1' not in cfg['env'] and 'STRATA_IQ_MT_MIN' not in cfg['env']
    cfg['env']['STRATA_IQ3S_MT1'] = '1'
    cfg['log'] = NEW_LOG
    NEW_CONFIG.write_text(json.dumps(cfg, indent=4), encoding='utf-8')
    lb = S2K_LAUNCHER.read_bytes()
    assert lb.count(S2K_CONFIG.name.encode()) == 1
    NEW_LAUNCHER.write_bytes(lb.replace(S2K_CONFIG.name.encode(), NEW_CONFIG.name.encode()))
    rec['new_config'] = dict(path=str(NEW_CONFIG), sha=ns.sha(NEW_CONFIG))
    rec['new_launcher'] = dict(path=str(NEW_LAUNCHER), sha=ns.sha(NEW_LAUNCHER))
    save()
    ok = False
    try:
        rec['stopped'] = stop_stack()
        rec['action_set'] = set_action(NEW_LAUNCHER)
        rec['start'] = ps("Start-ScheduledTask -TaskName '%s'; 'started'" % TASK)
        if wait_health():
            time.sleep(10)
            for i in range(4):
                rec['verify_mt1'] = verify(True, NEW_LOG)
                if rec['verify_mt1']['verified']:
                    break
                time.sleep(15)
            if rec['verify_mt1']['verified']:
                rec['smoke'] = smoke()
                ok = all(s['ok'] for s in rec['smoke'])
        rec['result'] = 'DEPLOYED_MT1' if ok else 'MT1_FAILED'
    finally:
        rec['automatic_fallback'] = False
        rec['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
        rec['old_config_unchanged'] = ns.sha(S2K_CONFIG) == ns.CONFIG_SHA
        rec['old_launcher_unchanged'] = ns.sha(S2K_LAUNCHER) == S2K_LAUNCHER_SHA
        rec['task_after'] = ps("$t=Get-ScheduledTask -TaskName '%s'; [pscustomobject]@{state=[string]$t.State;execute=$t.Actions[0].Execute;arguments=$t.Actions[0].Arguments;priority=$t.Settings.Priority} | ConvertTo-Json -Compress" % TASK)
        save()
    if not ok:
        raise RuntimeError('MT1 deployment verification failed; see durable receipt')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        rec['error'] = traceback.format_exc()
        rec.setdefault('result', 'ERROR')
        root = Path(sys.argv[1])
        if root.exists():
            (root / 'deploy_receipt.json').write_text(json.dumps(rec, indent=2, default=str))
        raise
