import json,struct,hashlib,datetime
from pathlib import Path
N=Path(r'C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029')
O=N.parent/'native-pipeline-20261029/build/strata.exe';F=N/'build/strata.exe'
def pe(p):
 b=p.read_bytes();o=struct.unpack_from('<I',b,0x3c)[0];assert b[o:o+4]==b'PE\0\0'
 ts=struct.unpack_from('<I',b,o+8)[0];n=struct.unpack_from('<H',b,o+6)[0];opt=struct.unpack_from('<H',b,o+20)[0]
 secs={}
 for i in range(n):
  q=o+24+opt+40*i;name=b[q:q+8].rstrip(b'\0').decode();size,start=struct.unpack_from('<II',b,q+16)
  secs[name]={'bytes':size,'sha256':hashlib.sha256(b[start:start+size]).hexdigest().upper()}
 return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest().upper(),pe_timestamp=ts,pe_time_utc=datetime.datetime.fromtimestamp(ts,datetime.timezone.utc).isoformat(),pe_offset=o,sections=secs)
a=pe(O);b=pe(F)
x=bytearray(O.read_bytes());y=bytearray(F.read_bytes())
x[a['pe_offset']+8:a['pe_offset']+12]=b'\0'*4;y[b['pe_offset']+8:b['pe_offset']+12]=b'\0'*4
r={'original':a,'fresh':b,'equal_after_zeroing_coff_timestamp':x==y,'section_equal':{k:a['sections'][k]==b['sections'].get(k) for k in a['sections']},'scope':'PE header and section observations; no claim all differing bytes are timestamp-only. Fresh vs incremental build and source/build paths differ.'}
(N/'binary-comparison.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r,indent=2))
