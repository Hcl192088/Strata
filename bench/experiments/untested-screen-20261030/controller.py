"""Task027 continuation: ten fresh-engine, single-flag, 3x128-token screens.

Requires the unchanged staged LFUSE base.py and replay harness in this run root.
No deployment, temperature change, combined flags, extra rounds, or fallback.
"""
import json
import os
from pathlib import Path
import re
import time
import traceback

import psutil
import base

R = Path(__file__).resolve().parent
rp, ns = base.rp, base.ns
POINTS = ('p01', 'p05', 'p08')
TOKENS = 128
FLAGS = tuple('STRATA_' + x for x in (
    'EXPERT_V2', 'DF_PLE', 'FUSE_HEAD_GR', 'GR_DOWN_MAX4',
    'DF_QB_Q4', 'DF_BRANCH', 'MMVF_ROWS', 'ATTN_LANECELL'))
EXCLUDED_FLAGS = tuple('STRATA_' + x for x in ('GDN_SPLIT', 'TSUM', 'QFUSE', 'LFUSE'))
ARMS = ('C',) + FLAGS + ('C2',)
FATAL = re.compile(r'(?i)(NATIVE_PIPE FATAL|CUDA error|CUDA_ERROR|fatal error|'
                   r'NATIVE_PIPE_CHECK MISMATCH|check_mismatch_rows=[1-9][0-9]*)')
S, ROWS, BLOCKS = {}, [], {}
ACTIVE = None
HTTP_LOCAL = rp.http_local
PROCESSES = ns.processes


def write(name, value):
    p = R / name
    t = p.with_suffix(p.suffix + '.tmp')
    t.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    t.replace(p)


def save(**fields):
    S.update(fields, utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    write('campaign.json', S)


def processes():
    # The reused gate already covers strata/llama/python/CMake/Ninja/nvcc/cl.
    # Add the actual CPU-screen/build/diagnostic executables it does not name.
    found = PROCESSES()
    seen = {p['pid'] for p in found}
    mine = psutil.Process()
    exclude = {mine.pid} | {p.pid for p in mine.parents()}
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        if p.pid in seen or p.pid in exclude:
            continue
        if re.search(r'(?i)(r4bench|^link\.exe$|^nmake\.exe$|^nsys\.exe$|^wpr\.exe$)',
                     p.info['name'] or ''):
            found.append(p.info)
    return found


ns.processes = processes


def gate(tag, live=False):
    base.identity()
    p = ns.processes()
    write('processes-' + tag + '.json', p)
    allowed = ({pid for _, pid, _ in ns.api_pids()} | set(ns.watch_pids())
               if live else rp.own_pids())
    assert not [x for x in p if x['pid'] not in allowed], ('PROCESS_GATE', tag, p)


def verify():
    v = base.verify()
    p = psutil.Process(v['pid'])
    env = p.environ()
    assert not any(k in env for k in FLAGS + EXCLUDED_FLAGS), 'BASELINE_FLAG_CONTAMINATION'
    assert env.get('STRATA_NATIVE_PIPE') == '1' and env.get('STRATA_IQ3S_MT1') == '1'
    assert 'STRATA_IQ_MT_MIN' not in env
    m = ns.http_json('/metrics', 8)
    assert m['live']['state'] == 'idle' and m['live']['queued'] == 0, ('API_BUSY', m['live'])
    v['live'] = m['live']
    return v


def spec(arm):
    assert arm in ARMS
    env = {'STRATA_NATIVE_PIPE': '1'}
    if arm in FLAGS:
        env[arm] = '1'
    return dict(exe=str(ns.EXE_C), sha=ns.EXE_C_SHA, serve_dir=rp.SERVE_V0142,
                env=env, args={}, strict_capacity=True, split=False)


def check_running_arm():
    """Runs before each inference request, while the owned engine still exists."""
    assert ACTIVE is not None
    base.identity()
    candidates = [p for p in psutil.Process().children(recursive=True)
                  if p.name().lower() == 'strata.exe']
    assert len(candidates) == 1, 'OWNED_ENGINE_COUNT'
    engine = candidates[0]
    assert ns.sha(Path(engine.exe())) == ns.EXE_C_SHA, 'RUNNING_BINARY_MISMATCH'
    assert engine.nice() == psutil.ABOVE_NORMAL_PRIORITY_CLASS, 'PRIORITY_MISMATCH'
    cfg = json.loads((ACTIVE['dir'] / 'config.json').read_text(encoding='utf-8-sig'))
    env = engine.environ()
    assert all(env.get(k) == str(v) for k, v in cfg['env'].items()), 'CONFIG_ENV_MISMATCH'
    for key in FLAGS + EXCLUDED_FLAGS:
        assert env.get(key) == ('1' if key == ACTIVE['arm'] else None), ('SINGLE_FLAG_MISMATCH', key)
    assert env.get('STRATA_NATIVE_PIPE') == '1' and env.get('STRATA_IQ3S_MT1') == '1'
    assert 'STRATA_IQ_MT_MIN' not in env
    m = HTTP_LOCAL('/metrics', timeout=10)
    assert m['engine']['expert_slots'] == 3153 and m['engine']['arena_mib'] == 20479
    evidence = ACTIVE.setdefault('runtime_checks', [])
    evidence.append(dict(pid=engine.pid, created=engine.create_time(), priority=engine.nice(),
                         env_verified=True, slots=3153, arena_mib=20479,
                         utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
    write('runtime-' + ACTIVE['arm'] + '.json', evidence)


def fatal_check():
    if ACTIVE is None:
        return
    p = ACTIVE['dir'] / 'engine.log'
    if p.exists():
        assert not FATAL.search(p.read_text(encoding='utf-8', errors='replace')), 'FATAL_ENGINE_LOG'


def http_local(path, body=None, timeout=900):
    if path == '/v1/chat/completions':
        check_running_arm()
        fatal_check()
    answer = HTTP_LOCAL(path, body, timeout)
    if path == '/v1/chat/completions':
        fatal_check()
    return answer


rp.http_local = http_local


def output_info(d, point):
    p = d / ('resp-' + point + '.json')
    response = json.loads(p.read_text(encoding='utf-8'))
    choice = response['choices'][0]
    message = choice['message']
    text = ((message.get('reasoning_content') or '') + '\n' + (message.get('content') or '') +
            json.dumps(message.get('tool_calls') or [], sort_keys=True, ensure_ascii=False))
    return text, dict(chars=len(text), repeated=base.repeated(text),
                      finish=choice.get('finish_reason'), response_sha256=ns.sha(p))


def preliminary_rate(rows):
    valid = [x for x in rows if x.get('m_out_tokens') is not None and x.get('m_decode_ms') is not None]
    assert len(valid) == len(rows) and valid, 'RATE_INPUT_INCOMPLETE'
    tokens = sum(float(x['m_out_tokens']) for x in valid)
    ms = sum(float(x['m_decode_ms']) for x in valid)
    assert tokens > 0 and ms > 0
    return tokens * 1000 / ms


def prepare():
    gate('preflight', True)
    write('prelaunch_verify.json', verify())
    cfg = json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
    assert not any(k in cfg['env'] for k in FLAGS + EXCLUDED_FLAGS), 'CONFIG_ALREADY_HAS_FLAG'
    sampling = {}
    for point in POINTS:
        original = json.loads((rp.REQ_DIR / (point + '.json')).read_text(encoding='utf-8'))
        # base.make_body is the tested sampled replay override, not harness's greedy default.
        body = base.make_body(point, TOKENS)
        assert rp.make_body is base.make_body, 'SAMPLED_BODY_OVERRIDE_MISSING'
        assert body.get('temperature') == 1.0 and body.get('top_p') == .95
        assert body.get('top_k') == 20 and body.get('min_p') == 0
        assert body.get('seed') == 1000 + int(point[1:]) and body['max_tokens'] == TOKENS
        assert {k: v for k, v in body.items() if k != 'max_tokens'} == {
            k: v for k, v in original.items() if k != 'max_tokens'}, 'REQUEST_CHANGED'
        sampling[point] = {k: body[k] for k in (
            'temperature', 'top_p', 'top_k', 'min_p', 'seed', 'presence_penalty',
            'frequency_penalty', 'repetition_penalty', 'reasoning_effort') if k in body}
    write('sampling.json', sampling)
    audits = []
    for arm in ARMS:
        d = R / ('config-audit-' + arm)
        d.mkdir(exist_ok=True)
        _, got = rp.build_cfg(arm, spec(arm), d)
        expected = json.loads(json.dumps(cfg))
        expected['cwd'] = str(ns.EXE_C.parent)
        expected['log'] = str(d / 'engine.log')
        expected['open_browser'] = False
        if arm in FLAGS:
            expected['env'][arm] = '1'
        assert got == expected, ('UNEXPECTED_CONFIG_DIFF', arm)
        audits.append(dict(arm=arm, allowed_diff_only=True, sha256=ns.sha(d / 'config.json')))
    write('config-audit.json', audits)
    inputs = dict(requests={p: ns.sha(rp.REQ_DIR / (p + '.json')) for p in POINTS},
                  harness={p.name: ns.sha(p) for p in (R / 'harness').glob('*.py')},
                  controller_sha256=ns.sha(Path(__file__)), base_sha256=ns.sha(R / 'base.py'),
                  binary_sha256=ns.EXE_C_SHA, config_sha256=ns.CONFIG_SHA,
                  points=list(POINTS), max_tokens=TOKENS, arms=list(ARMS))
    assert len(inputs['harness']) == 2, 'EXPECTED_TWO_HARNESS_FILES'
    write('inputs.json', inputs)
    return inputs


def run(index, arm):
    global ACTIVE
    gate('block-%02d' % index)
    d = R / 'out' / ('block-%02d-%s-r1' % (index, arm))
    ACTIVE = dict(arm=arm, dir=d)
    save(phase='BLOCK', current=dict(index=index, arm=arm, round=1))
    old_points = rp.POINTS
    rp.POINTS = list(POINTS)
    try:
        meta, rows = rp.run_block(R / 'out', index, 1, arm, spec(arm), TOKENS)
    finally:
        rp.POINTS = old_points
    text = (d / 'engine.log').read_text(encoding='utf-8', errors='replace')
    fatal = bool(FATAL.search(text))
    record = dict(index=index, arm=arm, path=str(d), status=meta['status'],
                  rows=len(rows), fatal=fatal, pipe_active='NATIVE_PIPE ACTIVE' in text)
    S.setdefault('completed', []).append(record)
    ROWS.extend(rows)
    write('rows.json', ROWS)
    save()
    write('activation-evidence-' + arm + '.json', dict(
        effective_env_verified=bool(ACTIVE.get('runtime_checks')),
        log_mentions=[line for line in text.splitlines() if arm in FLAGS and arm in line],
        kernel_branch_activation='NOT_MEASURED_NO_DEDICATED_COUNTER',
        limitation='Engine environment delivery does not prove the intended CUDA branch executed.'))
    assert not fatal, ('FATAL_ABORT_CAMPAIGN', arm)
    assert meta['status'] == 'OK' and len(rows) == len(POINTS), ('BLOCK_FAILED', arm, meta)
    assert record['pipe_active'] and ACTIVE.get('runtime_checks'), ('RUNTIME_EVIDENCE_MISSING', arm)
    per_point = {}
    for p in POINTS:
        _, per_point[p] = output_info(d, p)
    rejected = [p for p in POINTS if per_point[p]['repeated']]
    BLOCKS[arm] = dict(path=str(d), preliminary_tok_s=preliminary_rate(rows), points=per_point,
                       preliminary_reject=bool(rejected), repeated_points=rejected)
    write('blocks.json', BLOCKS)
    save(arm_results=BLOCKS)
    ACTIVE = None
    if arm in ('C', 'C2'):
        assert not rejected, ('BROKEN_CONTROL_REPETITION', arm, rejected)
    # A nonfatal broken candidate is recorded/rejected; the next predefined arm is still independent.


def summarize():
    c, c2 = BLOCKS['C'], BLOCKS['C2']
    aa = {}
    for point in POINTS:
        a, _ = output_info(Path(c['path']), point)
        b, _ = output_info(Path(c2['path']), point)
        aa[point] = dict(prefix_chars=base.prefix(a, b), identical=a == b,
                         C_chars=len(a), C2_chars=len(b))
    findings = {}
    for arm in FLAGS:
        details = []
        for point in POINTS:
            a, _ = output_info(Path(c['path']), point)
            b, _ = output_info(Path(c2['path']), point)
            x, info = output_info(Path(BLOCKS[arm]['path']), point)
            px, py = base.prefix(a, x), base.prefix(b, x)
            earlier = a != x and b != x and max(px, py) < aa[point]['prefix_chars']
            details.append(dict(point=point, C_prefix_chars=px, C2_prefix_chars=py,
                                identical_C=a == x, identical_C2=b == x,
                                earlier_than_AA=earlier, **info))
        findings[arm] = dict(
            status=('REJECT_REPETITION' if BLOCKS[arm]['preliminary_reject'] else
                    'NUMERIC_UNRESOLVED_EARLIER_DIVERGENCE' if any(x['earlier_than_AA'] for x in details) else
                    'NO_EXTRA_DIVERGENCE_OBSERVED_SMALL_SCREEN'),
            points=details, preliminary_tok_s=BLOCKS[arm]['preliminary_tok_s'],
            preliminary_vs_C_percent=100 * (BLOCKS[arm]['preliminary_tok_s'] / c['preliminary_tok_s'] - 1),
            preliminary_vs_C2_percent=100 * (BLOCKS[arm]['preliminary_tok_s'] / c2['preliminary_tok_s'] - 1),
            operator_bitwise='NOT_MEASURED', semantic_quality='NOT_ESTABLISHED',
            branch_activation='NOT_MEASURED')
    result = dict(status='SCREEN_COMPLETE_NO_PROMOTION', task_id='LUNA-20261012-027',
                  arms=10, requests=30, points=list(POINTS), max_tokens=TOKENS,
                  AA=aa, candidates=findings,
                  control_preliminary_tok_s=c['preliminary_tok_s'],
                  control2_preliminary_tok_s=c2['preliminary_tok_s'],
                  speed_claim='NONE: one fixed-order 3x128 screen, not a paired performance test',
                  quality_claim='NONE: AA comparison is not operator bitwise or semantic parity',
                  deployed=False)
    write('result.json', result)
    return result


def manifest():
    files = sorted(p for p in (R / 'out').rglob('*') if p.is_file())
    write('raw-manifest.json', {str(p.relative_to(R)): dict(bytes=p.stat().st_size, sha256=ns.sha(p))
                              for p in files})


def main():
    assert os.environ['COMPUTERNAME'] == 'DESKTOP-LKMLUPC'
    assert not (R / 'campaign.json').exists(), 'TERMINAL_OR_RUNNING_NO_RERUN'
    ns.log.path = R / 'controller.log'
    save(task_id='LUNA-20261012-027', task='UNTESTED_SINGLE_FLAGS_SCREEN', phase='PREFLIGHT',
         controller_pid=os.getpid(), current_best_sha=ns.EXE_C_SHA,
         authorization='2026-10-30 user: complete +10% plan and test remaining candidates; '
                       'fixed single-flag screen, no deployment or sampling changes')
    stopped, error = False, None
    try:
        prepare()
        gate('pre-stop', True)
        write('initial_verify.json', verify())
        (R / 'out').mkdir()
        write('rows.json', [])
        stopped = True
        ns.stop_api(R)
        gate('after-stop')
        for i, arm in enumerate(ARMS):
            run(i, arm)
        summarize()
        save(verdict='SCREEN_COMPLETE_NO_PROMOTION')
    except BaseException:
        error = traceback.format_exc()
        save(phase='ERROR', error=error, verdict='SCREEN_ABORTED')
        write('failure.json', dict(error=error, current=S.get('current'), completed=S.get('completed', [])))
    finally:
        save(before_restore_phase=S.get('phase'), phase='RESTORE')
        try:
            if stopped:
                gate('pre-restore')
                restore = ns.restore_api(R)
            else:
                restore = dict(restored=True, not_stopped=True)
        except BaseException:
            restore = dict(restored=False, error=traceback.format_exc())
        write('restore.json', restore)
        try:
            gate('post-restore', True)
            v = verify()
        except BaseException:
            v = dict(verified=False, error=traceback.format_exc())
        write('final_verify.json', v)
        manifest()
        save(phase='DONE' if error is None and restore.get('restored') and v['verified'] else 'FAILED',
             restored=bool(restore.get('restored')), verified=v['verified'],
             independent_verify='PENDING_PARENT_FRESH_CHECK')


if __name__ == '__main__':
    main()
