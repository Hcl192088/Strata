from pathlib import Path
import subprocess
R=Path(r'C:\Users\User\Strata-Adrian-control\runs\pcie-balance-20261029');p=R/'source/src/program/generate.cpp';s=p.read_text();a='                const double w = (double) dec_windows, L = (double) g.n_layers;';assert s.count(a)==1
b='''                if (ver.pcie_balance_on()) {
                    const auto& pm = drive.d.pcie_model;
                    std::fprintf(stderr, "PCIE_BALANCE fit ready=%d ncpu=%d ngpu=%d ngpu_p=%d explore=%u CPU_us=%.3f+%.3f*n_cpu+%.3f*n_pcie GPU_us=%.3f+%.3f*n_pcie (PCIe count per layer from these)\\n",
                                 pm.ready() ? 1 : 0, pm.ncpu, pm.ngpu, pm.ngpu_p, pm.explore,
                                 1000*pm.a, 1000*pm.c, 1000*pm.d, 1000*pm.g0, 1000*pm.g);
                }
'''+a
p.write_text(s.replace(a,b));print('serve fit logging added; balance OFF emits nothing')
