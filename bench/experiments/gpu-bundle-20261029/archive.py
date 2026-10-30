from pathlib import Path
import zipfile,json,hashlib
R=Path(__file__).resolve().parent
files=[]
for p in R.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(R)
 if rel.parts[0] in ['source','build','__pycache__','harness']:continue
 if p.suffix in ['.zip','.tmp','.pyc']:continue
 files.append(p)
manifest=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=hashlib.file_digest(open(p,'rb'),'sha256').hexdigest().upper()) for p in files]
(R/'raw-manifest.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(R/'evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files+[R/'raw-manifest.json']:z.write(p,p.relative_to(R))
print(json.dumps(dict(files=len(files),bytes=sum(x['bytes'] for x in manifest),zip_bytes=(R/'evidence.zip').stat().st_size)))
