"""Promote coordination pointers only from the verified remote deployment receipts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT.parent
r = json.loads((ROOT / 'out/deploy_receipt.json').read_text(encoding='utf-8'))
v = json.loads((ROOT / 'out/final_state.json').read_text(encoding='utf-8'))
assert r['result'] == 'DEPLOYED_MT1' and v['verified']
assert len(r['smoke']) == 3 and all(s['ok'] for s in r['smoke'])
oldlive = json.loads((STATE / 'LIVE_DEPLOYMENT.pre-mt1-20261028.json').read_text(encoding='utf-8-sig'))
campaign = json.loads((STATE / 'CAMPAIGN_CURRENT_BEST.pre-mt1-20261028.json').read_text(encoding='utf-8-sig'))
live = dict(oldlive)
ts = v['checked_at']
receipt_path = r'C:\Users\User\Strata-Adrian-control\runs\mt1-deploy-20261028\out\deploy_receipt.json'
proof_path = r'C:\Users\User\Strata-Adrian-control\runs\mt1-deploy-20261028\out\final_state.json'
bench = r'D:\strata\state\iq3s-mt1-ab-20261028\IQ3S-MT1-AB-20261028.md'
live.update(status='LIVE_S2K_MT1_DEPLOYED_VERIFIED', last_verified_at=ts,
            canonical_source_head=v['canonical_source_head'], canonical_source_branch=v['branch'],
            startup_launcher=v['launcher_path'], launcher_sha256=v['launcher_sha256'],
            config_path=v['config_path'], config_sha256=v['config_sha256'], engine_log=v['config']['log'],
            current_best_relation='deployed_current_best_per_user_decision_MT1_20261028',
            scheduled_task_state='Running (action -> start_task020_api_s2k_mt1.ps1, priority 2)')
live['previous_live'] = {k: oldlive[k] for k in ('startup_launcher', 'config_path', 'config_sha256', 'binary_path', 'binary_sha256', 'engine_log', 'launcher_sha256')}
live['previous_live'].update(name='S2K', full_record=str(STATE / 'LIVE_DEPLOYMENT.pre-mt1-20261028.json'))
live['last_remote_revalidation'] = dict(checked_at=ts, by='standalone verify_deployed.py after deployment and 3 smoke requests',
    hostname=v['hostname'], engine_pid=v['engines'][0]['pid'], binary_sha256=v['engines'][0]['sha256'], serve=True,
    priority_class='AboveNormal', env=v['config']['env'], capacity=v['capacity'], health_loaded=True,
    scheduled_task=v['task']['arguments'], evidence=proof_path)
live['notes'] = [
    'Local coordination pointer; verify remote runtime before any further operation.',
    'S2K and S2K+MT1 share binary SHA; current-best identity MUST include config SHA and MT1 environment.',
    'Use state/mt1-deploy-20261028/active-harness for MT1 identity; historical harness copies identify older configurations.',
    'MT1 uses the same mathematical operations with different floating-point accumulation order; output tokens can differ. User explicitly accepted this.',
    'Canonical repository HEAD differs from the build-source base; the build uses the recorded detached source with its existing dirty patches.',
    'Reproducible rebuild not performed; this promotion is backed by same-binary deployment and existing controlled A/B evidence.'
]
live['deployment'] = dict(deployed_at=r['stop_started_at'], verified_at=ts, authorized_by='User explicitly requested deployment and best update in this conversation',
    engine_pid_at_deploy=v['engines'][0]['pid'], engine_priority_class='AboveNormal', receipt=receipt_path,
    final_verification=proof_path, smoke=[{k: s[k] for k in ('pid', 'ok', 'finish', 'completion_tokens', 'has_tool_calls')} for s in r['smoke']],
    automatic_fallback=False)
live['config_derivation'] = 'Exact S2K config except +env STRATA_IQ3S_MT1=1 and dedicated log path; args and temperature unchanged.'
live['env_added_by_mt1'] = {'STRATA_IQ3S_MT1': '1'}
live['env_must_be_absent'] = ['STRATA_IQ_MT_MIN']
live['rollback'] = dict(automatic=False, target='S2K', binary_sha256=oldlive['binary_sha256'],
    config_path=oldlive['config_path'], config_sha256=oldlive['config_sha256'], launcher=oldlive['startup_launcher'],
    steps=['Only when user authorizes rollback: recheck host, live process identities and idle state.',
           'Stop only verified current API stack, set Strata-Task020-API action back to the preserved S2K launcher and start it.',
           'Verify same binary SHA, absence of STRATA_IQ3S_MT1 and STRATA_IQ_MT_MIN, MISS_OVERLAP=1/SPIN_US=2000, loaded, AboveNormal, 3153/20.00/20479.'])
env = dict(v['config']['env'])
campaign.update(status='S2K_MT1_PROMOTED_BY_USER_20261028', last_revalidated_at=ts,
    current_best_config_sha256=v['config_sha256'], current_best_env=env)
candidate = campaign['current_best_candidate']
candidate.update(name='S2K+MT1', config_path=v['config_path'], config_sha256=v['config_sha256'], env=env,
    promotion_status='promoted_by_user_20261028_MT1_deployment_verified',
    evidence=bench, deployment_evidence=proof_path,
    headline='Existing Hermes replay 10-round A/B: 47.00 vs S2K 45.10 tok/s; round-paired +4.26% (95% CI +2.15..+6.37), CPU -2.19 ms/window. Deployment verified; no new throughput benchmark.',
    output_contract='Same weights/routing/math, different floating-point accumulation order accepted by user; token identity not claimed.')
campaign['live_deployed_baseline'].update(name='S2K+MT1', env=env, config_path=v['config_path'], config_sha256=v['config_sha256'])
campaign['previous_current_best'].insert(0, dict(name='S2K', binary_sha256=oldlive['binary_sha256'], binary_path=oldlive['binary_path'],
    config_sha256=oldlive['config_sha256'], env=oldlive['env_added_by_s2k'],
    live_from_to='2026-10-28 10:27 .. MT1 deployment 2026-10-28 21:33',
    full_record=str(STATE / 'CAMPAIGN_CURRENT_BEST.pre-mt1-20261028.json'), history=str(STATE / 'CURRENT_BEST_HISTORY.md')))
campaign['promotion_gate']['output_contract'] = 'User accepts MT1 floating-point accumulation differences; no routing bias, expert skipping or requantization.'
campaign['promotion_gate']['baseline_assignment_reason'] = 'Existing IQ3S_MT1_AB passed controlled throughput gate; user explicitly authorized promotion; live config/env/capacity and smoke verified.'
campaign['last_reconciled_from'] += [bench, proof_path]
for name, data in [('LIVE_DEPLOYMENT', live), ('CAMPAIGN_CURRENT_BEST', campaign)]:
    (STATE / (name + '.json')).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

history = STATE / 'CURRENT_BEST_HISTORY.md'
text = history.read_text(encoding='utf-8')
assert '**S2K+MT1**' not in text
marker = '|---|---|---|---|---|---|\n'
row = '| 2026-10-28 21:33 切換／21:35 驗收 | **S2K+MT1** | 385EF64E…30F5（與 S2K 相同） | S2K 加 `STRATA_IQ3S_MT1=1`，`STRATA_IQ_MT_MIN` 未設；config `server-task020-8080-v0142-s2k-mt1.json`（SHA F23F1AAD…EB6F）；launcher `start_task020_api_s2k_mt1.ps1`；排程 priority 2 | 既有 IQ3S_MT1_AB：47.00 vs 45.10 tok/s，按輪 +4.26%（CI +2.15～+6.37），CPU −2.19 ms/window；本輪只驗收部署，3/3 smoke 通過；浮點差異經使用者接受 | S2K 原檔保留；`LIVE_DEPLOYMENT.pre-mt1-20261028.json`／`CAMPAIGN_CURRENT_BEST.pre-mt1-20261028.json`；receipt `runs/mt1-deploy-20261028/out/deploy_receipt.json` |\n'
assert marker in text
history.write_text(text.replace(marker, marker + row, 1), encoding='utf-8')

active = ROOT / 'active-harness'
active.mkdir(exist_ok=False)
for name in ('next_steps_ab_20261018.py', 'replay_ab_20261027.py'):
    s = (ROOT / 'harness' / name).read_text(encoding='utf-8')
    if name.startswith('next_steps'):
        s = s.replace('server-task020-8080-v0142-s2k.json', 'server-task020-8080-v0142-s2k-mt1.json')
        s = s.replace('start_task020_api_s2k.ps1', 'start_task020_api_s2k_mt1.ps1')
        s = s.replace('94D72B5677F543EAF104A6050D6951786387E437A6303895F091302E6E866C51', v['config_sha256'])
        anchor = "            matched.append((0, p.pid, cl))"
        assert s.count(anchor) == 1
        s = s.replace(anchor, "            ev = p.environ()\n            if ev.get('STRATA_IQ3S_MT1') != '1' or ev.get('STRATA_IQ_MT_MIN'):\n                raise RuntimeError('MT1 live environment identity mismatch')\n" + anchor)
        anchor = "    assert Path(cfg['exe']) == EXE_C"
        assert s.count(anchor) == 1
        s = s.replace(anchor, "    assert cfg_sha == CONFIG_SHA, 'MT1 config SHA mismatch'\n    assert cfg['env'].get('STRATA_IQ3S_MT1') == '1' and 'STRATA_IQ_MT_MIN' not in cfg['env']\n" + anchor)
        s = '# MT1 identity copy, 2026-10-28. Import for identity checks; no campaign was run in this deployment.\n' + s
    compile(s, name, 'exec')
    (active / name).write_text(s, encoding='utf-8')

manifest = dict(schema_version=1, name='S2K+MT1', status='DEPLOYED_VERIFIED', task_id='LUNA-20261012-027',
    authorized_scope='MT1 deployment and current-best promotion; no new benchmark', checked_at=ts,
    binary_path=live['binary_path'], binary_sha256=live['binary_sha256'], config_path=v['config_path'], config_sha256=v['config_sha256'],
    config=v['config'], launcher_path=v['launcher_path'], launcher_sha256=v['launcher_sha256'],
    source=dict(canonical_head_before_deployment=v['canonical_source_head'], build_source_head=v['build_source_head'],
                dirty_paths=live['build_source_dirty_files'], file_sha256=live['build_source_file_sha256'],
                rebuild_verified=False, note='Existing binary reused. Source base plus dirty patch identity must not be confused with canonical HEAD.'),
    task=dict(name='Strata-Task020-API', arguments=v['task']['arguments'], priority=2, recurring_triggers=False),
    capacity=v['capacity'], output_contract=candidate['output_contract'],
    performance_evidence=dict(path=bench, runs=10, workload='Hermes replay 10 points, max 512 tokens, greedy, fresh engine per block',
        mt1_tok_s=47.00, s2k_tok_s=45.10, paired_gain_percent=4.26, ci95_percent=[2.15, 6.37], cpu_delta_ms_window=-2.19,
        note='Historical controlled A/B, not a new performance measurement; outputs differ.'),
    verification=dict(receipt=receipt_path, final_state=proof_path, smoke=live['deployment']['smoke']),
    previous_best=live['previous_live'], local_snapshots=[str(STATE / 'LIVE_DEPLOYMENT.pre-mt1-20261028.json'), str(STATE / 'CAMPAIGN_CURRENT_BEST.pre-mt1-20261028.json')],
    rollback=live['rollback'], temperature_changed=False, routing_changed=False)
(ROOT / 'BEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(ROOT / 'server-task020-8080-v0142-s2k-mt1.json').write_text(json.dumps(v['config'], indent=4) + '\n', encoding='utf-8')
print('Promoted local live/campaign/history and created active MT1 harness + BEST manifest.')
