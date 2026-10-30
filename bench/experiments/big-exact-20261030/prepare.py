from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
src=Path(r'C:\Users\User\native-pipe-generic-20261029')
p=src/'src/kernels/cpu/iq_avx2.cpp'
s=p.read_text();prefix=s[:s.index('// ---- the row kernels, twice:')]
assert 'namespace strata::kernels::cpu' in prefix and 'struct Fmt32<121>' in prefix
(R/'kernel.cpp').write_text(prefix+(R/'kernel_tail.cpp').read_text(),encoding='utf-8')
paths=[p,src/'src/kernels/cpu/iq_avx2_rows.inl',src/'third_party/ggml/ggml-common.h',R/'kernel.cpp']
(R/'source-identity.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))
