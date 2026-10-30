import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
src=ROOT/'patched'/'expert_source.cpp'
data=src.read_bytes()
assert hashlib.sha256(data).hexdigest().upper()=='2294D6B8F007A3D238EE0D68CAA77B888A4491682156B796C869EC07E6163658'
text=data.decode().replace('\r\n','\n')
def replace(old,new):
    global text
    assert text.count(old)==1,(old[:80],text.count(old))
    text=text.replace(old,new)

replace('namespace {\nstruct PhaseIoCounters {',r'''namespace {
const char* direct_shadow_path() {
    static const char* p = std::getenv("STRATA_DIRECT_SHADOW_FIRST");
    return p && *p ? p : nullptr;
}
bool direct_shadow_source(const std::string& path) {
    const size_t cut = path.find_last_of("/\\");
    return path.substr(cut == std::string::npos ? 0 : cut + 1) ==
        "Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf";
}
std::atomic<uint64_t> shadow_calls{0}, shadow_requests{0}, shadow_bytes{0}, shadow_total_bytes{0};
struct PhaseIoCounters {''')
replace('''#if defined(_WIN32)
    for (const std::string& path : paths_) {
        const int wide = MultiByteToWideChar(CP_UTF8, 0, path.c_str(), -1, nullptr, 0);
        std::vector<wchar_t> w((size_t) (wide > 0 ? wide : 1), L'\\0');
        if (wide > 0) MultiByteToWideChar(CP_UTF8, 0, path.c_str(), -1, w.data(), wide);
        HANDLE h = CreateFileW(w.data(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING,
                               FILE_FLAG_NO_BUFFERING | FILE_FLAG_OVERLAPPED, nullptr);
        if (h == INVALID_HANDLE_VALUE) {''',r'''#if defined(_WIN32)
    const char* shadow = direct_shadow_path();
    size_t shadow_matches = 0;
    for (const std::string& path : paths_) {
        const bool use_shadow = shadow && direct_shadow_source(path);
        const std::string selected = use_shadow ? shadow : path;
        const int wide = MultiByteToWideChar(CP_UTF8, 0, selected.c_str(), -1, nullptr, 0);
        std::vector<wchar_t> w((size_t) (wide > 0 ? wide : 1), L'\0');
        if (wide > 0) MultiByteToWideChar(CP_UTF8, 0, selected.c_str(), -1, w.data(), wide);
        HANDLE h = CreateFileW(w.data(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING,
                               FILE_FLAG_NO_BUFFERING | FILE_FLAG_OVERLAPPED, nullptr);
        if (h == INVALID_HANDLE_VALUE && shadow) {
            std::fprintf(stderr, "DIRECT_SHADOW FATAL open error=%lu\n", GetLastError()); std::abort();
        }
        if (use_shadow) {
            const int ow = MultiByteToWideChar(CP_UTF8, 0, path.c_str(), -1, nullptr, 0);
            std::vector<wchar_t> original((size_t)ow);
            if (ow <= 0 || !MultiByteToWideChar(CP_UTF8, 0, path.c_str(), -1, original.data(), ow)) std::abort();
            HANDLE ref = CreateFileW(original.data(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING,
                FILE_FLAG_NO_BUFFERING | FILE_FLAG_OVERLAPPED, nullptr);
            BY_HANDLE_FILE_INFORMATION a{}, b{};
            if (ref == INVALID_HANDLE_VALUE || !GetFileInformationByHandle(ref,&a) || !GetFileInformationByHandle(h,&b)) std::abort();
            CloseHandle(ref);
            const uint64_t original_bytes = ((uint64_t)a.nFileSizeHigh<<32)|a.nFileSizeLow;
            const uint64_t copy_bytes = ((uint64_t)b.nFileSizeHigh<<32)|b.nFileSizeLow;
            if ((a.dwVolumeSerialNumber==b.dwVolumeSerialNumber && a.nFileIndexHigh==b.nFileIndexHigh && a.nFileIndexLow==b.nFileIndexLow) ||
                original_bytes != 47039860096ull || copy_bytes != ((original_bytes+4095)/4096*4096) || role_ptr_.empty()) {
                std::fprintf(stderr,"DIRECT_SHADOW FATAL identity/size/layout\n"); std::abort();
            }
            ++shadow_matches;
            std::fprintf(stderr,"DIRECT_SHADOW ACTIVE source=%s shadow=%s original_bytes=%llu shadow_bytes=%llu\n",
                path.c_str(),selected.c_str(),(unsigned long long)original_bytes,(unsigned long long)copy_bytes);
        }
        if (h == INVALID_HANDLE_VALUE) {''')
replace('''        direct_.push_back(h);
    }
    if (role_ptr_.empty())''','''        direct_.push_back(h);
    }
    if (shadow && shadow_matches != 1) {
        std::fprintf(stderr,"DIRECT_SHADOW FATAL expected exactly one source match\\n"); std::abort();
    }
    if (role_ptr_.empty())''')
replace('''#if defined(_WIN32)
    // NTFS runs the unbuffered reads''',r'''#if defined(_WIN32)
    struct StrictShadowRead {
        bool succeeded = false;
        ~StrictShadowRead() {
            if (!succeeded && direct_shadow_path()) {
                std::fprintf(stderr,"DIRECT_SHADOW FATAL read; no cached retry\n"); std::abort();
            }
        }
    } strict_shadow;
    // NTFS runs the unbuffered reads''')
replace('''        std::memcpy(x.dst + x.at, sc.buf + sc.req[x.req].pos + x.in_req + x.skip, (size_t) x.n);
    }
    return true;
#elif defined(__linux__)''',r'''        std::memcpy(x.dst + x.at, sc.buf + sc.req[x.req].pos + x.in_req + x.skip, (size_t) x.n);
    }
    strict_shadow.succeeded = true;
    if (direct_shadow_path()) {
        for (const Req& q : sc.req) {
            shadow_total_bytes.fetch_add(q.size,std::memory_order_relaxed);
            for (size_t f=0; f<paths_.size(); ++f)
                if (direct_shadow_source(paths_[f]) && q.h==(HANDLE)direct_[f]) {
                    shadow_requests.fetch_add(1,std::memory_order_relaxed);
                    shadow_bytes.fetch_add(q.size,std::memory_order_relaxed);
                }
        }
        if ((shadow_calls.fetch_add(1,std::memory_order_relaxed)&127u)==0)
            std::fprintf(stderr,"DIRECT_SHADOW progress requests=%llu shadow_bytes=%llu total_bytes=%llu\n",
                (unsigned long long)shadow_requests.load(),(unsigned long long)shadow_bytes.load(),
                (unsigned long long)shadow_total_bytes.load());
    }
    return true;
#elif defined(__linux__)''')
out=ROOT/'shadow-expert_source.cpp'
out.write_bytes(text.replace('\n','\r\n').encode())
identity=dict(original_sha256=hashlib.sha256(data).hexdigest().upper(),patched_sha256=hashlib.sha256(out.read_bytes()).hexdigest().upper(),env='STRATA_DIRECT_SHADOW_FIRST',shadow='C:\\Users\\User\\Strata-Adrian-control\\runs\\unmapped-shadow-20261029\\first-shard.direct')
(ROOT/'shadow-patch-identity.json').write_text(json.dumps(identity,indent=2))
print(json.dumps(identity,indent=2))
