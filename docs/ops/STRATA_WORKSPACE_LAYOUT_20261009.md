# Strata workspace layout

Updated: 2026-10-09

## Canonical project root

Use the existing GitHub fork clone directly for source and project management:

C:\Users\User\Strata-Adrian-control

This repository is the canonical location for source changes, AGENTS.md, handoffs, operational documentation, and small benchmark manifests.

Large local archive/runtime staging remains separate:

C:\Users\User\Strata

It is not a second source project. Current active runtime paths are retained until a separate path migration is verified; historical command artifacts are not rewritten.

## Current authoritative components

- Git source: C:\Users\User\Strata-Adrian-control
- Current build: C:\Users\User\Strata-Adrian-control-build\strata.exe
- Current IQ3 runtime: C:\Users\User\Strata-IQ3-20261008
- IQ3 model and pack: the models\IQ3_XXS and packs\iq3_xxs directories under the current IQ3 runtime
- Current IQ3 overnight results: the overnight-20261009 directory under the current IQ3 runtime

## Dependency warning

The effective IQ3 command currently references these assets from the older IQ2 project:

- C:\Users\User\Strata-v0.1.34-mtp-test-20261002\packs\iq2_xs\tokenizer
- C:\Users\User\Strata-v0.1.34-mtp-test-20261002\mtp\rt
- C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\learned-heart.bin

The IQ2 and IQ3 pack tokenizer directories are currently byte-for-byte identical across all five tokenizer files. The current config points to the IQ2 copy, but a future self-contained IQ3 config may point to the IQ3 pack copy without changing model semantics or decode performance.

Therefore the IQ2 and v0.1.38 projects are not redundant as a whole. Do not delete their models, packs, tokenizer, MTP, or expert-profile files until a new shared-runtime location has been copied, verified, and substituted in all effective configs.

## Completed cleanup

The following non-Git, non-active directories were moved, with file-count and byte-count verification, to:

C:\Users\User\Strata\archive\legacy\20261009

- Strata-lm-run-2026-09-28
- Strata-lm-pin-test-20260929-01
- Strata-Adrian-pf-d64-build-20261008
- older Adrian benchmark result directories
- strata_current_best_phases_20261008

The clean PF/D64 source worktree was removed after creating and verifying:

C:\Users\User\Strata\archive\git\Strata3060-adrian-pf-d64-seed-20261008.bundle

The PF/D64 branch remains in the main Git repository.

## Retention policy

- Keep source, handoffs, manifests, and small operational documentation in Git.
- Keep model weights, packs, MTP binaries, build outputs, and large benchmark logs local or in the local archive.
- Never infer that an IQ2/IQ3 directory is removable from its name alone; check current command references first.
