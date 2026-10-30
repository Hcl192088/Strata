"""Insert STRATA_TIMER_RES (opt-in) into generate.cpp main(); run on the remote copy. usage: patch_timer.py <generate.cpp>"""
import hashlib, sys
p = sys.argv[1]
raw = open(p, 'rb').read()
assert hashlib.sha256(raw).hexdigest().upper() == '23B3FBA82C48756A4546F970CA97A7949218BAA482C12CFE4CC528FD6D975553', 'unexpected source'
open(p + '.before-timer', 'wb').write(raw)
txt = raw.decode('utf-8')
nl = '\r\n' if '\r\n' in txt else '\n'
anchor = '    std::setvbuf(stdout, nullptr, _IONBF, 0);' + nl
assert txt.count(anchor) == 1
block = r'''#if defined(_WIN32)
    // STRATA_TIMER_RES (opt-in, output unchanged): 1 = ask for a 1 ms timer resolution and stop Windows 11 from ignoring that request
    // for this process; 2 = additionally switch off the EcoQoS execution-speed throttle.  Nothing else in the engine sets either; the
    // pool's sleepers wake on the system timer tick (15.6 ms) when a wake-up is missed.  Loaded dynamically: no new link dependency.
    if (const char* tr = std::getenv("STRATA_TIMER_RES"); tr != nullptr && (tr[0] == '1' || tr[0] == '2')) {
        unsigned ok_period = 0xFFFFFFFFu;
        if (HMODULE mm = LoadLibraryA("winmm.dll")) {
            using TimeBeginPeriodFn = unsigned (WINAPI*)(unsigned);
            if (auto fn = reinterpret_cast<TimeBeginPeriodFn>(reinterpret_cast<void*>(GetProcAddress(mm, "timeBeginPeriod")))) ok_period = fn(1);
        }
        struct PowerThrottlingState { unsigned long Version; unsigned long ControlMask; unsigned long StateMask; };
        PowerThrottlingState st{1ul, 0x4ul /* IGNORE_TIMER_RESOLUTION */, 0ul};
        if (tr[0] == '2') st.ControlMask |= 0x1ul /* EXECUTION_SPEED */;
        int set_ok = -1;
        if (HMODULE k32 = GetModuleHandleA("kernel32.dll")) {
            using SetProcInfoFn = BOOL (WINAPI*)(HANDLE, int, LPVOID, DWORD);
            if (auto fn = reinterpret_cast<SetProcInfoFn>(reinterpret_cast<void*>(GetProcAddress(k32, "SetProcessInformation"))))
                set_ok = fn(GetCurrentProcess(), 4 /* ProcessPowerThrottling */, &st, (DWORD) sizeof(st)) ? 1 : 0;
        }
        std::fprintf(stderr, "strata: STRATA_TIMER_RES=%c timeBeginPeriod(1) -> %u (0 = ok), SetProcessInformation(power throttling) -> %d\n", tr[0], ok_period, set_ok);
    }
#endif
'''.replace('\n', nl)
txt = txt.replace(anchor, anchor + block)
open(p, 'wb').write(txt.encode('utf-8'))
print('patched', hashlib.sha256(txt.encode('utf-8')).hexdigest().upper())
