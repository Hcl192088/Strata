#pragma once
#include <cstdint>
namespace strata::core {
struct CpuPhaseDiag {
    double helper_ms=0, join_ms=0, ready_ms=0, inline_ms=0, lru_ms=0;
    double direct_ms=0, copy_ms=0, issue_wait_ms=0;
    uint64_t issued_bytes=0, useful_bytes=0, splits=0, inlines=0;
};
bool cpu_phase_diag_enabled();
CpuPhaseDiag cpu_phase_diag_snapshot();
}
