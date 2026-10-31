import argparse, json, os, sys, traceback
from pathlib import Path

BEST = r'C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build\strata.exe'
SHA = 'A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8'
PY = r'C:\Users\User\Strata\archive\legacy\20261009\Strata-lm-run-2026-09-28\.venv\Scripts\python.exe'
SERVE = r'C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\upstream-v0142'

def plan(arms, rounds, root):
    result=[]
    for rnd in range(1, rounds+1):
        shift=(rnd-1)%len(arms)
        for arm in arms[shift:]+arms[:shift]:
            i=len(result)+1
            d=root/'out'/('block-%02d-%s-r%d' % (i,arm['name'],rnd))
            result.append({'index':i,'round':rnd,'arm':arm['name'],'dir':str(d),
                'exe':arm.get('exe',BEST),'sha':arm.get('sha',SHA),
                'command':[PY,'-u','-m','serve.server','--engine','strata','--config',str(d/'config.json'),'--host','127.0.0.1','--port','8081'],
                'cwd':SERVE,'extra_env':arm.get('env',{}),'extra_args':arm.get('args',{}),'gate_slots':arm.get('gate_slots',False)})
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--arms-file',required=True,type=Path);p.add_argument('--rounds',type=int,required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    cfg=json.loads(a.arms_file.read_text(encoding='utf-8-sig'));arms=cfg['arms'];assert arms and a.rounds>0
    assert len({x['name'] for x in arms})==len(arms)
    assert all(('exe' in x)==('sha' in x) and ('sha' not in x or x['sha']) for x in arms)
    blocks=plan(arms,a.rounds,a.root)
    if a.dry_run:
        print(json.dumps({'blocks':blocks,'total':len(blocks)},indent=2));return
    sys.path.insert(0,r'C:\Users\User\Strata-Adrian-control\runs\big-exact-20261030')
    import base as c
    rp,ns=c.rp,c.ns
    c.R=a.root;rp.make_body=c.make_body;ns.log.path=a.root/'controller.log'
    assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
    c.identity();assert not ns.api_pids() and not ns.engines()
    assert not (a.root/'progress.json').exists()
    (a.root/'out').mkdir(parents=True)
    specs={x['name']:x for x in arms}
    def capacity(arm,spec,facts):
        errors=[]
        if specs[arm].get('gate_slots',False) and str(facts.get('slots'))!='3153':errors.append('slots')
        if str(facts.get('ram_budget_gib'))!='20.00':errors.append('RAM budget')
        if str(facts.get('locked_mib'))!='20479':errors.append('locked MiB')
        return not errors, ', '.join(errors), specs[arm].get('gate_slots',False)
    rp.capacity_ok=capacity
    if 'request_set' in cfg:
        requests=json.loads(Path(cfg['request_set']).read_text(encoding='utf-8-sig'))
        rp.POINTS=list(requests)
        def request_body(point,maximum):
            body=dict(requests[point]);body.update(cfg.get('sampling',{}));return body
        rp.make_body=request_body
    results=[]
    try:
        for b in blocks:
            c.gate('block-%02d'%b['index']);assert not ns.api_pids() and not ns.engines()
            x=specs[b['arm']];env={'STRATA_NATIVE_PIPE':'1'};env.update(x.get('env',{}))
            spec=dict(exe=b['exe'],sha=b['sha'],serve_dir=SERVE,env=env,args=x.get('args',{}),strict_capacity=x.get('gate_slots',False),split=False)
            meta,rows=rp.run_block(a.root/'out',b['index'],b['round'],b['arm'],spec,512)
            if meta['status']!='OK':raise RuntimeError(str(meta))
            d=Path(b['dir']);n=sum(r['windows'] for r in rows)
            for row in rows:
                response=json.loads((d/('resp-'+row['pid']+'.json')).read_text(encoding='utf-8'))
                row['output_text']=response['choices'][0]['message']
            results.append(dict(index=b['index'],round=b['round'],arm=b['arm'],path=str(d),rate=c.rate(rows),tokens=sum(r['m_out_tokens'] for r in rows),windows=n,slots=meta['startup']['slots'],segments={k:sum(r[k]*r['windows'] for r in rows)/n for k in ('gpu_wait_ms','cpu_ms','draft_ms','ms_window')},rows=rows))
            (a.root/'blocks.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
            (a.root/'progress.json').write_text(json.dumps({'completed':len(results),'total':len(blocks),'status':'RUNNING'}),encoding='utf-8')
        status='DONE'
    except BaseException:
        status='FAILED';(a.root/'error.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        (a.root/'progress.json').write_text(json.dumps({'completed':len(results),'total':len(blocks),'status':status}),encoding='utf-8')
if __name__=='__main__':main()
