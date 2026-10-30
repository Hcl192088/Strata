"""Bounded read-only weight screen; no engine requests or deployment."""
import ctypes
from ctypes import wintypes as W
import hashlib
import json
import lzma
from pathlib import Path
import socket
import statistics
import sys
import time
import urllib.request
import zlib
import psutil

ROOT = Path(r'C:\Users\User\Strata-Adrian-control')
OUT = ROOT / 'runs' / 'lossless-screen-20261029'
BEST = ROOT / 'bench/results/2026-10-29-native-pipe/BEST.json'
EXPECTED_PIDS = {29576,11236,32632,32348,5280,4352,27744}
CODECS = ['xpress_huff', 'zlib1', 'lzma1']

def sha(data):
    return hashlib.sha256(data).hexdigest().upper()

def file_sha(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest().upper()

def get_metrics():
    with urllib.request.urlopen('http://<tailscale-host>:8080/metrics', timeout=6) as r:
        m = json.load(r)
    return {'state':m['live']['state'], 'engine':{k:m['engine'].get(k) for k in
            ['expert_slots','arena_mib','pool_workers','spec','mtp_max']}}

def gate(best):
    own = psutil.Process()
    permitted = EXPECTED_PIDS | {own.pid} | {p.pid for p in own.parents()}
    relevant = []
    for p in psutil.process_iter(['pid','ppid','name','cmdline','exe']):
        n = p.info['name'].lower()
        if n in {'strata.exe','llama-server.exe','python.exe','pythonw.exe','cmake.exe',
                 'ninja.exe','nvcc.exe','cl.exe','nsys.exe','wpr.exe','zstd.exe','7z.exe'}:
            relevant.append(p.info)
            if p.pid not in permitted:
                raise RuntimeError('PROCESS_GATE: ' + json.dumps(p.info))
    engine = [p for p in relevant if p['name'].lower() == 'strata.exe']
    if len(engine) != 1 or engine[0]['pid'] != 27744:
        raise RuntimeError('LIVE_PROCESS_CHANGED')
    if file_sha(engine[0]['exe']) != best['binary_sha256']:
        raise RuntimeError('BINARY_MISMATCH')
    if file_sha(best['config_path']) != best['config_sha256']:
        raise RuntimeError('CONFIG_MISMATCH')
    m = get_metrics()
    if m['state'] != 'idle':
        raise RuntimeError('API_NOT_IDLE')
    if m['engine']['expert_slots'] != 3153 or m['engine']['arena_mib'] != 20479:
        raise RuntimeError('CAPACITY_MISMATCH')
    free = psutil.virtual_memory().available
    if free < 1024**3:
        raise RuntimeError('AVAILABLE_RAM_BELOW_1GiB')
    return {'at':time.time(),'processes':relevant,'metrics':m,'available_bytes':free}

class Xpress:
    def __init__(self):
        self.api = ctypes.WinDLL('cabinet.dll', use_last_error=True)
        for name in ('CreateCompressor','CreateDecompressor'):
            fn = getattr(self.api,name)
            fn.argtypes = [W.DWORD,ctypes.c_void_p,ctypes.POINTER(W.HANDLE)]
            fn.restype = W.BOOL
        for name in ('Compress','Decompress'):
            fn = getattr(self.api,name)
            fn.argtypes = [W.HANDLE,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,
                           ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
            fn.restype = W.BOOL
        for name in ('CloseCompressor','CloseDecompressor'):
            getattr(self.api,name).argtypes = [W.HANDLE]
        self.c, self.d = W.HANDLE(), W.HANDLE()
        if not self.api.CreateCompressor(4,None,ctypes.byref(self.c)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not self.api.CreateDecompressor(4,None,ctypes.byref(self.d)):
            raise ctypes.WinError(ctypes.get_last_error())
    def compress(self,raw):
        buf=ctypes.create_string_buffer(len(raw)*2+65536)
        n=ctypes.c_size_t()
        if not self.api.Compress(self.c,ctypes.c_char_p(raw),len(raw),buf,len(buf),ctypes.byref(n)):
            raise ctypes.WinError(ctypes.get_last_error())
        return buf.raw[:n.value]
    def decompress(self,data,size):
        buf=ctypes.create_string_buffer(size)
        n=ctypes.c_size_t()
        if not self.api.Decompress(self.d,ctypes.c_char_p(data),len(data),buf,size,ctypes.byref(n)):
            raise ctypes.WinError(ctypes.get_last_error())
        if n.value != size:
            raise RuntimeError('DECOMPRESSED_SIZE_MISMATCH')
        return buf.raw
    def close(self):
        self.api.CloseCompressor(self.c)
        self.api.CloseDecompressor(self.d)

def summarize(rows):
    out={}
    for name in CODECS:
        rr=[r for r in rows if r['codec']==name]
        if not rr:
            continue
        raw=sum(r['raw_bytes'] for r in rr)
        packed=sum(r['compressed_bytes'] for r in rr)
        secs=sum(r['decompress_median_s'] for r in rr)
        ratio=packed/raw
        speed=raw/secs/1e9
        groups={}
        for pair in sorted({r['pair'] for r in rr}):
            pp=[r for r in rr if r['pair']==pair]
            rb=sum(r['raw_bytes'] for r in pp)
            groups[pair]={'samples':len(pp),'ratio':sum(r['compressed_bytes'] for r in pp)/rb,
                          'decode_GB_s':rb/sum(r['decompress_median_s'] for r in pp)/1e9}
        out[name]={'samples':len(rr),'raw_bytes':raw,'compressed_bytes':packed,'ratio':ratio,
                   'saving_percent':100*(1-ratio),'decode_GB_s':speed,
                   'median_expert_decode_ms':statistics.median(r['decompress_median_s'] for r in rr)*1000,
                   'ideal_20GiB_equivalent_GiB':20/ratio,
                   'screen_pass':ratio<=0.90 and speed>=3.0,'by_pair':groups}
    return out

def main():
    if socket.gethostname() != 'DESKTOP-LKMLUPC':
        raise RuntimeError('HOST_MISMATCH')
    if not OUT.is_dir():
        raise RuntimeError('RUN_ROOT_NOT_STAGED')
    result_path=OUT/'results.json'
    if result_path.exists():
        raise RuntimeError('EXISTING_TERMINAL_RESULT_NO_RERUN')
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    best=json.loads(BEST.read_text(encoding='utf-8-sig'))
    cfg=json.loads(Path(best['config_path']).read_text(encoding='utf-8-sig'))
    pack=Path(cfg['args'][cfg['args'].index('--pack')+1])
    meta=pack/'native_experts.txt'
    weights=pack/'experts.bin'
    layers=[]
    for line in meta.read_text().splitlines():
        if line and not line.startswith('#'):
            q=line.split()
            layers.append(dict(layer=int(q[0]),gu=int(q[1]),down=int(q[2]),
                               offset=int(q[3]),size=int(q[4])))
    if [q['layer'] for q in layers] != list(range(48)):
        raise RuntimeError('LAYER_METADATA_MISMATCH')
    result={'task_id':'LUNA-20261012-027','status':'RUNNING','host':socket.gethostname(),
            'started_at':time.time(),'code_sha256':file_sha(__file__),
            'binary_sha256':best['binary_sha256'],'config_sha256':best['config_sha256'],
            'source':best['source'],'pack':str(pack),'weight_size':weights.stat().st_size,
            'weight_mtime_ns':weights.stat().st_mtime_ns,'metadata_sha256':file_sha(meta),
            'codecs':CODECS,'zstandard_lz4_not_installed':True,'rows':[],'layer_gates':[]}
    xp=None
    try:
        result['pre_gate']=gate(best)
        xp=Xpress()
        deadline=time.monotonic()+240
        with weights.open('rb',buffering=0) as f:
            for layer in layers:
                if time.monotonic()>deadline:
                    raise RuntimeError('SCREEN_DEADLINE_240S')
                gg=gate(best)
                result['layer_gates'].append({'layer':layer['layer'],'at':gg['at'],
                     'pids':[p['pid'] for p in gg['processes']],'available_bytes':gg['available_bytes']})
                for ei,expert in enumerate((0,257)):
                    offset=layer['offset']+expert*layer['size']
                    if offset+layer['size']>result['weight_size']:
                        raise RuntimeError('SAMPLE_OUT_OF_BOUNDS')
                    f.seek(offset)
                    raw=f.read(layer['size'])
                    if len(raw)!=layer['size']:
                        raise RuntimeError('SHORT_READ')
                    original_sha=sha(raw)
                    sample_index=layer['layer']*2+ei
                    for ci in range(3):
                        if time.monotonic()>deadline:
                            raise RuntimeError('SCREEN_DEADLINE_240S')
                        name=CODECS[(sample_index+ci)%3]
                        start=time.perf_counter()
                        if name=='xpress_huff':
                            data=xp.compress(raw)
                        elif name=='zlib1':
                            data=zlib.compress(raw,level=1)
                        else:
                            data=lzma.compress(raw,preset=1)
                        compression_s=time.perf_counter()-start
                        ts=[]
                        for _ in range(7):
                            start=time.perf_counter()
                            if name=='xpress_huff':
                                restored=xp.decompress(data,len(raw))
                            elif name=='zlib1':
                                restored=zlib.decompress(data)
                            else:
                                restored=lzma.decompress(data)
                            ts.append(time.perf_counter()-start)
                            if restored!=raw:
                                raise RuntimeError('BYTE_PARITY_MISMATCH')
                        if sha(restored)!=original_sha:
                            raise RuntimeError('SHA_PARITY_MISMATCH')
                        row={'layer':layer['layer'],'expert':expert,'offset':offset,
                             'pair':f"{layer['gu']}/{layer['down']}",'codec':name,
                             'raw_sha256':original_sha,'compressed_sha256':sha(data),
                             'raw_bytes':len(raw),'compressed_bytes':len(data),
                             'compress_s':compression_s,'decompress_s':ts,
                             'decompress_median_s':statistics.median(ts),'parity':True}
                        result['rows'].append(row)
                    copies=[]
                    for _ in range(7):
                        start=time.perf_counter()
                        copied=memoryview(raw).tobytes()
                        copies.append(time.perf_counter()-start)
                        if copied!=raw:
                            raise RuntimeError('COPY_PARITY_MISMATCH')
                    result['rows'][-1]['copy_reference_median_s']=statistics.median(copies)
                    del raw,data,restored,copied
                if layer['layer']%4==3:
                    (OUT/'progress.json').write_text(json.dumps({'completed_layers':layer['layer']+1,
                        'completed_rows':len(result['rows']),'elapsed_s':time.time()-result['started_at']}))
                    print('completed_layers',layer['layer']+1,flush=True)
        result['post_gate']=gate(best)
        if (weights.stat().st_size,weights.stat().st_mtime_ns)!=(result['weight_size'],result['weight_mtime_ns']):
            raise RuntimeError('WEIGHT_FILE_METADATA_CHANGED')
        result['status']='COMPLETED'
    except Exception as e:
        result['status']='PARTIAL_FAILED'
        result['error']=str(e)
    finally:
        if xp:
            xp.close()
        result['elapsed_s']=time.time()-result['started_at']
        result['summary']=summarize(result['rows'])
        result['peak_working_set_bytes']=psutil.Process().memory_info().peak_wset
        result_path.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps({k:result.get(k) for k in ['status','error','elapsed_s','peak_working_set_bytes','summary']}),flush=True)
    return 0 if result['status']=='COMPLETED' else 2

if __name__=='__main__':
    sys.exit(main())
