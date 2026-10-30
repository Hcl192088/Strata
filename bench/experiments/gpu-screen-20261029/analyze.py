import json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parent/'raw'
rows=json.loads((R/'rows.json').read_text(encoding='utf-8'))
camp=json.loads((R/'campaign.json').read_text(encoding='utf-8'))
arms=[c['arm'] for c in camp['completed']]
dirs={c['arm']:Path(c['path']).name for c in camp['completed']}
def text(a,p):
    f=R/'out'/dirs[a]/('resp-%s.json'%p)
    if not f.exists():return None
    m=json.loads(f.read_text(encoding='utf-8'))['choices'][0]['message']
    return (m.get('reasoning_content') or '')+'\n<<CONTENT>>\n'+(m.get('content') or '')
def loop(t):
    w=re.findall(r'\S+',t or '')
    for n in range(2,7):
        for i in range(len(w)-n*4+1):
            u=w[i:i+n]
            if all(w[i+k*n:i+k*n+n]==u for k in range(4)):return ' '.join(u)
    return None
out={'cmp':{},'metrics':{}}
for a in arms:
    for p in ['p01','p05','p08']:
        t=text(a,p);c=text('C',p);c2=text('C2',p)
        d=dict(have=t is not None,loop=loop(t) if t else None)
        for nm,ref in (('vsC',c),('vsC2',c2)):
            if t is None or ref is None:d[nm]=None;continue
            if t==ref:d[nm]=dict(identical=True)
            else:
                i=next((i for i,(x,y) in enumerate(zip(t,ref)) if x!=y),min(len(t),len(ref)))
                d[nm]=dict(identical=False,idx=i,len=len(t),reflen=len(ref),this=t[max(0,i-30):i+50],ref=ref[max(0,i-30):i+50])
        d['excerpt']=t[:0] if t is None else t[-120:]
        out['cmp'][a+'|'+p]=d
for a in arms:
    rs=[r for r in rows if r['arm']==a and not r.get('error')]
    if not rs:continue
    w=sum(r['windows'] for r in rs);tok=sum(r['m_out_tokens'] for r in rs);ms=sum(r['m_decode_ms'] for r in rs)
    out['metrics'][a]=dict(n=len(rs),tokens=tok,windows=w,decode_ms=ms,tok_s=1000*tok/ms,ms_w=ms/w,tok_w=tok/w,cpu_ms=sum(r['cpu_ms']*r['windows'] for r in rs)/w,gpu_wait=sum(r['gpu_wait_ms']*r['windows'] for r in rs)/w,finish=[r.get('finish') for r in rs],per_prompt={r['pid']:dict(tok=r['m_out_tokens'],win=r['windows'],tok_s=r['m_decode_tok_s']) for r in rs})
(Path(__file__).resolve().parent/'analysis.json').write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf-8')
print(json.dumps(out['metrics'],indent=0)[:200])
