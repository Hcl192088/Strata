import json, shutil
from pathlib import Path
S = Path(r'D:\strata\state')
NEW_SHA = '385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5'
OLD_SHA = '366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2'
AT = '2026-10-28T10:27:30+08:00'
ENV = {'STRATA_MISS_OVERLAP': '1', 'STRATA_MISS_OVERLAP_SPIN_US': '2000'}
CAND_DIR = r'C:\Users\User\Strata-Adrian-control\runs\miss-overlap-20261027'
EVID = r'D:\strata\state\LUNA-20261012-027.night-20261027.md (夜間佇列 4) ; D:\strata\state\EXPERIMENT_LEDGER.md (S2K_PROMOTION_CONFIRM)'

for n in ('CAMPAIGN_CURRENT_BEST.json', 'LIVE_DEPLOYMENT.json'):
    shutil.copy2(S / n, S / (n[:-5] + '.pre-s2k-20261028.json'))

# ---- CAMPAIGN_CURRENT_BEST.json
p = S / 'CAMPAIGN_CURRENT_BEST.json'
d = json.loads(p.read_text(encoding='utf-8'))
d['status'] = 'S2K_PROMOTED_BY_USER_20261028'
d['last_revalidated_at'] = AT
d['current_best_binary_sha256'] = NEW_SHA
d['current_best_candidate'] = {
    'binary_sha256': NEW_SHA,
    'binary_path': CAND_DIR + r'\build\strata.exe',
    'env': ENV,
    'role': 'current_best_deployed_live',
    'global_fastest_claim': False,
    'promotion_status': 'promoted_by_user_2026-10-28_phase1_confirm_passed',
    'identity_evidence': 'D:\\strata\\state\\LIVE_DEPLOYMENT.json',
    'evidence': EVID,
    'headline': 'greedy 8-round ABBA S2K vs previous best +8.49% (95% CI +5.91..+11.06, df=7), 46.42 vs 42.81 tok/s pooled; sampling +4.0%; neuro warm +5.6%; MCHK 0/69896 mismatches',
}
d['live_deployed_baseline'] = {
    'binary_sha256': NEW_SHA, 'quantization': 'IQ3_XXS', 'role': 'deployed_current_best', 'env': ENV,
    'evidence': 'D:\\strata\\state\\LIVE_DEPLOYMENT.json',
}
d['previous_current_best'] = [
    {
        'binary_sha256': OLD_SHA,
        'binary_path': r'C:\Users\User\Strata-Adrian-control\runs\ram-lru-20261013\build\strata.exe',
        'name': 'Task020 live (ram-lru-20261013 build, IQ3_XXS)',
        'live_from_to': 'built 2026-10-13, revalidated 2026-10-18 .. replaced 2026-10-28 10:27',
        'rollback': 'scheduled task Strata-Task020-API action back to tools\\start_task020_api.ps1 (see LIVE_DEPLOYMENT.json.rollback)',
        'full_record': 'D:\\strata\\state\\CAMPAIGN_CURRENT_BEST.pre-s2k-20261028.json',
        'history': 'D:\\strata\\state\\CURRENT_BEST_HISTORY.md',
    }
]
d['last_reconciled_from'] = list(d.get('last_reconciled_from', [])) + [EVID]
p.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding='utf-8')

# ---- LIVE_DEPLOYMENT.json
p = S / 'LIVE_DEPLOYMENT.json'
d = json.loads(p.read_text(encoding='utf-8'))
prev = {k: d[k] for k in ('startup_launcher', 'config_path', 'config_sha256', 'binary_path', 'binary_sha256', 'build_source', 'build_source_head', 'build_source_dirty_files', 'last_verified_at')}
prev['note'] = ('config file on the desktop hashes to 43A48004...39C07 at deployment time (this file previously recorded C805...EA18; the change predates 2026-10-28 and was not made by the S2K deployment); '
                'launcher start_task020_api.ps1 hashes to 8D043FBC...018AC; both left untouched.')
d['previous_live'] = prev
d['status'] = 'LIVE_S2K_DEPLOYED_VERIFIED'
d['last_verified_at'] = AT
d['startup_launcher'] = r'C:\Users\User\Strata-Adrian-control\tools\start_task020_api_s2k.ps1'
d['launcher_sha256'] = '50B9D745E980409E397FCBF18A94B87AC97B49F56DD12B5F4CA80A0AD60B42CB'
d['config_path'] = r'C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\server-task020-8080-v0142-s2k.json'
d['config_sha256'] = '94D72B5677F543EAF104A6050D6951786387E437A6303895F091302E6E866C51'
d['binary_path'] = CAND_DIR + r'\build\strata.exe'
d['binary_sha256'] = NEW_SHA
d['build_source'] = CAND_DIR + r'\source'
d['build_source_head'] = '61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406 (ram-lru-20261013 base) + 2 dirty RAM-LRU files + patch3 (MISS_OVERLAP)'
d['build_source_dirty_files'] = ['include/strata/core/expert_source.hpp', 'src/core/expert_source.cpp']
d['build_source_file_sha256'] = {
    'include/strata/core/expert_source.hpp': '6A8C92ED77259EB5984C704EC6935D9CCD84A045AE3B294B1B212B03E1029F6E',
    'src/core/expert_source.cpp': 'F51BE9DED69C50CBEAEFEF05A922A3B63D2AF0B4190AE489E519D2C29259E485',
    'previous_hpp': '72D25EEBAEF05C994418734DDEE2CE4D16D7FAAC7E8FC68692BDC8F4BFA5140F',
    'previous_cpp': 'A44FCDAA21092DC3824A5F388EB6E9CFCDA03723408B019297555D5A69A180A6',
}
d['env_added_by_s2k'] = ENV
d['engine_log'] = CAND_DIR + r'\s2k-api.engine.log'
d['config_derivation'] = 'copy of server-task020-8080-v0142.json; changed only exe, cwd, log and env (+STRATA_MISS_OVERLAP=1, STRATA_MISS_OVERLAP_SPIN_US=2000); args identical'
d['deployment'] = {
    'deployed_at': '2026-10-28 10:27:13 (new engine start)',
    'authorized_by': 'user (chat, 2026-10-28)',
    'engine_pid_at_deploy': 6668,
    'engine_priority_class': 'AboveNormal',
    'verification': ['/health loaded=true', 'expert cache 3153 slots, RAM budget 20.00 GiB, locked 20479 MiB', 'MISS_OVERLAP progress lines present (split_calls accumulating)',
                     '3 Hermes smoke requests ok (p01 p02 p03, max_tokens 128)', 'scheduled task Strata-Task020-API priority stays 2'],
    'receipt': r'C:\Users\User\Strata-Adrian-control\runs\s2k-deploy-20261028\switch_receipt.json',
}
d['rollback'] = {
    'steps': ['Set-ScheduledTask action of Strata-Task020-API back to: powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File C:\\Users\\User\\Strata-Adrian-control\\tools\\start_task020_api.ps1',
              'stop the verified API stack (engine + serve.server + memory-policy --run wrapper), keep the --watch process',
              'Start-ScheduledTask Strata-Task020-API; wait /health loaded=true; check binary SHA 366A355E... and 3153 slots'],
    'previous_binary_sha256': OLD_SHA,
    'estimated_minutes': 5,
}
d['scheduled_task_state'] = 'Running (action -> start_task020_api_s2k.ps1, priority 2)'
d['current_best_relation'] = 'deployed_current_best_per_user_decision_20261028'
d['notes'] = list(d.get('notes', [])) + [
    'ATTENTION: benchmark harness tools (next_steps_ab_20261018.py: EXE_C/api_pids/restore_api, replay_ab_20261027.py) still identify the live API by the OLD binary path/SHA 366A... (control arm "C0"). After this deployment stop_api() will not find the live engine (it requires the verified 366A exe in --serve) and capacity/SHA gates for "control" still point to 366A: update or copy the harness before the next remote benchmark.',
    'The old binary and old config/launcher are untouched and remain the C0 control for matched comparisons.',
]
p.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding='utf-8')
print('ok')
