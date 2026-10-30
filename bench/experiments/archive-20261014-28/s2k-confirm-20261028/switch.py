"""Cut the live API over to the S2K config (task action -> start_task020_api_s2k.ps1). Auto-rollback to the original launcher on failure.
Stops only the verified API stack (ns.stop_api); the memory-restore watcher stays running."""
import json, os, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, r'C:\Users\User\Strata-Adrian-control\tools')
import next_steps_ab_20261018 as ns  # noqa: E402

TASK = 'Strata-Task020-API'
TOOLS = r'C:\Users\User\Strata-Adrian-control\tools'
ORIG = TOOLS + r'\start_task020_api.ps1'
NEW = TOOLS + r'\start_task020_api_s2k.ps1'
CAND_LOG = Path(r'C:\Users\User\Strata-Adrian-control\runs\miss-overlap-20261027\s2k-api.engine.log')
root = Path(r'C:\Users\User\Strata-Adrian-control\runs\s2k-deploy-20261028')
rec = {}


def ps(cmd):
    r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', cmd], capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()


def set_action(script):
    arg = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File %s' % script
    return ps("$a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '%s'; Set-ScheduledTask -TaskName '%s' -Action $a | Out-Null; "
              "$t = Get-ScheduledTask -TaskName '%s'; $t.Actions[0].Arguments + ' | prio=' + $t.Settings.Priority" % (arg, TASK, TASK))


def wait_health(limit=420):
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            h = ns.http_json('/health', 5)
            if h.get('loaded'):
                return True
        except Exception:  # noqa
            pass
        time.sleep(4)
    return False


assert os.environ.get('COMPUTERNAME', '').upper() == ns.HOSTNAME
assert ns.sha(ns.EXE_C) == ns.EXE_C_SHA
assert ns.sha(Path(NEW)) .upper() == '50B9D745E980409E397FCBF18A94B87AC97B49F56DD12B5F4CA80A0AD60B42CB'
api = {p[1] for p in ns.api_pids()}
watch = set(ns.watch_pids()) if hasattr(ns, 'watch_pids') else set()
watch = {w[1] if isinstance(w, (tuple, list)) else (w['pid'] if isinstance(w, dict) else w) for w in watch}
unclassified = [p for p in ns.processes() if p['pid'] not in api and p['pid'] not in watch]
rec['api_pids'] = sorted(api)
rec['watch_pids'] = sorted(watch)
rec['unclassified'] = unclassified
if unclassified or not api:
    rec['result'] = 'PROCESS_GATE_STOP'
    (root / 'switch_receipt.json').write_text(json.dumps(rec, indent=2, default=str))
    print(json.dumps(rec, indent=2, default=str))
    sys.exit(3)
ok = False
try:
    rec['stopped'] = ns.stop_api(root)
    rec['action_set'] = set_action(NEW)
    rec['start'] = ps("Start-ScheduledTask -TaskName '%s'; 'started'" % TASK)
    ok = wait_health()
    rec['healthy_on_s2k'] = ok
finally:
    if not ok:
        rec['rollback'] = True
        try:
            for p in ns.api_pids():
                pass
            ns.stop_api(root)
        except Exception as e:  # noqa
            rec['rollback_stop_error'] = repr(e)
        rec['action_restored'] = set_action(ORIG)
        ps("Start-ScheduledTask -TaskName '%s'" % TASK)
        rec['healthy_after_rollback'] = wait_health()
    (root / 'switch_receipt.json').write_text(json.dumps(rec, indent=2, default=str))
print(json.dumps(rec, indent=2, default=str))
