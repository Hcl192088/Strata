# IQ3 Config Runtime Identity Recheck — 2026-10-18 02:26 +08:00

## Result

The controlled IQ3 config was read-only rechecked after a clean process gate:

- Config SHA256: `C805B120...FEA18`
- Argument-string SHA256 (UTF-8): `58523bed...532381`
- Model: `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS`
- Executable: `ram-lru-20261013\\build\\strata.exe`
- Source HEAD: `61b3fb5...`
- 47 argument tokens and 24 non-sensitive flag names were recorded without copying full argument or credential values.

This gives a fresh frozen identity input for a future sibling isolated Fate capture. It does not mean the scheduled API is safe to repurpose, and it does not prove a capture runner exists.

## Decision

`RUNTIME_IDENTITY_RECHECK_PASS_CAPTURE_MANIFEST_INPUT_READY`. No service was started, no config was changed, and no benchmark or trace capture ran.

## Coverage

Checked process gate, config hash, non-sensitive keys/fields, args hash, token count and flag names. Prompt, seed, sampling, temperature, credential values, model load and service behavior were not inspected in this unit.
