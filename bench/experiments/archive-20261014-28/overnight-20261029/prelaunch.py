import json,os
from pathlib import Path
import controller_roles as c
assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
c.identity()
v=c.final_verify()
allowed={pid for _,pid,_ in c.ns.api_pids()}|set(c.ns.watch_pids())
procs=c.ns.processes()
other=[p for p in procs if p['pid'] not in allowed]
assert not other,other
c.write('prelaunch.json',dict(verified=v,processes=procs))
print(json.dumps(v))
