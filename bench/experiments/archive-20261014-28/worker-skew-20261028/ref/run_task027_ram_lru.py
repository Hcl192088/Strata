"""Sequential 020-C / experimental RAM LRU neuro test, restores API in finally."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request
import psutil

BASE = Path(r'C:\Users\User\Strata-Adrian\runs\iq3-campaign-020')
ROOT = Path(r'C:\Users\User\Strata-Adrian-control\runs\ram-lru-20261013')
SOURCE = ROOT / 'source'
BUILD = ROOT / 'build'
OLD_SHA = '803C1EA975038328716FD4AD37BD9A21268A66AC60EB1F5C26171074A14CEF39'
PYTHON = Path(sys.executable)
CFG = json.loads((BASE / 'server-task020-8080-v0142.json').read_text(encoding='utf-8-sig'))
PROMPT = Path(r'C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens')


def ps(command):
    subprocess.run(['powershell', '-NoProfile', '-Command', command], check=True, capture_output=True)


def health(path):
    with urllib.request.urlopen('http://<desktop-tailscale-ip>:8080' + path, timeout=10) as response:
        return json.load(response)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def processes():
    found = []
    parents = {p.pid for p in psutil.Process().parents()}
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        if p.pid == os.getpid() or p.pid in parents:
            continue
        if re.search('strata|llama|python|cmake|ninja|nvcc|msbuild|cl.exe', p.info['name'] or '', re.I):
            found.append(p.info)
    return found


def run(name, exe, lru, check=False, max_new=1024, request_keys='', expected_capacity=None):
    assert not processes(), 'process gate: ' + json.dumps(processes())
    d = ROOT / name
    d.mkdir()
    env = os.environ.copy()
    env.update(CFG['env'])
    env['STRATA_RAM_LRU'] = str(int(lru))
    env['STRATA_RAM_LRU_CHECK'] = str(int(check))
    env['STRATA_DECODE_TIMING'] = '1'
    args = ['--serve'] + list(CFG['args'])
    assert '--dump-routing' not in args
    manifest = dict(exe=str(exe), binary_sha256=sha(exe), args=args,
                    env={k: v for k, v in env.items() if k.startswith('STRATA_')},
                    prompt_sha256=sha(PROMPT), max_new=max_new, request_keys=request_keys,
                    free_ram=psutil.virtual_memory().available)
    (d / 'command.json').write_text(json.dumps(manifest, indent=2))
    tokens, done = [], None
    started = time.time()
    with (d / 'stderr.log').open('w', encoding='utf-8') as err, (d / 'stdout.log').open('w', encoding='utf-8') as log:
        p = subprocess.Popen([str(exe)] + args, env=env, cwd=exe.parent,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, text=True, encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.NORMAL_PRIORITY_CLASS)
        try:
            next_gate = 0.0
            for line in p.stdout:
                log.write(line)
                if expected_capacity is not None and time.monotonic() >= next_gate:
                    other = [item for item in processes() if item['pid'] != p.pid]
                    (d/'live-process-gate.json').write_text(json.dumps(dict(owned_pid=p.pid,processes=other),indent=2))
                    assert not other, 'live process gate: ' + json.dumps(other)
                    next_gate = time.monotonic() + 5
                if time.time() - started > 900:
                    raise TimeoutError(name)
                if line.startswith('READY'):
                    if expected_capacity is not None:
                        startup = (d/'stderr.log').read_text(encoding='utf-8')
                        slots = re.search(r'expert cache (\d+) slots',startup)
                        ram = re.search(r'RAM budget ([\d.]+) GiB',startup)
                        assert slots and ram, 'Missing startup capacity evidence'
                        actual = (int(slots[1]),float(ram[1]))
                        (d/'capacity-gate.json').write_text(json.dumps(dict(actual=actual,expected=expected_capacity)))
                        assert actual == expected_capacity, 'Runtime capacity mismatch: ' + str(actual)
                    p.stdin.write(f'GEN {max_new} ' + (request_keys+' ' if request_keys else '') + PROMPT.read_text(encoding='utf-8-sig').strip() + '\n')
                    p.stdin.flush()
                elif line.startswith('T '):
                    tokens.append(int(line.split()[1]))
                elif line.startswith('DONE '):
                    done = line.strip()
                    p.stdin.write('QUIT\n')
                    p.stdin.flush()
                    break
                elif line.startswith('ERR '):
                    raise RuntimeError(line)
            assert done, name + ' no DONE'
            p.stdin.close()
            for line in p.stdout:
                log.write(line)
            assert p.wait(timeout=30) == 0
        finally:
            if p.poll() is None:
                p.terminate()
                p.wait(timeout=30)
    residual = processes()
    (d / 'post-process-gate.json').write_text(json.dumps(dict(owned_pid=p.pid,exit_code=p.returncode,processes=residual),indent=2))
    assert not residual, 'residual process after ' + name + ': ' + json.dumps(residual)
    (d / 'tokens.json').write_text(json.dumps(tokens))
    result = dict(name=name, done=done, output_tokens=len(tokens), token_sha256=sha(d/'tokens.json'), exit_code=0)
    (d / 'result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)
    return result


def main():
    assert sha(CFG['exe']) == OLD_SHA
    assert sha(PROMPT) == '9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA'
    assert health('/metrics')['live']['state'] == 'idle', 'API busy'
    live = processes()
    assert len([p for p in live if p['name'].lower() == 'strata.exe']) == 1
    assert all('iq3-campaign-020' in ' '.join(p['cmdline'] or []) for p in live), live
    resume = '--resume-build' in sys.argv
    if resume:
        assert SOURCE.exists() and not (ROOT/'control-01').exists()
    else:
        ROOT.mkdir(exist_ok=False)
    (ROOT / ('resume-gate.json' if resume else 'pre-gate.json')).write_text(json.dumps(live, indent=2))
    paused = False
    try:
        # Recheck immediately before pausing; never interrupt an active request.
        assert health('/metrics')['live']['state'] == 'idle'
        ps('Stop-ScheduledTask -TaskName Strata-Task020-API')
        paused = True
        for item in reversed(live):
            if psutil.pid_exists(item['pid']):
                p = psutil.Process(item['pid'])
                assert 'iq3-campaign-020' in ' '.join(p.cmdline())
                p.terminate()
        time.sleep(2)
        assert not processes(), processes()
        upstream = BASE / 'upstream-v0142'
        if resume:
            assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip() == '61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406'
            for relative in ('src/core/expert_source.cpp','include/strata/core/expert_source.hpp'):
                file = SOURCE / relative
                text = file.read_text(encoding='utf-8')
                assert text.count('const ExpertJobMulti* jobs') == 1
                file.write_text(text.replace('const ExpertJobMulti* jobs', 'const strata::kernels::cpu::ExpertJobMulti* jobs'),encoding='utf-8')
        else:
            subprocess.run(['git', '-C', str(upstream), 'worktree', 'add', '--detach', str(SOURCE),
                            '61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406'], check=True)
            subprocess.run([str(PYTHON), str(Path(__file__).with_name('apply_task027_ram_lru.py')),
                            '--source', str(SOURCE)], check=True)
        with (ROOT / 'candidate.patch').open('w', encoding='utf-8') as patch:
            subprocess.run(['git', '-C', str(SOURCE), 'diff', '--'], stdout=patch, check=True)
        build_script = ROOT / 'build.cmd'
        dep = BASE / 'build-v0142/_deps/strata_llamacpp-src'
        assert (dep / 'ggml/CMakeLists.txt').exists()
        build_script.write_text('@echo off\ncall "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\Common7\\Tools\\VsDevCmd.bat" -arch=x64\n'
            'if errorlevel 1 exit /b %errorlevel%\n'
            f'cmake -S "{SOURCE}" -B "{BUILD}" -G "NMake Makefiles" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES=89 -DSTRATA_ENABLE_CUDA=ON -DFETCHCONTENT_SOURCE_DIR_STRATA_LLAMACPP="{dep}"\n'
            'if errorlevel 1 exit /b %errorlevel%\n'
            f'cmake --build "{BUILD}" --target strata -j 9\nexit /b %errorlevel%\n')
        with (ROOT/'build.log').open('w', encoding='utf-8') as log:
            subprocess.run(['cmd', '/c', str(build_script)], stdout=log, stderr=subprocess.STDOUT, check=True, timeout=1800)
        assert not processes(), processes()
        exe = BUILD / 'strata.exe'
        results = []
        for name, binary, enabled, check in [
            ('control-01', Path(CFG['exe']), False, False),
            ('rebuilt-off', exe, False, False),
            ('candidate-checked', exe, True, True),
            ('candidate-01', exe, True, False),
            ('control-02', Path(CFG['exe']), False, False),
            ('candidate-02', exe, True, False),
        ]:
            assert sha(CFG['exe']) == OLD_SHA
            results.append(run(name, binary, enabled, check))
        (ROOT/'results.json').write_text(json.dumps(results, indent=2))
    finally:
        if paused:
            ps('Start-ScheduledTask -TaskName Strata-Task020-API')
            for _ in range(90):
                try:
                    if health('/health').get('loaded'):
                        print('API_RESTORED loaded=true', flush=True)
                        break
                except (OSError, ValueError):
                    pass
                time.sleep(2)
            else:
                raise RuntimeError('API restoration did not reach loaded=true')


if __name__ == '__main__':
    main()
