"""Create a never-mapped direct-I/O shadow; exact prefix SHA256, zero sector padding."""
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
from ctypes import wintypes as w

sys.path.insert(0,str(Path(__file__).resolve().parent))
import probe_unmapped as io

ROOT=Path(r'C:\Users\User\Strata-Adrian-control\runs\unmapped-shadow-20261029')
SRC=io.SOURCE
DST=ROOT/'first-shard.direct'
CHUNK=2*1024**2
QD=16

def main():
    assert os.environ.get('COMPUTERNAME','').upper()=='DESKTOP-LKMLUPC'
    assert time.time()<1793226600,'past 06:30 prepare cutoff'
    ROOT.mkdir(exist_ok=True)
    assert not DST.exists() and not (ROOT/'copy.json').exists(),'copy already attempted; no overwrite/restart'
    stat=SRC.stat();size=stat.st_size;padded=(size+4095)//4096*4096
    assert size==47039860096
    assert shutil.disk_usage(ROOT).free>padded+10*1024**3,'insufficient free disk with 10GiB reserve'
    state=dict(status='START',pid=os.getpid(),source=str(SRC),destination=str(DST),source_bytes=size,shadow_bytes=padded,padding_bytes=padded-size,source_mtime_ns=stat.st_mtime_ns,copied=0,verified=0)
    def save():
        temp=ROOT/'copy.tmp';temp.write_text(json.dumps(state,indent=2));temp.replace(ROOT/'copy.json')
    save()
    files=[];buffers=[]
    def read_valid(b,f,off,ask,valid):
        b.start(f,off,ask)
        if io.wait(b.ev,5000)!=0:
            io.cancel(f.h,c.byref(b.ov));raise RuntimeError('direct read timeout; no fallback')
        got=w.DWORD()
        if not io.result(f.h,c.byref(b.ov),c.byref(got),False):raise c.WinError(c.get_last_error())
        b.pending=False
        assert got.value==valid,(off,got.value,valid)
    try:
        src=io.File(SRC);files.append(src);dst=io.File(DST,True);files.append(dst)
        buffers=[io.Buffer(CHUNK) for _ in range(QD)]
        digest=hashlib.sha256();started=time.monotonic()
        for base in range(0,padded,CHUNK*QD):
            assert time.time()<1793226600,'copy cutoff'
            batch=[]
            for b,off in zip(buffers,range(base,min(base+CHUNK*QD,padded),CHUNK)):
                valid=min(CHUNK,size-off);ask=(valid+4095)//4096*4096
                if valid<ask:c.memset(b.p,0,ask)
                b.start(src,off,ask);batch.append((b,off,ask,valid))
            for b,off,ask,valid in batch:
                if io.wait(b.ev,5000)!=0:io.cancel(src.h,c.byref(b.ov));raise RuntimeError('source timeout')
                got=w.DWORD()
                if not io.result(src.h,c.byref(b.ov),c.byref(got),False):raise c.WinError(c.get_last_error())
                b.pending=False;assert got.value==valid,(off,got.value,valid)
                digest.update(c.string_at(b.p,valid));b.start(dst,off,ask,True)
            for b,off,ask,valid in batch:b.finish()
            state.update(status='COPY',copied=min(base+CHUNK*QD,size),elapsed_seconds=time.monotonic()-started)
            if base%(1024**3)==0:save()
        state.update(status='VERIFY',source_sha256=digest.hexdigest(),copied=size);save()
        verify=hashlib.sha256()
        for base in range(0,padded,CHUNK*QD):
            assert time.time()<1793226600,'verify cutoff'
            batch=[]
            for b,off in zip(buffers,range(base,min(base+CHUNK*QD,padded),CHUNK)):
                ask=min(CHUNK,padded-off);b.start(dst,off,ask);batch.append((b,off,ask,min(CHUNK,size-off)))
            for b,off,ask,valid in batch:
                b.finish();verify.update(c.string_at(b.p,valid))
                if valid<ask:assert c.string_at(b.p+valid,ask-valid)==bytes(ask-valid),'nonzero tail padding'
            state.update(verified=min(base+CHUNK*QD,size),elapsed_seconds=time.monotonic()-started)
            if base%(1024**3)==0:save()
        assert verify.digest()==digest.digest(),'full prefix hash mismatch'
        after=SRC.stat();assert after.st_size==size and after.st_mtime_ns==stat.st_mtime_ns,'source changed during copy'
        state.update(status='DONE',shadow_prefix_sha256=verify.hexdigest(),elapsed_seconds=time.monotonic()-started);save()
        print(json.dumps(state,indent=2))
    except BaseException as e:
        state.update(status='FAILED',error=repr(e));save();raise
    finally:
        for f in files:f.close()
        for b in buffers:b.close()
if __name__=='__main__':main()
