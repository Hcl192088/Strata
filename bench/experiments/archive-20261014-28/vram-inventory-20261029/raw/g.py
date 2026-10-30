import struct,sys,collections
def rd(f):
    d=open(f,'rb').read();o=[0]
    def u(fmt):
        s=struct.calcsize(fmt);v=struct.unpack_from('<'+fmt,d,o[0]);o[0]+=s;return v[0] if len(v)==1 else v
    def st():
        n=u('Q');s=d[o[0]:o[0]+n].decode('utf8','replace');o[0]+=n;return s
    def val(t):
        if t==8:return st()
        if t==9:
            et=u('I');n=u('Q')
            if et in(8,9):
                for _ in range(n):val(et)
                return None
            sz={0:1,1:1,2:2,3:2,4:4,5:4,6:4,7:1,10:8,11:8,12:8}[et];o[0]+=sz*n;return None
        return u({0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'B',10:'Q',11:'q',12:'d'}[t])
    assert d[:4]==b'GGUF';o[0]=4;ver=u('I');nt=u('Q');nk=u('Q');kv={}
    for _ in range(nk):
        k=st();t=u("I");print(k,t) if len(kv)<3 or len(kv)>nk-3 else 0;kv[k]=val(t)
    ts=[]
    for _ in range(nt):
        n=st();nd=u('I');dims=[u('Q') for _ in range(nd)];ty=u('I');off=u('Q');ts.append((n,dims,ty,off))
    return kv,ts
