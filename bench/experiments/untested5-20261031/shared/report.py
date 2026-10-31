import argparse,json,math,statistics
from pathlib import Path
T95 = {1:12.706204736,2:4.30265273,3:3.182446305,4:2.776445105,5:2.570581836,6:2.446911851,7:2.364624252,8:2.306004135,9:2.262157163,10:2.228138852,11:2.20098516,12:2.17881283,13:2.160368656,14:2.144786688,15:2.131449546,16:2.119905299,17:2.109815578,18:2.10092204,19:2.093024054,20:2.085963447,21:2.079613845,22:2.073873068,23:2.06865761,24:2.063898562,25:2.059538553,26:2.055529439,27:2.051830516,28:2.048407142,29:2.045229642,30:2.042272456}
p=argparse.ArgumentParser();p.add_argument('blocks',type=Path);p.add_argument('--control',default='C');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
blocks=json.loads(a.blocks.read_text(encoding='utf-8-sig'));by={(b['round'],b['arm']):b for b in blocks};arms=sorted({b['arm'] for b in blocks}-{a.control});out={}
for arm in arms:
    pairs=[]
    for rnd in sorted({b['round'] for b in blocks}):
        if (rnd,a.control) not in by or (rnd,arm) not in by:continue
        c=by[rnd,a.control];b=by[rnd,arm]
        cp={r['pid']:r for r in c['rows']};bp={r['pid']:r for r in b['rows']}
        points={q:100*(bp[q]['m_decode_tok_s']/cp[q]['m_decode_tok_s']-1) for q in cp.keys() & bp.keys()}
        pairs.append({'round':rnd,'percent':100*(b['rate']/c['rate']-1),'per_point_percent':points})
    vals=[x['percent'] for x in pairs];mean=statistics.mean(vals) if vals else None
    half=T95[len(vals)-1]*statistics.stdev(vals)/math.sqrt(len(vals)) if len(vals)>1 else None
    out[arm]={'pairs':pairs,'mean_percent':mean,'ci95_percent':[mean-half,mean+half] if half is not None else None}
a.output.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')

