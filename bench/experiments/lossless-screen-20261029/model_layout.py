import importlib.util
import json
from pathlib import Path
import struct
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('screen_gate',HERE/'screen.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
best=json.loads(s.BEST.read_text(encoding='utf-8-sig'))
gate=s.gate(best)
cfg=json.loads(Path(best['config_path']).read_text(encoding='utf-8-sig'))

class Header:
    scalar={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'B',10:'Q',11:'q',12:'d'}
    def __init__(self,f):self.f=f
    def u(self,fmt):return struct.unpack('<'+fmt,self.f.read(struct.calcsize(fmt)))[0]
    def string(self):return self.f.read(self.u('Q')).decode('utf-8')
    def skip(self,t):
        if t in self.scalar:self.f.seek(struct.calcsize(self.scalar[t]),1)
        elif t==8:self.f.seek(self.u('Q'),1)
        elif t==9:
            et,n=self.u('I'),self.u('Q')
            if et in self.scalar:self.f.seek(n*struct.calcsize(self.scalar[et]),1)
            else:
                for _ in range(n):self.skip(et)
        else:raise ValueError(t)

rows=[];files=[]
for flag in ('--native','--ple-gguf'):
    path=Path(cfg['args'][cfg['args'].index(flag)+1])
    with path.open('rb') as f:
        r=Header(f)
        if f.read(4)!=b'GGUF':raise RuntimeError('NOT_GGUF')
        ver,nt,nkv=r.u('I'),r.u('Q'),r.u('Q')
        for _ in range(nkv):r.string();r.skip(r.u('I'))
        for _ in range(nt):
            name=r.string();nd=r.u('I');dims=[r.u('Q') for _ in range(nd)]
            ty,offset=r.u('I'),r.u('Q')
            if ty in (8,14) and len(dims)==2 or name=='output.weight':
                rows.append({'name':name,'dims':dims,'type':ty,'shard':path.name})
        files.append({'path':str(path),'size':path.stat().st_size,
                      'mtime_ns':path.stat().st_mtime_ns,'header_end':f.tell(),'version':ver})
eligible=[]
for row in rows:
    if row['type']==14:
        ni,no=row['dims']
        row['bytes']=ni*no//256*210
        row['eligible_shape']=ni%256==0 and ni//256>=4 and no>=2048
        if row['eligible_shape']:eligible.append(row)
out={'pre_gate':gate,'files':files,'selected_tensors':rows,
     'q6_total_count':sum(r['type']==14 for r in rows),
     'q6_total_bytes':sum(r.get('bytes',0) for r in rows if r['type']==14),
     'q6_shape_eligible_count':len(eligible),'q6_shape_eligible_bytes':sum(r['bytes'] for r in eligible),
     'q8_count':sum(r['type']==8 for r in rows),'post_gate':s.gate(best)}
(HERE/'model-layout.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ('selected_tensors','pre_gate','post_gate')}))
print('OUTPUT_HEAD',[r for r in rows if r['name']=='output.weight'])
