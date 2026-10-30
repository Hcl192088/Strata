"""Reduce a tracerpt CSV (WPR/ETW kernel trace) to the I/O rows of the strata.exe process. stdlib only.
usage: python etl_filter.py wpr-X.csv out_prefix
  out_prefix.io.csv      kind,ft,pid,tid,f...   (ft = FILETIME 100 ns units, UTC)
     FREAD/FWRITE: offset,size,irp,fileobj,issuing_tid,ioflags,filekey
     FEND   : irp,extra,status            (FileIo OperationEnd, completion of an irp)
     DINIT  : irp,issuing_tid
     DREAD  : bytes,byteoffset,irp,resp_time_raw,issuing_tid,fileobj,irpflags   (ft = completion)
     HFAULT : initial_time_ft,readoffset,va,fileobj,tthread,bytes
  out_prefix.names.csv   fileobj,path
  out_prefix.stacks.csv  kind,ft,tid,frames...  (StackWalk rows right after FREAD/HFAULT of strata threads)
  out_prefix.images.csv  base,size,pid,...,path (Image rows of strata.exe/nvcuda/ntoskrnl)
"""
import csv, sys

src, pref = sys.argv[1], sys.argv[2]
csv.field_size_limit(1 << 28)


def hx(x):
    x = x.strip()
    try:
        return int(x, 16) if x.lower().startswith('0x') else int(x)
    except ValueError:
        return None


def rows(path):
    with open(path, encoding='utf-8', errors='replace', newline='') as f:
        for line in f:
            yield line


# ---- pass 1: strata pids and thread ids
strata_pids, strata_tids = set(), set()
procs = {}
for line in rows(src):
    s = line.lstrip()[:8]
    if s.startswith('Process,') and 'strata.exe' in line.lower():
        r = next(csv.reader([line], skipinitialspace=True))
        if r[1].strip() in ('DCStart', 'Start', 'DCEnd'):
            p = hx(r[20])
            if p:
                strata_pids.add(p)
for line in rows(src):
    s = line.lstrip()[:7]
    if s.startswith('Thread,'):
        r = next(csv.reader([line], skipinitialspace=True))
        if r[1].strip() in ('DCStart', 'DCEnd', 'Start') and len(r) > 20:
            if hx(r[19]) in strata_pids:
                t = hx(r[20])
                if t:
                    strata_tids.add(t)
print('strata pids', sorted(strata_pids), 'threads', len(strata_tids), flush=True)

# ---- pass 2
fio = open(pref + '.io.csv', 'w', encoding='utf-8', newline='')
fst = open(pref + '.stacks.csv', 'w', encoding='utf-8', newline='')
wio, wst = csv.writer(fio), csv.writer(fst)
names, refobj, images = {}, set(), []
last_ev = {}
base_off = None
nstack = 0
pend_irp = set()   # irps issued by strata (so FEND / DINIT rows can be kept)
keys = ('FileIo', 'DiskIo', 'PageFault', 'StackWalk', 'Image')
for line in rows(src):
    s = line.lstrip()
    if not s.startswith(keys):
        continue
    r = next(csv.reader([line], skipinitialspace=True))
    if len(r) < 19:
        continue
    n, t = r[0].strip(), r[1].strip()
    pid, tid, ft = hx(r[9]), hx(r[10]), r[16].strip()
    u = [c.strip() for c in r[19:]]
    if n == 'Image':
        low = line.lower()
        if 'strata.exe' in low or 'nvcuda64' in low or 'ntoskrnl' in low:
            images.append(u)
        continue
    if n == 'StackWalk':
        if t != 'Stack' or len(u) < 3:
            continue
        sp, st = hx(u[1]), hx(u[2])
        if st in last_ev:
            eft, kind = last_ev[st]
            raw = hx(u[0])
            cand = eft - raw
            if base_off is None:
                base_off = cand
            if abs(cand - base_off) <= 2:
                wst.writerow([kind, eft, st] + u[3:])
                nstack += 1
                del last_ev[st]
        continue
    if n == 'FileIo':
        if t in ('Read', 'Write'):
            if pid not in strata_pids:
                continue
            kind = 'FREAD' if t == 'Read' else 'FWRITE'
            wio.writerow([kind, ft, pid, tid, u[0], u[5], u[1], u[2], u[4], u[6], u[3]])
            refobj.add(u[3]); pend_irp.add(u[1])
            if kind == 'FREAD':
                last_ev[tid] = (int(ft), 'FREAD')
        elif t == 'OperationEnd':
            if u[0] in pend_irp:
                wio.writerow(['FEND', ft, pid, tid, u[0], u[1], u[2]])
        elif t == 'Create':
            names[u[1]] = u[-1].strip('"')
        elif t in ('FileCreate', 'FileRundown', 'Name'):
            names[u[0]] = u[-1].strip('"')
    elif n == 'DiskIo':
        tt = hx(u[-1]) if u else None
        if t == 'ReadInit' and tt in strata_tids:
            wio.writerow(['DINIT', ft, pid, tid, u[0], u[1]])
        elif t == 'Read' and tt in strata_tids:
            wio.writerow(['DREAD', ft, pid, tid, u[2], u[4], u[6], u[7], u[8], u[5], u[1]])
    elif n == 'PageFault' and t == 'HardFault':
        tt = hx(u[4])
        if tt in strata_tids:
            wio.writerow(['HFAULT', ft, pid, tid, u[0], u[1], u[2], u[3], u[4], u[5]])
            last_ev[tt] = (int(ft), 'HFAULT')
fio.close(); fst.close()
with open(pref + '.names.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f)
    for fo in refobj:
        if fo in names:
            w.writerow([fo, names[fo]])
with open(pref + '.images.csv', 'w', encoding='utf-8', newline='') as f:
    csv.writer(f).writerows(images)
print('stack_rows', nstack, 'base_off', base_off, 'images', len(images), 'names', len(names), flush=True)
