"""Bounded Windows direct-I/O mechanism probe. Never changes model/runtime files."""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import mmap
import os
from pathlib import Path
import random
import statistics
import time

ROOT=Path(__file__).resolve().parent/'io-probe'
SOURCE=Path(r'C:\Users\User\Strata-IQ3-20261008\models\IQ3_XXS\Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf')
SIZE=256*1024**2
OFFSET=16*1024**3
K=c.WinDLL('kernel32',use_last_error=True)
class OV(c.Structure):
    _fields_=[('Internal',c.c_size_t),('InternalHigh',c.c_size_t),('Offset',w.DWORD),('OffsetHigh',w.DWORD),('hEvent',w.HANDLE)]
def api(name,args,ret):
    f=getattr(K,name);f.argtypes=args;f.restype=ret;return f
openfile=api('CreateFileW',[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE],w.HANDLE)
close=api('CloseHandle',[w.HANDLE],w.BOOL)
alloc=api('VirtualAlloc',[c.c_void_p,c.c_size_t,w.DWORD,w.DWORD],c.c_void_p)
free=api('VirtualFree',[c.c_void_p,c.c_size_t,w.DWORD],w.BOOL)
event=api('CreateEventW',[c.c_void_p,w.BOOL,w.BOOL,w.LPCWSTR],w.HANDLE)
reset=api('ResetEvent',[w.HANDLE],w.BOOL)
read=api('ReadFile',[w.HANDLE,c.c_void_p,w.DWORD,c.c_void_p,c.POINTER(OV)],w.BOOL)
write=api('WriteFile',[w.HANDLE,c.c_void_p,w.DWORD,c.c_void_p,c.POINTER(OV)],w.BOOL)
wait=api('WaitForSingleObject',[w.HANDLE,w.DWORD],w.DWORD)
result=api('GetOverlappedResult',[w.HANDLE,c.POINTER(OV),c.POINTER(w.DWORD),w.BOOL],w.BOOL)
cancel=api('CancelIoEx',[w.HANDLE,c.POINTER(OV)],w.BOOL)

class File:
    def __init__(self,path,new=False):
        self.h=openfile(str(path),0xC0000000 if new else 0x80000000,7,None,1 if new else 3,0x60000000|(0x80000000 if new else 0),None)
        if self.h in (None,c.c_void_p(-1).value): raise c.WinError(c.get_last_error())
    def close(self):
        if self.h: close(self.h);self.h=None
class Buffer:
    def __init__(self,n):
        self.p=alloc(None,n,0x3000,4);self.ev=event(None,True,False,None);self.ov=OV();self.pending=False
        if not self.p or not self.ev: raise c.WinError(c.get_last_error())
    def start(self,f,off,n,writing=False):
        reset(self.ev);self.ov=OV();self.ov.hEvent=self.ev;self.ov.Offset=off&0xffffffff;self.ov.OffsetHigh=off>>32
        self.f=f;self.n=n
        ok=(write if writing else read)(f.h,self.p,n,None,c.byref(self.ov))
        if not ok and c.get_last_error()!=997: raise c.WinError(c.get_last_error())
        self.pending=True
    def finish(self):
        if wait(self.ev,5000)!=0:
            cancel(self.f.h,c.byref(self.ov));raise RuntimeError('Direct I/O timed out; own request cancelled; no fallback')
        got=w.DWORD()
        if not result(self.f.h,c.byref(self.ov),c.byref(got),False): raise c.WinError(c.get_last_error())
        self.pending=False
        assert got.value==self.n,('short I/O',got.value,self.n)
    def close(self):
        if self.pending: return  # OS reclaims on exit; never free memory while cancellation may still be pending.
        close(self.ev);free(self.p,0,0x8000)

def bench(f,chunk,buffers):
    order=list(range(SIZE//chunk));random.Random(7821).shuffle(order)
    start=time.perf_counter()
    for at in range(0,len(order),len(buffers)):
        batch=order[at:at+len(buffers)]
        for b,i in zip(buffers,batch): b.start(f,i*chunk,chunk)
        for b in buffers[:len(batch)]: b.finish()
    seconds=time.perf_counter()-start
    return dict(seconds=seconds,GB_s=SIZE/1e9/seconds)

def main():
    import psutil
    assert os.environ.get('COMPUTERNAME','').upper()=='DESKTOP-LKMLUPC'
    assert time.time()<1793227800,'past 06:50 cutoff'
    for p in psutil.process_iter(['pid','name','cmdline']):
        cmd=' '.join(p.info['cmdline'] or [])
        if p.pid==os.getpid() or p.pid==os.getppid(): continue
        name=(p.info['name'] or '').lower()
        assert not (name in ('cmake.exe','cl.exe','nvcc.exe','link.exe','nsys.exe','wpr.exe') or 'overnight-20261029\\controller.py' in cmd),('foreign test/build',p.pid,name,cmd)
        if name=='strata.exe':
            assert hashlib.sha256(Path(p.exe()).read_bytes()).hexdigest().upper()=='385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5'
    assert SOURCE.stat().st_size>OFFSET+SIZE
    ROOT.mkdir(exist_ok=False)
    files=[];buffers=[];mapping=None;mapfile=None
    state=dict(status='PREPARE',source=str(SOURCE),offset=OFFSET,bytes_per_file=SIZE,rounds=[])
    def save():
        temp=ROOT/'progress.tmp';temp.write_text(json.dumps(state,indent=2));temp.replace(ROOT/'progress.json')
    save()
    try:
        source=File(SOURCE);files.append(source)
        buffers=[Buffer(2*1024**2) for _ in range(16)]
        digests={}
        for label in ('U','M'):
            dst=File(ROOT/(label+'.bin'),True);files.append(dst)
            expected=hashlib.sha256()
            for off in range(0,SIZE,2*1024**2):
                b=buffers[0];b.start(source,OFFSET+off,2*1024**2);b.finish()
                expected.update(c.string_at(b.p,2*1024**2))
                b.start(dst,off,2*1024**2,True);b.finish()
            actual=hashlib.sha256()
            for off in range(0,SIZE,2*1024**2):
                b=buffers[0];b.start(dst,off,2*1024**2);b.finish();actual.update(c.string_at(b.p,2*1024**2))
            assert expected.digest()==actual.digest(),'shadow byte mismatch'
            digests[label]=actual.hexdigest()
        assert digests['U']==digests['M']
        state.update(shadow_sha256=digests,status='MEASURE');save()
        mapfile=open(ROOT/'M.bin','rb');mapping=mmap.mmap(mapfile.fileno(),0,access=mmap.ACCESS_READ)
        time.sleep(3)
        arms=dict(U=files[1],M=files[2])
        for rd in range(1,7):
            for chunk in (512*1024,2*1024**2):
                for label in (('U','M') if rd%2 else ('M','U')):
                    row=dict(round=rd,arm=label,chunk=chunk,queue_depth=16,**bench(arms[label],chunk,buffers))
                    state['rounds'].append(row);save()
        summary={}
        for chunk in (512*1024,2*1024**2):
            delta=[]
            for rd in range(1,7):
                x={r['arm']:r['GB_s'] for r in state['rounds'] if r['round']==rd and r['chunk']==chunk}
                delta.append((x['U']/x['M']-1)*100)
            mean=statistics.mean(delta);half=2.570582*statistics.stdev(delta)/(len(delta)**.5)
            summary[str(chunk)]=dict(unmapped_advantage_pct=mean,paired_ci95_pct=[mean-half,mean+half],deltas_pct=delta,
                mechanism_gate=mean>=15 and mean-half>0)
        state.update(status='DONE',summary=summary,limitations=['Two separate shadow extents; physical placement/SSD cache can confound.', 'Mapped clone not faulted into RAM; tests mapping section behavior, not all original GGUF cache conditions.', 'Mechanism screen only; no model tok/s or promotion claim.']);save()
        print(json.dumps(state['summary'],indent=2))
    except BaseException as e:
        state.update(status='FAILED',error=repr(e));save();raise
    finally:
        if mapping is not None: mapping.close()
        if mapfile is not None: mapfile.close()
        for f in files: f.close()
        for b in buffers: b.close()
def confirm_mapping():
    assert os.environ.get('COMPUTERNAME','').upper()=='DESKTOP-LKMLUPC'
    assert time.time()<1793227800
    receipt=ROOT/'confirm-mapping.json'
    assert not receipt.exists(),'confirmation already executed'
    old=json.loads((ROOT/'progress.json').read_text());assert old['status']=='DONE'
    files=[];buffers=[];maps=[];readers=[]
    state=dict(status='START',rounds=[],design='same U file before/after mapping, fixed mapped M reference; six alternating rounds per phase')
    def save(): receipt.write_text(json.dumps(state,indent=2))
    save()
    try:
        files=[File(ROOT/'U.bin'),File(ROOT/'M.bin')];buffers=[Buffer(2*1024**2) for _ in range(16)]
        mf=open(ROOT/'M.bin','rb');readers.append(mf);maps.append(mmap.mmap(mf.fileno(),0,access=mmap.ACCESS_READ))
        for phase in ('U_unmapped','U_mapped'):
            if phase=='U_mapped':
                uf=open(ROOT/'U.bin','rb');readers.append(uf);maps.append(mmap.mmap(uf.fileno(),0,access=mmap.ACCESS_READ))
            for rd in range(1,7):
                for chunk in (512*1024,2*1024**2):
                    for label in (('U','M') if rd%2 else ('M','U')):
                        state['rounds'].append(dict(phase=phase,round=rd,arm=label,chunk=chunk,**bench(files[0 if label=='U' else 1],chunk,buffers)));save()
        # Validate both shadows by direct read, after all measurements; no buffered hash changes the unmapped arm.
        for f,label in zip(files,('U','M')):
            digest=hashlib.sha256()
            for off in range(0,SIZE,2*1024**2):
                b=buffers[0];b.start(f,off,2*1024**2);b.finish();digest.update(c.string_at(b.p,2*1024**2))
            assert digest.hexdigest()==old['shadow_sha256'][label]
        summary={}
        for phase in ('U_unmapped','U_mapped'):
            summary[phase]={}
            for chunk in (512*1024,2*1024**2):
                ratios=[]
                for rd in range(1,7):
                    x={r['arm']:r['GB_s'] for r in state['rounds'] if r['phase']==phase and r['chunk']==chunk and r['round']==rd}
                    ratios.append(x['U']/x['M'])
                summary[phase][str(chunk)]=dict(U_over_M_mean=statistics.mean(ratios),ratios=ratios)
        state.update(status='DONE',bytes_verified=True,summary=summary,limitation='Mapping order cannot be reversed without changing cache state; fixed M reference reduces time-drift confounding but does not prove full model speedup.');save()
        print(json.dumps(summary,indent=2))
    except BaseException as e:
        state.update(status='FAILED',error=repr(e));save();raise
    finally:
        for m in maps:m.close()
        for f in readers:f.close()
        for f in files:f.close()
        for b in buffers:b.close()
if __name__=='__main__':
    import sys
    if sys.argv[1:]==['--confirm-map']:confirm_mapping()
    else:
        assert len(sys.argv)==1
        main()
