import ctypes as C, ctypes.wintypes as W, time, json, collections, pathlib, os
k=C.WinDLL('kernel32',use_last_error=True)
H=C.c_void_p; U=W.ULONG
for name,args,ret in [('GetCurrentThread',[],H),('GetCurrentProcess',[],H),('SetPriorityClass',[H,W.DWORD],W.BOOL),('GetPriorityClass',[H],W.DWORD),('GetSystemCpuSetInformation',[H,U,C.POINTER(U),H,U],W.BOOL),('GetThreadSelectedCpuSets',[H,C.POINTER(U),U,C.POINTER(U)],W.BOOL),('SetThreadSelectedCpuSets',[H,C.POINTER(U),U],W.BOOL)]:
 f=getattr(k,name);f.argtypes=args;f.restype=ret
class PN(C.Structure): _fields_=[('Group',W.WORD),('Number',W.BYTE),('Reserved',W.BYTE)]
class GA(C.Structure): _fields_=[('Mask',C.c_size_t),('Group',W.WORD),('Reserved',W.WORD*3)]
k.GetCurrentProcessorNumberEx.argtypes=[C.POINTER(PN)]
k.SetThreadGroupAffinity.argtypes=[H,C.POINTER(GA),C.POINTER(GA)]; k.SetThreadGroupAffinity.restype=W.BOOL
k.GetThreadGroupAffinity.argtypes=[H,C.POINTER(GA)];k.GetThreadGroupAffinity.restype=W.BOOL
p=k.GetCurrentProcess();t=k.GetCurrentThread()
def check(ok):
 if not ok: raise C.WinError(C.get_last_error())
check(k.SetPriorityClass(p,0x4000))
n=U();k.GetSystemCpuSetInformation(None,0,C.byref(n),p,0)
b=C.create_string_buffer(n.value);check(k.GetSystemCpuSetInformation(b,n.value,C.byref(n),p,0))
rows=[];off=0
while off<n.value:
 raw=b.raw; size=int.from_bytes(raw[off:off+4],'little');typ=int.from_bytes(raw[off+4:off+8],'little')
 if size<8:raise RuntimeError('invalid CPU set size')
 if typ==0:
  rows.append(dict(id=int.from_bytes(raw[off+8:off+12],'little'),group=int.from_bytes(raw[off+12:off+14],'little'),lp=raw[off+14],core=raw[off+15],efficiency=raw[off+18],flags=raw[off+19]))
 off+=size
selected=[r for r in rows if r['group']==0 and r['lp']==0 and (not r['flags']&2 or r['flags']&4)]
assert len(selected)==1
id=U(selected[0]['id']);count=U()
k.GetThreadSelectedCpuSets(t,None,0,C.byref(count));prior=(U*count.value)()
if count.value:check(k.GetThreadSelectedCpuSets(t,prior,count.value,C.byref(count)))
ga=GA();check(k.GetThreadGroupAffinity(t,C.byref(ga)))
def sample(mode):
 pn=PN(); hist=collections.Counter();initial=[];start=time.perf_counter();cpu=time.process_time()
 for batch in range(100):
  for i in range(100):
   k.GetCurrentProcessorNumberEx(C.byref(pn));hist[f'{pn.Group}:{pn.Number}']+=1
   if batch==0 and i<10:initial.append([pn.Group,pn.Number])
   x=(i*37+batch)**2
  deadline=start+(batch+1)*0.02
  time.sleep(max(0,deadline-time.perf_counter()))
 outside=sum(v for key,v in hist.items() if key!='0:0')
 return dict(mode=mode,n=sum(hist.values()),outside=outside,fraction=outside/sum(hist.values()),histogram=dict(hist),initial=initial,elapsed_s=time.perf_counter()-start,cpu_s=time.process_time()-cpu)
check(k.SetThreadSelectedCpuSets(t,C.byref(id),1))
read=(U*8)();check(k.GetThreadSelectedCpuSets(t,read,8,C.byref(count)))
result=dict(pid=os.getpid(),priority=k.GetPriorityClass(p),mapping=rows,selected_id=id.value,readback=list(read)[:count.value],prior_selected=list(prior),prior_group=ga.Group,prior_mask=ga.Mask)
result['soft']=sample('SetThreadSelectedCpuSets')
check(k.SetThreadSelectedCpuSets(t,prior,len(prior)))
hard=GA();hard.Group=0;hard.Mask=1
check(k.SetThreadGroupAffinity(t,C.byref(hard),None))
result['hard']=sample('SetThreadGroupAffinity')
pathlib.Path(__file__).with_name('probe-result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
