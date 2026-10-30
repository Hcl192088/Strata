"""Offline finite-grid allocation screen; preserves the established simulator semantics."""
import ctypes
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import numpy as np

ROOT=Path(r'D:\strata')
OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'tools'))
import ram_policy_sim_20261018 as S
import simulate_ram_routing as B

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()

def optimize(curves,sizes,basecaps,requests):
    unit=1024**2
    weights=[[math.ceil((c-basecaps[l])*sizes[l]/unit) for c in curves[l]['caps']] for l in range(48)]
    lo=sum(min(w) for w in weights);hi=sum(max(w) for w in weights);zero=-lo;n=hi-lo+1
    dp=np.full(n,np.inf);dp[zero]=0
    parents=[]
    for l in range(48):
        nxt=np.full(n,np.inf);par=np.full(n,-1,dtype=np.int16)
        reads=np.array(curves[l]['reads'])+np.array(curves[l]['adapt'])
        costs=reads[:,requests].sum(axis=1)*sizes[l]
        for j,w in enumerate(weights[l]):
            if w>=0:src=slice(0,n-w);dst=slice(w,n)
            else:src=slice(-w,n);dst=slice(0,n+w)
            v=dp[src]+costs[j]
            take=v<nxt[dst]
            nxt[dst][take]=v[take];par[dst][take]=j
        dp=nxt;parents.append(par)
    pos=int(np.argmin(dp[:zero+1]));objective=float(dp[pos]);indices=[]
    for l in reversed(range(48)):
        j=int(parents[l][pos])
        if j<0:raise RuntimeError('DP_BACKTRACK_FAILED')
        indices.append(j);pos-=weights[l][j]
    if pos!=zero:raise RuntimeError('DP_ORIGIN_MISMATCH')
    indices.reverse()
    caps=[curves[l]['caps'][j] for l,j in enumerate(indices)]
    if sum(c*sizes[l] for l,c in enumerate(caps))>sum(c*sizes[l] for l,c in enumerate(basecaps)):
        raise RuntimeError('BYTE_BUDGET_EXCEEDED')
    return indices,caps,objective

def gather(curves,indices,sizes):
    reads=np.zeros(11,dtype=np.int64);ad=np.zeros(11,dtype=np.int64);bs=np.zeros(11,dtype=np.int64)
    for l,j in enumerate(indices):
        rr=np.array(curves[l]['reads'][j]);aa=np.array(curves[l]['adapt'][j])
        reads+=rr;ad+=aa;bs+=(rr+aa)*sizes[l]
    return {'reads_req':reads.tolist(),'adapt_req':ad.tolist(),'ssd_bytes_req':bs.tolist(),
            'ssd_bytes_total':int(bs.sum()),'heldout_bytes':int(bs[5:].sum())}

def main():
    target=OUT/'ram-quota-results.json'
    if target.exists():raise RuntimeError('EXISTING_RESULT_NO_RERUN')
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(),0x4000)
    t0=time.monotonic()
    d=ROOT/'state/ram-policy-sim-20261018/capture-01'
    trace=d/'routing-dump.bin';profile=ROOT/'state/trace-baseline-profile.bin';native=ROOT/'state/trace-native-experts.txt'
    hashes={str(p):sha(p) for p in [trace,profile,native]}
    if hashes[str(trace)]!='1A151333E854138EED0A9354B758C55799B2DF40EC2BC5CDC966385BF714E34C':
        raise RuntimeError('TRACE_SHA_MISMATCH')
    bounds=json.loads((d/'bounds.json').read_text())['bounds']
    if sum(bounds)!=8623:raise RuntimeError('WINDOW_COUNT_MISMATCH')
    rank=B.profile(profile);sizes=B.sizes(native)
    initial,selected=S.init_sets_from(rank,3153,21474406400,sizes)
    basecaps=[len(x) for x in initial]
    gpu=set(rank[:3153]);complement=[[e for ll,e in rank[3153:] if ll==l] for l in range(48)]
    E=S.build_events(trace,rank,3153,bounds)
    seq=[[] for _ in range(48)]
    for x in E.timeline:
        if x[0]=='X':
            _,l,i,o=x;seq[l].append(('X',i,o))
        else:
            _,w,l,needed,routed,req=E.ev[x[1]]
            seq[l].append(('A',needed,list(routed),req))
    curves=[]
    for l in range(48):
        if time.monotonic()-t0>600:raise RuntimeError('OFFLINE_600S_DEADLINE')
        maximum=len(complement[l])
        caps=sorted(set(list(range(16,maximum+1,16))+[basecaps[l],maximum]))
        nc=len(caps);res=np.zeros((nc,512),dtype=bool);touch=np.zeros((nc,512),dtype=np.int64)
        for j,c in enumerate(caps):res[j,complement[l][:c]]=True
        reads=np.zeros((nc,11),dtype=np.int64);adapt=np.zeros_like(reads)
        clock=0;request=0
        for item in seq[l]:
            if item[0]=='X':
                _,i,o=item;mask=res[:,i].copy();adapt[:,request]+=~mask
                res[mask,i]=False;res[mask,o]=True
                continue
            _,needed,routed,request=item;clock+=1
            for e in needed:
                hit=res[:,e];touch[hit,e]=clock
            for e in needed:
                mm=np.flatnonzero(~res[:,e])
                if not len(mm):continue
                reads[mm,request]+=1
                allowed=res[mm].copy();allowed[:,routed]=False
                good=allowed.any(axis=1)
                if not good.any():continue
                rr=mm[good];score=touch[rr].copy();score[~allowed[good]]=2**60
                victims=score.argmin(axis=1)
                res[rr,victims]=False;res[rr,e]=True;touch[rr,e]=clock
        curves.append({'layer':l,'blob_bytes':sizes[l],'caps':caps,'reads':reads.tolist(),'adapt':adapt.tolist()})
        print('layer',l+1,'of48','elapsed',round(time.monotonic()-t0,1),flush=True)
        (OUT/'ram-quota-progress.json').write_text(json.dumps({'layers':l+1,'elapsed_s':time.monotonic()-t0}))
    (OUT/'ram-quota-curves.json').write_text(json.dumps(curves))
    baseind=[curves[l]['caps'].index(c) for l,c in enumerate(basecaps)]
    baseline=gather(curves,baseind,sizes)
    reference=json.loads((d/'warm_policies.json').read_text())['policies']['LRU_engine']
    if baseline['reads_req']!=reference['reads_req'] or baseline['adapt_req']!=reference['adapt_ssd_req']:
        raise RuntimeError('ENGINE_BASELINE_REPRODUCTION_FAILED '+json.dumps({'new':baseline,'reference':reference}))
    train_idx,train_caps,_=optimize(curves,sizes,basecaps,list(range(5)))
    oracle_idx,oracle_caps,_=optimize(curves,sizes,basecaps,list(range(11)))
    candidate=gather(curves,train_idx,sizes);oracle=gather(curves,oracle_idx,sizes)
    held=1-candidate['heldout_bytes']/baseline['heldout_bytes']
    out={'status':'COMPLETED','scope':'offline old single-neuro trace; finite-grid allocation, not runtime speed',
      'input_sha256':hashes,'windows':8623,'requests':11,'train_requests':list(range(5)),
      'heldout_requests':list(range(5,11)),'same_gpu_events':dict(E.counters),
      'baseline_read_reproduction_exact':True,'baseline_caps':basecaps,'candidate_caps':train_caps,'oracle_caps':oracle_caps,
      'baseline_bytes':sum(c*sizes[l] for l,c in enumerate(basecaps)),
      'candidate_bytes':sum(c*sizes[l] for l,c in enumerate(train_caps)),
      'oracle_bytes':sum(c*sizes[l] for l,c in enumerate(oracle_caps)),
      'baseline':baseline,'candidate':candidate,'finite_grid_oracle':oracle,
      'heldout_ssd_byte_reduction_percent':held*100,
      'all_trace_ssd_byte_reduction_percent':100*(1-candidate['ssd_bytes_total']/baseline['ssd_bytes_total']),
      'oracle_ssd_byte_reduction_percent':100*(1-oracle['ssd_bytes_total']/baseline['ssd_bytes_total']),
      'decision':'CONTINUE_COST_ANALYSIS_ONLY' if held>=0.25 else 'NO_GO_BOUNDED_SCREEN',
      'elapsed_s':time.monotonic()-t0}
    target.write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2),flush=True)

if __name__=='__main__':main()
