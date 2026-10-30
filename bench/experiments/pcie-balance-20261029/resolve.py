from pathlib import Path
import subprocess,json,shutil
R=Path(r'C:\Users\User\Strata-Adrian-control\runs\pcie-balance-20261029');W=R/'source'
def edit(f,a,b):
 p=W/f;s=p.read_text();assert s.count(a)==1,(f,a,s.count(a));p.write_text(s.replace(a,b))
edit('include/strata/kernels/verify_kernels.hpp','void wait_flag_ge(const uint32_t* flag, uint32_t value, void* stream);','void wait_flag_ge(const uint32_t* flag, uint32_t value, void* stream);\n/// As wait_flag_ge, with optional GPU clock stamps at entry and exit.\nvoid wait_flag_ge_stamped(const uint32_t* flag, uint32_t value, unsigned long long* t_in, unsigned long long* t_out, void* stream);')
edit('src/core/expert_source.cpp','const bool pcie_ok = d.pcie_num > 0 && d.src->pcie_layer(d.layers);\n        const int m = pcie_ok ? (nmiss * d.pcie_num) >> 8 : 0;','const bool pcie_ok = (d.pcie_num > 0 || d.pcie_model.on) && d.src->pcie_layer(d.layers);\n        const int m = pcie_ok ? d.pcie_model.pick(nmiss, (nmiss * d.pcie_num) >> 8) : 0;')
edit('src/core/expert_source.cpp','    pt("run", njobs);','    if (d.plan != nullptr) d.plan->cpu_jobs = njobs;\n    pt("run", njobs);')
edit('src/core/verify.cpp','h_flagA_, h_plan_, h_flagB_, h_plan_err_};','h_flagA_, h_plan_, h_flagB_, h_plan_err_, h_bal_};')
edit('src/core/verify.cpp','                wait_flag_ge(m_flagA_, ring, cs);                  // the pool published this group\'s GPU plan','                if (m_bal_ != nullptr)\n                    wait_flag_ge_stamped(m_flagA_, ring, nullptr, m_bal_ + ((l - lb_) * 2 + grp) * 4, cs);\n                else\n                    wait_flag_ge(m_flagA_, ring, cs);')
edit('src/core/verify.cpp','                wait_flag_ge(m_flag_, ring, cs);               // the CPU\'s share is in the mapped rows','                if (m_bal_ != nullptr)\n                    wait_flag_ge_stamped(m_flag_, ring, m_bal_ + ((l - lb_) * 2 + grp) * 4 + 2, nullptr, cs);\n                else\n                    wait_flag_ge(m_flag_, ring, cs);')
edit('src/core/verify.cpp','    VDBG("staged; launching\\n");','    VDBG("staged; launching\\n");\n    if (h_bal_ != nullptr) std::memset(h_bal_, 0, (size_t) bal_p_.size() * 4 * 8);')
edit('src/program/generate.cpp','        ver.set_remote_expert_opt(remote_opt.get());','        ver.set_remote_expert_opt(remote_opt.get());\n        if (pcie_balance() && n_stages == 1) ver.set_pcie_balance(&drive.d.pcie_model);')
edit('src/program/generate.cpp','            double req_pcie_frac = o.pcie_frac, req_spec_min_p = o.spec_min_p;','            double req_pcie_frac = o.pcie_frac, req_spec_min_p = o.spec_min_p;\n            bool req_pcie_set = false;')
edit('src/program/generate.cpp','else if (key == "pcie_frac") req_pcie_frac = std::clamp((double) fv, 0.0, 1.0);','else if (key == "pcie_frac") { req_pcie_frac = std::clamp((double) fv, 0.0, 1.0); req_pcie_set = true; }')
for p in W.rglob('*.rej'):
 d=R/'rejects'/p.relative_to(W);d.parent.mkdir(parents=True,exist_ok=True);shutil.move(p,d)
diff=subprocess.check_output(['git','-C',str(W),'diff']);(R/'ported.patch').write_bytes(diff)
b=(R.parent/'native-pipe-deploy-prep-20261029/build.cmd').read_text().replace(r'C:\Users\User\native-pipe-generic-20261029',str(W)).replace(str(R.parent/'native-pipe-deploy-prep-20261029'),str(R))
(R/'build.cmd').write_text(b)
print(subprocess.check_output(['git','-C',str(W),'diff','--stat']).decode())
