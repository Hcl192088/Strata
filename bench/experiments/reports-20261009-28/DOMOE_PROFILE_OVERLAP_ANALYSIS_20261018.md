# DoMoE Profile Overlap Analysis — 2026-10-18

The previously missing DoMoE overlap evidence is now available as a read-only structural analysis. All 10 catalogued 48x512 profiles passed the STRP v1, SHA256, size and 24,576-pair checks.

The method is global rank-prefix pair-set intersection against the generic profile. A pair is identified as layer:expert; K is 64, 256, 1024 or 4096. This is not a model run and not a semantic domain classifier.

The strongest small-prefix overlap was learned-heart-chat at K=64 with 20.3125%. At K=4096, learned-heart-original was highest at 43.408203%, followed by learned-3topics at 40.136719%. iq2xs-pitching and iq2xs-travel had zero overlap at K=64; this demonstrates structural profile difference, not domain quality or performance.

The result is therefore DIAGNOSTIC_ONLY. It makes a future matched current-IQ3 trace/profile matrix more informative, but it does not prove current IQ3 equivalence, selector quality, hit rate, accepted decode tok/s, output parity or DoMoE reproduction. No profile was copied, selected or deployed.

Two transport attempts failed before analysis: a long encoded PowerShell command exceeded the Windows SSH command-line transport, and PowerShell stdin returned no usable result. A Python stdin read-only analysis then succeeded. These were tooling-layer failures with no remote side effect.
