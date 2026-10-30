"""Task027 continuation (LUNA-20261012-027): multi-arm fresh-engine A/B campaign, 2026-10-18.

Arms (all greedy 1024-token neuro, fresh engine per block, 1 discarded warm-up + 3 measured):
  C      control: current best binary + exact live config args/env (+ STRATA_ROUTE_TAIL_SKIP=7, as serve does)
  A9/A11/A13/A15  control with --pool-affinity auto and --pool-workers N (control: affinity all, 9 workers).
         On this hybrid i5-12600KF (6 P-cores/12 threads: logical 0-11 as pairs; 4 E-cores: logical 12-15) auto orders the
         workers P primaries (host takes 0) -> P SMT siblings -> E-cores:  2,4,6,8,10, 1,3,5,7,9,11, 12,13,14,15
         so A9 = 5 primaries + 4 siblings (no E), A11 = all 11 P threads, A13 = + 2 E, A15 = every logical processor.
         (The first campaign's --pool-workers 11/13/15 with --pool-affinity all only left the surplus workers
         unpinned over the same 9 CPUs; the SMT siblings were never used. Those arms are retired.)
  SAUTO  control with --expert-cache auto   (S3000 retired: --expert-cache 3000 is a budget of 3000 LARGEST blobs and the
         profile-sized cache still filled all free VRAM = 3153 slots, i.e. identical to C)
  ML8/ML32     pure mainline 0.1.45 build, STRATA_RAM_ADAPT=8 / 32 (no private RAM_LRU); mainline locks 20478 MiB
  TIE    control source + untouched-slot eviction tie ordered by profile rank
Rotating order, 3 rounds, C every round.
Start state: the API may already be stopped (api_was_running=false); then nothing is stopped, the gates must be clean,
and `finally` still starts the API at the end. Available RAM and heavy processes at start are logged only (no RAM gate).

Runs on the remote desktop under a scheduled task (wrapper: run_next_steps_ab_20261018.ps1). It stops the live
API (only after /metrics reports idle, only verified API PIDs), runs the arms, and in `finally` ALWAYS stops its
own engines and restarts Strata-Task020-API and waits for /health loaded=true.

  python next_steps_ab_20261018.py <run_root>            full run
  python next_steps_ab_20261018.py --dry-run             no engine, no API: validation only
  python next_steps_ab_20261018.py --parse-test <stderr> [arm]  parse one engine stderr with the real parsers + gates
Optional: --arms C,A11,...   --rounds 3
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import statistics
import subprocess
import sys
import threading
import time
import urllib.request

import psutil

CONTROL_ROOT = Path(r'C:\Users\User\Strata-Adrian-control')
CONFIG = Path(r'C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\server-task020-8080-v0142.json')
CONFIG_NAME = 'server-task020-8080-v0142.json'
EXE_C = CONTROL_ROOT / r'runs\ram-lru-20261013\build\strata.exe'
EXE_C_SHA = '366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2'
EXE_TIE = CONTROL_ROOT / r'runs\tie-order-20261018\build\strata.exe'
EXE_TIE_SHA = 'EC89B62700103DFCB0524BD7B632A3ACE9C3447BB7152ED0B47283A5D062CB01'
EXE_ML = CONTROL_ROOT / r'runs\mainline-build-20261018\build\strata.exe'
EXE_ML_SHA = '14EE0A85DE997EC363DDA371A7BB218DB305FDBB1940A1E90DA8AA83F8D52AF9'
PROMPT = Path(r'C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens')
PROMPT_SHA = '9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA'
API_TASK = 'Strata-Task020-API'
API_URL = 'http://<desktop-tailscale-ip>:8080'
HOSTNAME = 'DESKTOP-LKMLUPC'
LAYERS = 48
MEASURED = 3
BLOCK_CAP_S = 10 * 60
CAMPAIGN_CAP_S = 130 * 60          # no new block starts after this; restore always runs
EST_BLOCK_S = 150                  # ~25 s start + warm-up ~50 s + 3 x ~22 s + exit (pcie A/B: 6 blocks ~13 min)
EST_OVERHEAD_S = 6 * 60            # stop API + gates + restore
IDLE_WAIT_S = 15 * 60
EXPECT_RAM = '20.00'
EXPECT_LOCK = '20479'
HEAVY_TOP_N = 8
HOST_LINE = ', the host thread on 0'

def pool_expect(n, cpus):
    return '%d pool workers on logical processors %s%s' % (n, cpus, HOST_LINE)


POOL9_ALL = pool_expect(9, '2,4,6,8,10,12,13,14,15')
AUTO_ORDER = [2, 4, 6, 8, 10, 1, 3, 5, 7, 9, 11, 12, 13, 14, 15]    # host on 0; derived from pool.cpp (auto, hybrid)


# name: (exe, expected sha, args modifier, env modifier, allowed slot range, family, allowed locked MiB, pool-line prefix)
def _arm(exe, sha, args=None, env=None, slots=(3153, 3153), family='ours', locks=(EXPECT_LOCK,), pool=POOL9_ALL):
    return dict(exe=exe, sha=sha, args=args or {}, env=env or {}, slots=slots, family=family, locks=tuple(locks), pool=pool)


def _auto(n):
    return _arm(EXE_C, EXE_C_SHA, args={'--pool-workers': str(n), '--pool-affinity': 'auto'},
                pool=pool_expect(n, ','.join(str(c) for c in AUTO_ORDER[:n])))


# mainline 0.1.45 rounds the lock to 20478 MiB where our build reports 20479 (same 20.00 GiB budget): both accepted for ML only
ML_LOCKS = ('20478', '20479')
ARMS = {
    'C': _arm(EXE_C, EXE_C_SHA),
    'A9': _auto(9),
    'A11': _auto(11),
    'A13': _auto(13),
    'A15': _auto(15),
    'SAUTO': _arm(EXE_C, EXE_C_SHA, args={'--expert-cache': 'auto'}, slots=(1500, 3153)),
    'ML8': _arm(EXE_ML, EXE_ML_SHA, env={'STRATA_RAM_ADAPT': '8', '-STRATA_RAM_LRU': '', '-STRATA_RAM_LRU_CHECK': ''},
                slots=(3100, 3200), family='mainline', locks=ML_LOCKS),
    'ML32': _arm(EXE_ML, EXE_ML_SHA, env={'STRATA_RAM_ADAPT': '32', '-STRATA_RAM_LRU': '', '-STRATA_RAM_LRU_CHECK': ''},
                 slots=(3100, 3200), family='mainline', locks=ML_LOCKS),
    'TIE': _arm(EXE_TIE, EXE_TIE_SHA),
}
DEFAULT_ORDER = ['C', 'A9', 'A11', 'A13', 'A15', 'SAUTO', 'ML8', 'ML32', 'TIE']

STARTUP_PATTERNS = dict(
    slots=r'expert cache (\d+) slots',
    ram_budget_gib=r'RAM budget ([\d.]+) GiB',
    locked_mib=r'locked (\d+) MiB via working-set minimum \+ VirtualLock',
    resident_gib=r'complement ready: resident ([\d.]+) GiB',
    pinned_gib=r'pinned ([\d.]+) GiB',
    pool_line=r'(\d+ pool workers on logical processors [^\n]+)',
    tail_skip_line=r'(STRATA_ROUTE_TAIL_SKIP=\d+ is ON[^\n]*)',
    engine_version=r'session is up \(engine ([\d.]+)\)',
    ram_lru_line=r'(RAM_LRU enabled[^\n]*)',
    vram_free_line=r'(\d+ MiB of VRAM free with everything loaded[^\n]*)',
    pcie_line=r'(PCIe probe: [^\n]+)',
    hybrid_line=r'(hybrid CPU detected[^\n]*)',
)


# ---------------------------------------------------------------- helpers
def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


class Log:
    def __init__(self, path=None):
        self.path = path

    def __call__(self, msg):
        line = time.strftime('%Y-%m-%d %H:%M:%S ') + msg
        print(line, flush=True)
        if self.path:
            with open(self.path, 'a', encoding='utf-8') as f:
                f.write(line + '\n')


log = Log()


def http_json(path, timeout=10):
    with urllib.request.urlopen(API_URL + path, timeout=timeout) as r:
        return json.load(r)


def ps(command, check=True):
    return subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', command], check=check,
                          capture_output=True, text=True)


def processes():
    """Same process gate as run_task027_ram_lru.py: anything that can disturb RAM/GPU, except this runner."""
    found = []
    parents = {p.pid for p in psutil.Process().parents()}
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        if p.pid == os.getpid() or p.pid in parents:
            continue
        if re.search('strata|llama|python|cmake|ninja|nvcc|msbuild|cl.exe', p.info['name'] or '', re.I):
            found.append(p.info)
    return found


def engines(descendants_only=False):
    out = []
    for p in psutil.process_iter(['pid', 'name']):
        if (p.info['name'] or '').lower() == 'strata.exe':
            out.append(p.info['pid'])
    return out


def api_pids():
    """Verified API processes by command line (never anything else)."""
    live_exe = str(EXE_C).lower()
    matched = []
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        name = (p.info['name'] or '').lower()
        cl = ' '.join(p.info['cmdline'] or [])
        low = cl.lower()
        if name == 'strata.exe' and live_exe in low and '--serve' in low and 'iq3_xxs' in low:
            matched.append((0, p.pid, cl))
        elif name.startswith('python') and CONFIG_NAME.lower() in low and ('serve.server' in low or 'strata_memory_policy.py' in low):
            matched.append((1, p.pid, cl))
        elif name in ('powershell.exe', 'pwsh.exe') and 'start_task020_api.ps1' in low:
            matched.append((2, p.pid, cl))
    return sorted(matched)


def watch_pids():
    out = []
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        cl = ' '.join(p.info['cmdline'] or [])
        if (p.info['name'] or '').lower().startswith('python') and 'strata_memory_policy.py' in cl and '--watch' in cl:
            out.append(p.info['pid'])
    return out


def heavy_processes(top=HEAVY_TOP_N):
    """Top working-set processes that are NOT Strata/this runner. Logged only, never killed."""
    out = []
    parents = {p.pid for p in psutil.Process().parents()}
    for p in psutil.process_iter(['pid', 'name', 'memory_info']):
        if p.pid == os.getpid() or p.pid in parents:
            continue
        mi = p.info.get('memory_info')
        if mi is None:
            continue
        out.append(dict(pid=p.pid, name=p.info['name'], ws_mib=round(getattr(mi, 'wset', mi.rss) / 2**20)))
    return sorted(out, key=lambda x: -x['ws_mib'])[:top]


def log_heavy(tag, path=None):
    vm = psutil.virtual_memory()
    hv = heavy_processes()
    log('%s: available RAM %.2f GiB; heaviest other processes (logged, not touched): %s' % (
        tag, vm.available / 2**30, ', '.join('%s[%d] %d MiB' % (h['name'], h['pid'], h['ws_mib']) for h in hv)))
    if path:
        Path(path).write_text(json.dumps(dict(available_gib=round(vm.available / 2**30, 2), heavy=hv), indent=2))
    return hv


def idle_start_gate(root):
    """API not running at start: nothing to stop. Proceed only if nothing API/Strata-related exists and the gate is clean."""
    problems = []
    if api_pids():
        problems.append('api processes %r' % (api_pids(),))
    if engines():
        problems.append('strata.exe %r' % (engines(),))
    if watch_pids():
        problems.append('watch %r' % (watch_pids(),))
    try:
        h = http_json('/health', 5)
        problems.append('API /health answered: %r' % (h,))
    except Exception:  # noqa
        pass
    if problems:
        raise RuntimeError('api_was_running=false path but state is not clean: ' + '; '.join(problems))
    t0 = time.time()
    while time.time() - t0 < 60 and processes():
        time.sleep(2)
    left = processes()
    (root / 'process-gate-after-stop.json').write_text(json.dumps(left, indent=2))
    if left:
        raise RuntimeError('process gate not clean (API already stopped): %s' % json.dumps(left))
    log('API was NOT running at start; no API/strata.exe/watch processes; process gate clean')


def ram_start_gate(root):
    """Observation only: log available RAM and heavy processes; never aborts."""
    avail = psutil.virtual_memory().available / 2**30
    log('start observation: available RAM %.2f GiB (logged only, no gate)' % avail)
    log_heavy('start observation: available %.2f GiB' % avail, root / 'heavy-start.json')


def stop_api(root):
    """Returns api_was_running."""
    if not api_pids():
        (root / 'api-before.json').write_text(json.dumps(dict(api_was_running=False, api_processes=[]), indent=2))
        idle_start_gate(root)
        return False
    for _ in range(IDLE_WAIT_S // 10):
        try:
            state = http_json('/metrics')['live']['state']
        except Exception as e:  # noqa
            raise RuntimeError('API metrics unreadable before stop: %r' % (e,))
        if state == 'idle':
            break
        log('API busy (live.state=%s); waiting for idle before stopping it' % state)
        time.sleep(10)
    else:
        raise RuntimeError('API never idle within %d s; nothing was stopped' % IDLE_WAIT_S)
    m = http_json('/metrics')
    (root / 'api-before.json').write_text(json.dumps(dict(api_was_running=True,
        live=m.get('live'), engine={k: m['engine'].get(k) for k in ('expert_slots', 'arena_mib', 'pool_workers', 'pcie_frac', 'version')},
        api_processes=[(k, pid, cl) for k, pid, cl in api_pids()]), indent=2))
    before = api_pids()
    if not any(k == 0 for k, _, _ in before):
        raise RuntimeError('verified API strata.exe not found; refusing to proceed')
    log('stopping API: Stop-ScheduledTask %s' % API_TASK)
    ps('Stop-ScheduledTask -TaskName %s' % API_TASK)
    time.sleep(2)
    for _ in range(3):
        for _, pid, cl in api_pids():
            try:
                log('terminate verified API pid %d: %s' % (pid, cl[:140]))
                psutil.Process(pid).terminate()
            except psutil.NoSuchProcess:
                pass
        time.sleep(3)
        if not api_pids():
            break
    if api_pids():
        raise RuntimeError('API processes survived terminate: %r' % api_pids())
    t0 = time.time()
    while time.time() - t0 < 180:
        if not watch_pids() and not processes():
            break
        time.sleep(2)
    left = processes()
    (root / 'process-gate-after-stop.json').write_text(json.dumps(left, indent=2))
    if left:
        raise RuntimeError('process gate not clean after API stop: %s' % json.dumps(left))
    log('process gate clean; available RAM %.2f GiB' % (psutil.virtual_memory().available / 2**30))
    return True


def restore_api(root):
    result = dict(started=time.strftime('%Y-%m-%d %H:%M:%S'))
    try:
        own = psutil.Process().children(recursive=True)
        for c in own:
            if (c.name() or '').lower() == 'strata.exe':
                log('restore: terminating own engine pid %d' % c.pid)
                c.terminate()
        t0 = time.time()
        while time.time() - t0 < 90 and engines():
            time.sleep(1)
        result['strata_exe_left_before_start'] = engines()
        if result['strata_exe_left_before_start']:
            log('WARNING: strata.exe still present before API start (not ours to kill): %r' % result['strata_exe_left_before_start'])
        ps('Start-ScheduledTask -TaskName %s' % API_TASK, check=False)
        result['start_issued'] = time.strftime('%H:%M:%S')
        t0 = time.time()
        while time.time() - t0 < 600:
            try:
                h = http_json('/health', 5)
                if h.get('loaded'):
                    result['health'] = h
                    result['loaded_after_s'] = round(time.time() - t0, 1)
                    break
            except Exception:  # noqa
                pass
            time.sleep(3)
        else:
            result['error'] = 'health loaded=true not reached within 600 s'
        try:
            m = http_json('/metrics')
            result['metrics'] = {k: m['engine'].get(k) for k in ('expert_slots', 'arena_mib', 'pool_workers', 'pcie_frac')}
            result['live_state'] = m.get('live', {}).get('state')
        except Exception as e:  # noqa
            result['metrics_error'] = repr(e)
        result['api_processes_after'] = [(k, pid) for k, pid, _ in api_pids()]
        result['binary_sha256_after'] = sha(EXE_C)
        result['restored'] = bool(result.get('health', {}).get('loaded'))
    except Exception as e:  # noqa
        result['exception'] = repr(e)
        result['restored'] = False
    result['finished'] = time.strftime('%Y-%m-%d %H:%M:%S')
    (root / 'restore.json').write_text(json.dumps(result, indent=2, default=str))
    with open(root / 'restore.log', 'a', encoding='utf-8') as f:
        f.write(json.dumps(result, default=str) + '\n')
    log('API RESTORE %s: %s' % ('OK' if result.get('restored') else 'FAILED', json.dumps(result, default=str)))
    return result


# ---------------------------------------------------------------- parsing
def startup_facts(text):
    facts = {}
    for k, pat in STARTUP_PATTERNS.items():
        m = re.search(pat, text)
        facts[k] = m.group(1) if m else None
    return facts


def _f(pattern, text):
    m = re.search(pattern, text)
    return float(m.group(1)) if m else None


def parse_request(tail):
    """Decode rate ONLY from the 'N generated in X ms (R tok/s)' segment; never the prefill rate."""
    out = {}
    g = re.search(r'\b(\d+)\s+generated in\s+([\d.]+)\s+ms\s+\(([\d.]+)\s+tok/s\)', tail)
    out['gen_found'] = bool(g)
    if g:
        out['tokens'] = int(g.group(1))
        out['decode_ms'] = float(g.group(2))
        out['decode_tok_s_text'] = float(g.group(3))
        out['decode_tok_s'] = round(out['tokens'] / out['decode_ms'] * 1000, 2)
    p = re.search(r'prompt (\d+) tokens = (\d+) reused \+ (\d+) read in ([\d.]+) ms', tail)
    if p:
        out.update(prompt_tokens=int(p.group(1)), reused=int(p.group(2)), read=int(p.group(3)), prefill_ms=float(p.group(4)))
    d = re.search(r'decode timing:[^\n]*', tail)
    line = d.group(0) if d else ''
    out['timing_line'] = line.strip() or None
    out['windows'] = _f(r'decode timing: (\d+) windows', line)
    out['tokens_per_window'] = _f(r'([\d.]+) tokens/window', line)
    out['ms_window'] = _f(r'([\d.]+) ms/window', line)
    out['verify_ms'] = _f(r'verify ([\d.]+)', line)
    out['gpu_wait_ms'] = _f(r'GPU-reach wait ([\d.]+)', line)
    out['host_ms'] = _f(r'per-layer host ([\d.]+)', line)
    out['jobs_ms'] = _f(r'jobs ([\d.]+)', line)
    out['cpu_ms'] = _f(r'CPU ([\d.]+)\]', line)
    out['draft_ms'] = _f(r'draft ([\d.]+)', line)
    out['cpu_experts_per_layer_window'] = _f(r'CPU experts ([\d.]+)', line)
    out['cpu_entries_per_layer_window'] = _f(r'CPU experts [\d.]+ \(([\d.]+) entries', line)
    out['vram_hits_per_layer_window'] = _f(r'VRAM hits ([\d.]+)', line)
    out['pcie_per_layer_window'] = _f(r'PCIe ([\d.]+)', line)
    if out['cpu_ms'] and out['cpu_experts_per_layer_window']:
        # CPU ms/window is summed over layers: per-expert CPU time = CPU ms / (experts per layer-window x layers)
        out['cpu_us_per_expert'] = round(out['cpu_ms'] * 1000 / (out['cpu_experts_per_layer_window'] * LAYERS), 1)
        if out['cpu_entries_per_layer_window']:
            out['cpu_us_per_entry'] = round(out['cpu_ms'] * 1000 / (out['cpu_entries_per_layer_window'] * LAYERS), 1)
    out['cache_hit_rate'] = _f(r'decode expert cache hit rate: ([\d.]+)%', tail)
    out['drafts'] = (re.search(r'drafts accepted (\d+ of \d+)', tail) or [None, None])[1]
    out['adapt_lines'] = [l.strip() for l in tail.splitlines() if re.search(r'RAM_ADAPT|ram.adapt|promot', l, re.I)][-3:]
    return out


def parse_done(line):
    f = line.split()
    out = dict(done=line.strip())
    try:
        out.update(done_tokens=int(f[1]), done_decode_ms=float(f[4]), file_blobs=int(f[-4]), file_mb=float(f[-3]))
        out['done_tok_s'] = round(out['done_tokens'] / out['done_decode_ms'] * 1000, 2)
    except (ValueError, IndexError):
        out['done_parse_error'] = True
    return out


# ---------------------------------------------------------------- arm construction
def build_command(arm, cfg):
    spec = ARMS[arm]
    args = list(cfg['args'])
    for flag, value in spec['args'].items():
        assert args.count(flag) == 1, flag
        args[args.index(flag) + 1] = value
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('STRATA_')}
    cfg_env = dict(cfg['env'])
    cfg_env['STRATA_ROUTE_TAIL_SKIP'] = '7'
    env.update(cfg_env)
    for k, v in spec['env'].items():
        if k.startswith('-'):
            env.pop(k[1:], None)
        else:
            env[k] = v
    assert 'STRATA_VERIFY_PROFILE' not in env
    return ['--serve'] + args, env


def capacity_verdict(arm, facts):
    lo, hi = ARMS[arm]['slots']
    try:
        slots = int(facts['slots'])
    except (TypeError, ValueError):
        return False, 'no slots evidence'
    problems = []
    if not lo <= slots <= hi:
        problems.append('slots %d outside [%d,%d]' % (slots, lo, hi))
    if facts['ram_budget_gib'] != EXPECT_RAM:
        problems.append('RAM budget %r != %s' % (facts['ram_budget_gib'], EXPECT_RAM))
    if facts['locked_mib'] not in ARMS[arm]['locks']:
        problems.append('locked %r MiB not in %s via VirtualLock' % (facts['locked_mib'], '/'.join(ARMS[arm]['locks'])))
    pool = facts.get('pool_line') or ''
    if not pool.startswith(ARMS[arm]['pool']):
        problems.append('pool line %r does not start with expected %r' % (pool[:150], ARMS[arm]['pool']))
    return not problems, '; '.join(problems)


# ---------------------------------------------------------------- one block
def run_block(root, index, rnd, arm, cfg, prompt):
    d = root / ('block-%02d-%s-r%d' % (index, arm, rnd))
    d.mkdir()
    spec = ARMS[arm]
    exe = spec['exe']
    binary_sha = sha(exe)
    meta = dict(block=index, round=rnd, arm=arm, binary=str(exe), binary_sha256=binary_sha, status='STARTED')
    if binary_sha != spec['sha']:
        meta['status'] = 'BINARY_MISMATCH'
        meta['detail'] = 'expected %s' % spec['sha']
        (d / 'meta.json').write_text(json.dumps(meta, indent=2))
        return meta, []
    args, env = build_command(arm, cfg)
    if engines():
        raise RuntimeError('strata.exe already running: %r' % engines())
    left = processes()
    if left:
        raise RuntimeError('process gate before block: %s' % json.dumps(left))
    vm = psutil.virtual_memory()
    log_heavy('%s r%d pre-block' % (arm, rnd), d / 'heavy-processes.json')
    (d / 'command.json').write_text(json.dumps(dict(
        arm=arm, exe=str(exe), binary_sha256=binary_sha, args=args,
        env={k: v for k, v in env.items() if k.startswith('STRATA_')},
        available_ram_gib=round(vm.available / 2**30, 2), prompt_sha256=PROMPT_SHA), indent=2))
    err_path = d / 'stderr.log'
    rows, started = [], time.time()
    state = dict(k=0, offset=0, ready=False)
    p = None
    timer = None
    try:
        with err_path.open('w', encoding='utf-8') as err, (d / 'stdout.log').open('w', encoding='utf-8') as out:
            p = subprocess.Popen([str(exe)] + args, env=env, cwd=str(exe.parent), stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=err, text=True, encoding='utf-8',
                                 creationflags=subprocess.CREATE_NO_WINDOW)
            timer = threading.Timer(BLOCK_CAP_S, lambda: p.poll() is None and p.kill())
            timer.start()
            next_gate = 0.0
            for line in p.stdout:
                out.write(line)
                out.flush()
                if time.monotonic() >= next_gate:
                    other = [x for x in processes() if x['pid'] != p.pid]
                    (d / 'live-process-gate.json').write_text(json.dumps(dict(owned_pid=p.pid, processes=other), indent=2))
                    if other:
                        raise RuntimeError('live process gate: ' + json.dumps(other))
                    next_gate = time.monotonic() + 5
                if line.startswith('READY'):
                    text = err_path.read_text(encoding='utf-8', errors='replace')
                    facts = startup_facts(text)
                    ok, why = capacity_verdict(arm, facts)
                    facts.update(capacity_ok=ok, capacity_detail=why, expected_slots=list(spec['slots']))
                    (d / 'startup.json').write_text(json.dumps(facts, indent=2))
                    meta['startup'] = facts
                    log('%s r%d READY %s' % (arm, rnd, json.dumps({k: facts[k] for k in ('slots', 'ram_budget_gib', 'locked_mib', 'pool_line')})))
                    if not ok:
                        meta['status'] = 'ENV_BLOCKED_CAPACITY'
                        meta['detail'] = why
                        log('%s r%d ENV_BLOCKED_CAPACITY: %s' % (arm, rnd, why))
                        p.stdin.write('QUIT\n')
                        p.stdin.flush()
                        break
                    state['ready'] = True
                    state['offset'] = err_path.stat().st_size
                    p.stdin.write('GEN 1024 %s\n' % prompt)
                    p.stdin.flush()
                elif line.startswith('DONE '):
                    tail = ''
                    for _ in range(20):
                        time.sleep(0.5)
                        text = err_path.read_text(encoding='utf-8', errors='replace')
                        tail = text[state['offset']:]
                        if 'generated in' in tail and 'decode timing' in tail:
                            break
                    state['offset'] = len(text)
                    row = dict(block=index, round=rnd, arm=arm, k=state['k'], measured=state['k'] > 0)
                    row.update(parse_done(line))
                    row.update(parse_request(tail))
                    if row.get('gen_found') and row.get('done_tok_s') is not None and abs(row['done_tok_s'] - row['decode_tok_s']) > 0.3:
                        row['rate_crosscheck_warning'] = True
                    rows.append(row)
                    log(json.dumps({x: row.get(x) for x in ('arm', 'round', 'k', 'decode_tok_s', 'file_mb', 'cpu_us_per_expert')}))
                    state['k'] += 1
                    if state['k'] <= MEASURED:
                        p.stdin.write('GEN 1024 %s\n' % prompt)
                    else:
                        p.stdin.write('QUIT\n')
                    p.stdin.flush()
                    if state['k'] > MEASURED:
                        break
                elif line.startswith('ERR '):
                    raise RuntimeError(line.strip())
            if meta['status'] == 'STARTED':
                meta['status'] = 'OK' if state['k'] > MEASURED else ('NO_READY' if not state['ready'] else 'INCOMPLETE')
            try:
                p.stdin.close()
            except OSError:
                pass
            p.wait(timeout=90)
    except Exception as e:  # noqa
        meta['status'] = 'NO_READY' if not state['ready'] else 'INCOMPLETE'
        meta['error'] = repr(e)
        log('%s r%d block error: %r' % (arm, rnd, e))
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
        if not engines():
            break
        time.sleep(1)
    if engines():
        raise RuntimeError('engine left behind after block: %r' % engines())
    try:
        meta['stderr_tail'] = err_path.read_text(encoding='utf-8', errors='replace')[-1500:] if meta['status'] not in ('OK',) else None
    except OSError:
        pass
    meta['rows'] = len(rows)
    (d / 'results.json').write_text(json.dumps(rows, indent=1))
    (d / 'meta.json').write_text(json.dumps(meta, indent=2))
    time.sleep(3)
    return meta, rows


# ---------------------------------------------------------------- statistics / summary
def stats(values):
    v = [x for x in values if x is not None]
    if not v:
        return None
    return dict(n=len(v), mean=statistics.mean(v), median=statistics.median(v), min=min(v), max=max(v),
                sd=statistics.stdev(v) if len(v) > 1 else 0.0)


def summarize(rows, blocks, order, meta_info):
    arms = [a for a in order if any(r['arm'] == a for r in rows)]
    per = {}
    for a in arms:
        m = [r for r in rows if r['arm'] == a and r['measured'] and r.get('decode_tok_s') is not None]
        per[a] = dict(rate=stats([r['decode_tok_s'] for r in m]),
                      file_mb=stats([r.get('file_mb') for r in m]),
                      ms_window=stats([r.get('ms_window') for r in m]),
                      gpu_wait=stats([r.get('gpu_wait_ms') for r in m]),
                      jobs=stats([r.get('jobs_ms') for r in m]),
                      cpu_ms=stats([r.get('cpu_ms') for r in m]),
                      cpu_us=stats([r.get('cpu_us_per_expert') for r in m]),
                      cpu_experts=stats([r.get('cpu_experts_per_layer_window') for r in m]),
                      tpw=stats([r.get('tokens_per_window') for r in m]),
                      hit=stats([r.get('cache_hit_rate') for r in m]))
    # paired by round: block mean(arm) - block mean(C)
    def block_means(a):
        out = {}
        for r in rows:
            if r['arm'] == a and r['measured'] and r.get('decode_tok_s') is not None:
                out.setdefault(r['round'], []).append(r['decode_tok_s'])
        return {k: statistics.mean(v) for k, v in out.items()}
    base = block_means('C')
    for a in arms:
        bm = block_means(a)
        diffs = [bm[k] - base[k] for k in bm if k in base]
        per[a]['paired_vs_C'] = stats(diffs) if a != 'C' else None
        per[a]['block_means'] = {str(k): round(v, 2) for k, v in sorted(bm.items())}
    lines = ['# next-steps A/B 2026-10-18 (Task027 continuation)', '']
    for k, v in meta_info.items():
        lines.append('- %s: %s' % (k, v))
    lines += ['', '## Decode tok/s (measured requests only; "generated in" segment)', '',
              '| arm | n | mean | median | min | max | sd | d mean vs C | d % | d median vs C | block means (r1,r2,r3) | paired d (mean+-sd, rounds) |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|']
    c = per.get('C', {}).get('rate')
    for a in arms:
        s = per[a]['rate']
        if not s:
            lines.append('| %s | 0 | - | - | - | - | - | - | - | - | - | - |' % a)
            continue
        dm = ('%+.2f' % (s['mean'] - c['mean'])) if c and a != 'C' else '-'
        dp = ('%+.1f%%' % ((s['mean'] / c['mean'] - 1) * 100)) if c and a != 'C' else '-'
        dd = ('%+.2f' % (s['median'] - c['median'])) if c and a != 'C' else '-'
        pv = per[a]['paired_vs_C']
        pvs = ('%+.2f +- %.2f (%d)' % (pv['mean'], pv['sd'], pv['n'])) if pv else '-'
        lines.append('| %s | %d | %.2f | %.2f | %.2f | %.2f | %.2f | %s | %s | %s | %s | %s |' % (
            a, s['n'], s['mean'], s['median'], s['min'], s['max'], s['sd'], dm, dp, dd,
            ','.join('%.1f' % x for x in per[a]['block_means'].values()), pvs))
    lines += ['', '## Per-window breakdown and CPU (means of measured requests)', '',
              '| arm | file MB/req | ms/window | GPU-reach wait | jobs | CPU ms | CPU experts/layer-win | CPU us/expert | tok/window | cache hit % |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    def m(s):
        return '%.2f' % s['mean'] if s else '-'
    for a in arms:
        q = per[a]
        lines.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            a, m(q['file_mb']), m(q['ms_window']), m(q['gpu_wait']), m(q['jobs']), m(q['cpu_ms']),
            m(q['cpu_experts']), m(q['cpu_us']), m(q['tpw']), m(q['hit'])))
    lines += ['', '## Blocks', '', '| block | round | arm | status | binary sha (8) | slots | locked MiB | detail |', '|---|---|---|---|---|---|---|---|']
    for b in blocks:
        lines.append('| %02d | %d | %s | %s | %s | %s | %s | %s |' % (
            b['block'], b['round'], b['arm'], b['status'], b['binary_sha256'][:8], (b.get('startup') or {}).get('slots'),
            (b.get('startup') or {}).get('locked_mib'),
            (b.get('detail') or b.get('error') or '')[:120].replace('|', '/')))
    return per, '\n'.join(lines) + '\n'


def write_outputs(root, rows, blocks, order, meta_info):
    per, md = summarize(rows, blocks, order, meta_info)
    (root / 'results.json').write_text(json.dumps(dict(meta=meta_info, summary=per, blocks=blocks, rows=rows), indent=1, default=str))
    (root / 'summary.md').write_text(md, encoding='utf-8')


# ---------------------------------------------------------------- schedule
def schedule(arms, rounds):
    seq = []
    n = len(arms)
    shift = max(1, n // 3)
    for r in range(rounds):
        k = (r * shift) % n
        seq += [(r + 1, a) for a in arms[k:] + arms[:k]]
    return seq


def campaign(root, arms, rounds):
    root.mkdir(exist_ok=False)
    log.path = root / 'orchestrator.log'
    seq = schedule(arms, rounds)
    est = len(seq) * EST_BLOCK_S + EST_OVERHEAD_S
    log('host %s run root %s' % (os.environ.get('COMPUTERNAME'), root))
    log('arms %s, %d rounds, %d blocks; ESTIMATED TOTAL RUNTIME ~%d min (%d s/block x %d + %d min stop/restore)' % (
        arms, rounds, len(seq), est // 60, EST_BLOCK_S, len(seq), EST_OVERHEAD_S // 60))
    log('order: ' + ' | '.join('r%d:%s' % s for s in seq))
    assert os.environ.get('COMPUTERNAME', '').upper() == HOSTNAME
    for name, ex, expect in (('control', EXE_C, EXE_C_SHA), ('tie', EXE_TIE, EXE_TIE_SHA), ('mainline', EXE_ML, EXE_ML_SHA)):
        got = sha(ex) if ex.exists() else None
        log('binary %s %s sha=%s expected=%s' % (name, ex, got, expect))
    assert sha(EXE_C) == EXE_C_SHA, 'control binary SHA mismatch'
    assert sha(PROMPT) == PROMPT_SHA
    cfg_sha = sha(CONFIG)
    cfg = json.loads(CONFIG.read_text(encoding='utf-8-sig'))
    assert Path(cfg['exe']) == EXE_C
    prompt = PROMPT.read_text(encoding='utf-8-sig').strip()
    # arms whose binary is absent/mismatched are dropped before touching the API
    live_arms = []
    for a in arms:
        spec = ARMS[a]
        if spec['exe'].exists() and sha(spec['exe']) == spec['sha']:
            live_arms.append(a)
        else:
            log('arm %s DROPPED before start: binary missing or SHA mismatch' % a)
    if 'C' not in live_arms:
        raise RuntimeError('control arm unavailable')
    seq = [s for s in seq if s[1] in live_arms]
    meta_info = dict(task='LUNA-20261012-027 continuation', host=HOSTNAME, config_sha256=cfg_sha, control_sha256=EXE_C_SHA,
                     started=time.strftime('%Y-%m-%d %H:%M:%S'), arms=live_arms, rounds=rounds,
                     estimated_minutes=est // 60, order=' | '.join('r%d:%s' % s for s in seq))
    rows, blocks, dropped = [], [], {}
    fails = {}
    restored = None
    stopped = False
    try:
        stopped = True          # set before the destructive step: a partial stop is also restored in `finally`
        meta_info['api_was_running'] = stop_api(root)
        log('api_was_running=%s' % meta_info['api_was_running'])
        ram_start_gate(root)
        log_heavy('campaign start', root / 'heavy-start.json')
        t_start = time.time()
        for index, (rnd, arm) in enumerate(seq, 1):
            if arm in dropped:
                log('skip %s r%d: %s' % (arm, rnd, dropped[arm]))
                continue
            if time.time() - t_start > CAMPAIGN_CAP_S:
                log('campaign cap reached; skipping remaining blocks')
                break
            meta, r = run_block(root, index, rnd, arm, cfg, prompt)
            blocks.append(meta)
            rows += r
            write_outputs(root, rows, blocks, live_arms, meta_info)
            st = meta['status']
            if st == 'OK':
                fails[arm] = 0
            else:
                fails[arm] = fails.get(arm, 0) + 1
                log('%s r%d status %s (consecutive failures %d)' % (arm, rnd, st, fails[arm]))
                family = ARMS[arm]['family']
                if st in ('NO_READY', 'BINARY_MISMATCH') and family == 'mainline':
                    for a in live_arms:
                        if ARMS[a]['family'] == 'mainline':
                            dropped[a] = 'mainline engine did not reach READY (see %s)' % (root / ('block-%02d-%s-r%d' % (index, arm, rnd)))
                elif fails[arm] >= 2:
                    dropped[arm] = 'two consecutive failures (%s)' % st
                if st == 'PROCESS_GATE':
                    raise RuntimeError('process gate tripped; aborting campaign (API restore follows)')
    except BaseException as e:  # noqa
        log('CAMPAIGN ABORTED: %r' % (e,))
        (root / 'abort.txt').write_text(repr(e))
        raise
    finally:
        try:
            write_outputs(root, rows, blocks, live_arms, dict(meta_info, finished=time.strftime('%Y-%m-%d %H:%M:%S'),
                                                                dropped=json.dumps(dropped)))
        except Exception as e:  # noqa
            log('summary write failed: %r' % (e,))
        try:
            healthy = bool(http_json('/health', 5).get('loaded')) and bool(api_pids())
        except Exception:  # noqa
            healthy = False
        if stopped or not healthy:
            restored = restore_api(root)
        else:
            log('API was never stopped and is healthy; nothing to restore')
            restored = dict(restored=True, note='never stopped')
        (root / 'DONE.json').write_text(json.dumps(dict(finished=time.strftime('%Y-%m-%d %H:%M:%S'), api_restored=restored.get('restored'),
                                                        api_was_running=meta_info.get('api_was_running'),
                                                        dropped=dropped), indent=2))
    return 0 if restored.get('restored') else 2


# ---------------------------------------------------------------- dry run / parse test
def dry_run(arms):
    import py_compile
    py_compile.compile(__file__, doraise=True)
    print('syntax OK; hostname', os.environ.get('COMPUTERNAME'))
    cfg = json.loads(CONFIG.read_text(encoding='utf-8-sig'))
    print('config sha', sha(CONFIG), 'control sha ok', sha(EXE_C) == EXE_C_SHA)
    for a in arms:
        s = ARMS[a]
        have = s['exe'].exists()
        got = sha(s['exe']) if have else None
        args, env = build_command(a, cfg)
        print('ARM', a, 'exe', s['exe'].name, 'exists', have, 'sha_ok', got == s['sha'], 'slots', s['slots'])
        print('   args', ' '.join(args[args.index('--pool-workers'):args.index('--pool-workers') + 2]),
              '| expert-cache', args[args.index('--expert-cache') + 1],
              '| env', json.dumps({k: v for k, v in sorted(env.items()) if k.startswith('STRATA_')}))
    seq = schedule(arms, 3)
    print('blocks', len(seq), 'est min', (len(seq) * EST_BLOCK_S + EST_OVERHEAD_S) // 60)
    print('order', ' | '.join('r%d:%s' % s for s in seq))
    # synthetic summary
    import random
    random.seed(1)
    rows = [dict(block=1, round=r, arm=a, k=k, measured=k > 0, decode_tok_s=48 + random.random() * 2 - (a != 'C'),
                 file_mb=5000, ms_window=34, gpu_wait=12, jobs_ms=3, cpu_ms=13, cpu_us_per_expert=70, cpu_experts_per_layer_window=3.7,
                 tokens_per_window=1.6, cache_hit_rate=70)
            for r in (1, 2, 3) for a in arms for k in range(4)]
    blocks = [dict(block=1, round=1, arm='C', status='OK', binary_sha256='0' * 64, startup=dict(slots='3153'))]
    per, md = summarize(rows, blocks, arms, dict(test='synthetic'))
    print(md[:1500])
    print('capacity_verdict samples:', capacity_verdict('C', dict(slots='3153', ram_budget_gib='20.00', locked_mib='20479', pool_line=POOL9_ALL + ' (x)')),
          capacity_verdict('C', dict(slots='3141', ram_budget_gib='20.00', locked_mib='20479', pool_line=POOL9_ALL + ' (x)')),
          capacity_verdict('SAUTO', dict(slots='3038', ram_budget_gib='20.00', locked_mib='20479', pool_line=POOL9_ALL + ' (x)')),
          capacity_verdict('ML8', dict(slots='3145', ram_budget_gib='20.00', locked_mib='20478', pool_line=POOL9_ALL + ' (x)')),
          capacity_verdict('C', dict(slots='3153', ram_budget_gib='20.00', locked_mib='20478', pool_line=POOL9_ALL + ' (x)')))
    for a in arms:
        print('expected pool line', a, '->', ARMS[a]['pool'])
    print('current available RAM %.2f GiB (logged only, no start gate); api_pids %d engines %d' % (
        psutil.virtual_memory().available / 2**30, len(api_pids()), len(engines())))
    print('heavy processes:', json.dumps(heavy_processes()))
    print('API NOT touched; no engine started.')


def parse_test(path, arm=None):
    text = Path(path).read_text(encoding='utf-8', errors='replace')
    facts = startup_facts(text)
    print(json.dumps(facts, indent=1))
    if arm:
        print('capacity_verdict(%s) ->' % arm, capacity_verdict(arm, facts))
    blocks = re.split(r'(?=strata decode timing:)', text)
    for b in blocks[1:4]:
        r = parse_request(b)
        r.pop('timing_line', None)
        print(json.dumps(r))


def main():
    argv = sys.argv[1:]
    arms = DEFAULT_ORDER
    rounds = 3
    if '--arms' in argv:
        i = argv.index('--arms')
        arms = argv[i + 1].split(',')
        del argv[i:i + 2]
    if '--rounds' in argv:
        i = argv.index('--rounds')
        rounds = int(argv[i + 1])
        del argv[i:i + 2]
    for a in arms:
        assert a in ARMS, a
    assert 'C' in arms
    if argv and argv[0] == '--dry-run':
        return dry_run(arms)
    if argv and argv[0] == '--parse-test':
        return parse_test(argv[1], argv[2] if len(argv) > 2 else None)
    for s in (signal.SIGTERM, getattr(signal, 'SIGBREAK', signal.SIGTERM)):
        signal.signal(s, lambda *_: (_ for _ in ()).throw(SystemExit(3)))
    return campaign(Path(argv[0]), arms, rounds)


if __name__ == '__main__':
    sys.exit(main())
