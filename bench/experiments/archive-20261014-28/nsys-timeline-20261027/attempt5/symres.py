"""Resolve RVAs of strata.exe to function names with dbghelp + the build PDB (read-only, no rebuild).
usage: python symres.py rvas.json out.json   (rvas.json = list of ints)
"""
import ctypes, json, sys
from ctypes import wintypes

EXE = r'C:\Users\User\Strata-Adrian-control\runs\ram-lru-20261013\build\strata.exe'
PDBDIR = r'C:\Users\User\Strata-Adrian-control\runs\ram-lru-20261013\build'
BASE = 0x140000000
SIZE = 0x32EB000

dbg = ctypes.WinDLL('dbghelp.dll')
dbg.SymInitializeW.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, wintypes.BOOL]
dbg.SymSetOptions.argtypes = [wintypes.DWORD]
dbg.SymLoadModuleExW.restype = ctypes.c_uint64
dbg.SymLoadModuleExW.argtypes = [wintypes.HANDLE, wintypes.HANDLE, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                 ctypes.c_uint64, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
MAXN = 1024


class SYMBOL_INFOW(ctypes.Structure):
    _fields_ = [('SizeOfStruct', wintypes.ULONG), ('TypeIndex', wintypes.ULONG), ('Reserved', ctypes.c_uint64 * 2),
                ('Index', wintypes.ULONG), ('Size', wintypes.ULONG), ('ModBase', ctypes.c_uint64),
                ('Flags', wintypes.ULONG), ('Value', ctypes.c_uint64), ('Address', ctypes.c_uint64),
                ('Register', wintypes.ULONG), ('Scope', wintypes.ULONG), ('Tag', wintypes.ULONG),
                ('NameLen', wintypes.ULONG), ('MaxNameLen', wintypes.ULONG), ('Name', ctypes.c_wchar * MAXN)]


class IMAGEHLP_LINEW64(ctypes.Structure):
    _fields_ = [('SizeOfStruct', wintypes.DWORD), ('Key', ctypes.c_void_p), ('LineNumber', wintypes.DWORD),
                ('FileName', wintypes.LPWSTR), ('Address', ctypes.c_uint64)]


h = ctypes.c_void_p(0x1234)
SYMOPT_UNDNAME, SYMOPT_DEFERRED, SYMOPT_LINES = 0x2, 0x4, 0x10
dbg.SymSetOptions(SYMOPT_UNDNAME | SYMOPT_LINES)
assert dbg.SymInitializeW(h, PDBDIR, False), ctypes.GetLastError()
b = dbg.SymLoadModuleExW(h, None, EXE, None, BASE, SIZE, None, 0)
assert b, ctypes.GetLastError()

rvas = json.load(open(sys.argv[1]))
out = {}
for rva in rvas:
    addr = BASE + rva
    si = SYMBOL_INFOW()
    si.SizeOfStruct = 88
    si.MaxNameLen = MAXN
    disp = ctypes.c_uint64(0)
    ok = dbg.SymFromAddrW(h, ctypes.c_uint64(addr), ctypes.byref(disp), ctypes.byref(si))
    name = si.Name if ok else None
    ln = None
    li = IMAGEHLP_LINEW64()
    li.SizeOfStruct = ctypes.sizeof(IMAGEHLP_LINEW64)
    d2 = wintypes.DWORD(0)
    if dbg.SymGetLineFromAddrW64(h, ctypes.c_uint64(addr), ctypes.byref(d2), ctypes.byref(li)):
        ln = '%s:%d' % (li.FileName.split('\\')[-1], li.LineNumber)
    out[str(rva)] = [name, int(disp.value) if ok else None, ln, int(si.Size) if ok else None]
json.dump(out, open(sys.argv[2], 'w'))
print('resolved', sum(1 for v in out.values() if v[0]), 'of', len(out))
