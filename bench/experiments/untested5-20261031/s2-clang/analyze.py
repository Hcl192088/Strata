import re, statistics, json
from pathlib import Path

root = Path(__file__).parent
lines = (root / 'raw-summary.txt').read_text(encoding='utf-8-sig').splitlines()
assert json.loads(lines[0]) == {'status':'DONE','completed':1020,'total':1020}
pat = re.compile(r'r(\d+)-lp(11|15)-(msvc|clang)-t(\d+)-nt(\d+)-down([01])-(.*?)\.log\|RAW .*us_per_expert=([0-9.]+)$')
data = {}
for line in lines[1:]:
    m = pat.fullmatch(line)
    assert m, line
    rnd, lp, arm, typ, nt, down, dt, value = m.groups()
    key = (lp, typ, nt, down, dt, arm)
    data.setdefault(key, {})[int(rnd)] = float(value)
assert len(data) == 68 and all(set(x) == set(range(1,16)) for x in data.values())
names = {'16':'IQ2_XXS','17':'IQ2_XS','18':'IQ3_XXS','21':'IQ3_S','22':'IQ2_S'}
weights = {'18':6,'21':13,'17':10,'22':10,'16':9}
rows=[]
for lp in ('11','15'):
    for typ in ('18','21','17','22','16'):
        for nt in ('1','2','3'):
            a=statistics.median(data[(lp,typ,nt,'0','','msvc')].values()); b=statistics.median(data[(lp,typ,nt,'0','','clang')].values())
            rows.append((lp,names[typ],nt,a,b,a/b))
    for dt in ('q2_0','iq4_nl'):
        a=statistics.median(data[(lp,'16','1','1',dt,'msvc')].values()); b=statistics.median(data[(lp,'16','1','1',dt,'clang')].values())
        rows.append((lp,dt,'1',a,b,a/b))
out=['| 核心 | 型別 | nt | MSVC µs | clang µs | MSVC/clang |','|---|---|---:|---:|---:|---:|']
out += [f'| {lp} | {name} | {nt} | {a:.2f} | {b:.2f} | {ratio:.3f} |' for lp,name,nt,a,b,ratio in rows]
out += ['', '加權結果（各 nt 分開計算，層數 6/13/10/10/9；倍數 = Σ層數×MSVC 中位數 / Σ層數×clang 中位數）：']
ratios={}
for nt in ('1','2','3'):
    vals={}
    for lp in ('11','15'):
        sums=[sum(weights[t]*statistics.median(data[(lp,t,nt,'0','',arm)].values()) for t in weights) for arm in ('msvc','clang')]
        vals[lp]=1-sums[1]/sums[0]; ratios[(lp,nt)]=sums[0]/sums[1]
    estimate=8.8*(0.73*vals['11']+0.27*vals['15'])
    out.append(f'- nt={nt}: P {ratios[("11",nt)]:.4f}x ({vals["11"]*100:+.2f}% 時間節省), E {ratios[("15",nt)]:.4f}x ({vals["15"]*100:+.2f}%); 估計 {estimate:+.3f} ms/window。')
(root/'analysis.md').write_text('\n'.join(out)+'\n',encoding='utf-8')
print('\n'.join(out[-4:]))
