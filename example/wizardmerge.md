# WizardMerge: Save Us From Merging Without Any Clues

**Authors:** Qingyu Zhang, Junzhe Li, Jiayi Lin, Jie Ding, Lanteng Lin, Chenxiong Qian

> This markdown version condenses the contents of `wizardmerge.pdf` into a clean, accessible summary. It preserves the
> paper's structure, key ideas, and reported results while omitting PDF-specific artifacts that appeared in the original
> automated extraction.

## Abstract

Modern software development relies on efficient, version-oriented collaboration, yet Git's textual three-way merge can
produce unsatisfactory results that leave developers with little guidance on how to resolve conflicts or detect incorrectly
applied, conflict-free changes. WizardMerge is an auxiliary tool that augments Git's merge output by retrieving code-block
dependencies at both the text and LLVM-IR levels and surfacing developer-facing suggestions. In evaluations across 227
conflicts drawn from five large-scale projects, WizardMerge reduced conflict-handling time by 23.85% and provided
suggestions for over 70% of code blocks potentially affected by the conflicts, including conflict-unrelated blocks that
Git mistakenly applied.

## 1. Introduction

Git's default line-oriented three-way merge is fast and general, but it ignores syntax and semantics. Developers therefore
frequently encounter merge conflicts or incorrect, conflict-free merges that still alter behavior. Prior structured and
semi-structured merge tools reframe the problem around AST manipulation but still leave developers without guidance when
conflicts arise. Machine-learning approaches can suggest resolutions but depend on specialized training data, introduce
length constraints, and may not match developer intent. WizardMerge addresses these gaps by guiding developers toward
conflict resolution rather than automatically rewriting code, highlighting both conflicting and potentially affected
non-conflicting regions.

## 2. Background: Git Merging

Git identifies a merge base, aligns modified code blocks from each side, and treats each modified segment as a Differing
Code Block (DCB). Conflicts occur when both sides touch overlapping regions; non-conflicting DCBs are applied directly but
may still change behavior in subtle ways. Developers therefore need insight into how DCBs depend on one another and which
blocks merit closer inspection during reconciliation.

## 3. Design of WizardMerge

WizardMerge combines Git's merge output with LLVM-based static analysis to illuminate dependencies among code blocks. The
high-level workflow is:

*High-level WizardMerge workflow diagram — see wizardmerge.pdf (object 343).* 

1. **Metadata collection:** Compile each merge input with LLVM to gather intermediate representation (IR) and debug
   information without adding custom build steps for large projects.
2. **Dependency graph generation:** Build overall dependency graphs from LLVM IR, aligning Git's DCBs with graph nodes to
   capture relationships across both text and IR levels.
3. **Group-wise analysis:** Partition DCBs into relevance groups so that developers can triage related changes together
   rather than in isolation.
4. **Priority-oriented classification:** Score and order DCBs based on dependency violations or potential risk, helping
   developers focus on code most likely to be affected by the merge.
5. **Resolution suggestions:** Surface actionable hints for resolving conflicts and flag conflict-unrelated blocks that Git
   applied but still require human attention.

## 4. Evaluation

WizardMerge was evaluated on 227 conflicts from five large-scale projects. Key findings include:

- **Efficiency:** Average conflict-handling time decreased by 23.85% compared to baseline Git workflows.
- **Coverage:** WizardMerge produced suggestions for more than 70% of code blocks potentially impacted by conflicts.
- **False-safety detection:** The tool identified conflict-unrelated blocks that Git applied automatically but that still
  demanded manual review.
- **Comparison to ML approaches:** Machine-learning-based merge generators struggle with large codebases due to sequence
  length limits and generalization challenges; WizardMerge avoids these constraints by relying on static analysis rather
  than learned models.

## 5. Limitations and Threats to Validity

- WizardMerge depends on successful LLVM compilation of both merge inputs; projects that cannot be built or require
  non-standard toolchains may limit applicability.
- Static analysis provides conservative approximations and may miss dynamic dependencies, so developer judgment remains
  essential.
- The evaluation focuses on a curated set of conflicts; broader studies could further validate effectiveness across diverse
  languages and project types.

## 6. Conclusion

WizardMerge augments Git's textual merging by revealing dependency-aware relationships among differing code blocks and
prioritizing developer effort. By coupling Git merge results with LLVM-based analysis, it shortens conflict resolution time
and highlights risky, conflict-unrelated changes that would otherwise slip through. Future work includes expanding language
coverage, refining prioritization heuristics, and integrating the tool more deeply into developer workflows.

## Appendix: Graphics from the original PDF

The original WizardMerge paper interleaves numerous figures, icons, and decorative separators. To mirror that layout, this appendix lists every extracted graphic in order of appearance so readers can cross-reference the visuals with the summarized text. To keep the repository lightweight, the extracted PNG assets are no longer stored here; use the object filenames below to locate each visual inside `wizardmerge.pdf`.

### Figure gallery

- Figure 1: Object 234 (33×34, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-portrait-33x34-obj234.png)

- Figure 2: Object 235 (32×34, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-portrait-32x34-obj235.png)

- Figure 3: Object 236 (193×162, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-193x162-obj236.png)

- Figure 4: Object 237 (193×162, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-193x162-obj237.png)

- Figure 5: Object 238 (193×161, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-193x161-obj238.png)

- Figure 6: Object 239 (33×34, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-portrait-33x34-obj239.png)

- Figure 7: Object 247 (33×34, dark gray) — see wizardmerge.pdf (object file: extracted_graphics/dark-gray-detailed-portrait-33x34-obj247.png)

- Figure 8: Object 248 (32×34, dark gray) — see wizardmerge.pdf (object file: extracted_graphics/dark-gray-detailed-portrait-32x34-obj248.png)

- Figure 9: Object 249 (193×162, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-193x162-obj249.png)

- Figure 10: Object 250 (193×162, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-193x162-obj250.png)

- Figure 11: Object 251 (193×161, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-193x161-obj251.png)

- Figure 12: Object 252 (33×34, dark gray) — see wizardmerge.pdf (object file: extracted_graphics/dark-gray-detailed-portrait-33x34-obj252.png)

- Figure 13: Object 296 (256×155, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-256x155-obj296.png)

- Figure 14: Object 297 (527×321, dark gray red) — see wizardmerge.pdf (object file: extracted_graphics/dark-gray-red-low-contrast-landscape-527x321-obj297.png)

- Figure 15: Object 298 (527×321, dark gray blue) — see wizardmerge.pdf (object file: extracted_graphics/dark-gray-blue-low-contrast-landscape-527x321-obj298.png)

- Figure 16: Object 302 (256×155, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-256x155-obj302.png)

- Figure 17: Object 303 (527×321, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-527x321-obj303.png)

- Figure 18: Object 304 (527×321, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-527x321-obj304.png)

- Figure 19: Object 343 (4234×1847, mid gray green) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-green-detailed-landscape-4234x1847-obj343.png)

- Figure 20: Object 359 (4234×1847, light gray) — see wizardmerge.pdf (object file: extracted_graphics/light-gray-detailed-landscape-4234x1847-obj359.png)

- Figure 21: Object 374 (165×216, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-portrait-165x216-obj374.png)

- Figure 22: Object 376 (194×122, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-194x122-obj376.png)

- Figure 23: Object 378 (195×122, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-195x122-obj378.png)

- Figure 24: Object 381 (348×170, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-348x170-obj381.png)

- Figure 25: Object 382 (134×79, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-134x79-obj382.png)

- Figure 26: Object 383 (122×76, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-122x76-obj383.png)

- Figure 27: Object 384 (137×76, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-137x76-obj384.png)

- Figure 28: Object 385 (348×249, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-348x249-obj385.png)

- Figure 29: Object 386 (134×79, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-134x79-obj386.png)

- Figure 30: Object 387 (129×76, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-129x76-obj387.png)

- Figure 31: Object 388 (189×79, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-189x79-obj388.png)

- Figure 32: Object 389 (151×76, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-151x76-obj389.png)

- Figure 33: Object 390 (189×79, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-189x79-obj390.png)

- Figure 34: Object 391 (169×76, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-169x76-obj391.png)

- Figure 35: Object 393 (148×155, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-portrait-148x155-obj393.png)

- Figure 36: Object 395 (298×329, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-portrait-298x329-obj395.png)

- Figure 37: Object 396 (148×155, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-portrait-148x155-obj396.png)

- Figure 38: Object 401 (165×216, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-portrait-165x216-obj401.png)

- Figure 39: Object 402 (194×122, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-194x122-obj402.png)

- Figure 40: Object 403 (195×122, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-195x122-obj403.png)

- Figure 41: Object 404 (348×170, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-348x170-obj404.png)

- Figure 42: Object 405 (134×79, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-134x79-obj405.png)

- Figure 43: Object 406 (122×76, black) — see wizardmerge.pdf (object file: extracted_graphics/black-low-contrast-landscape-122x76-obj406.png)

- Figure 44: Object 407 (137×76, black) — see wizardmerge.pdf (object file: extracted_graphics/black-low-contrast-landscape-137x76-obj407.png)

- Figure 45: Object 408 (348×249, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-348x249-obj408.png)

- Figure 46: Object 409 (134×79, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-134x79-obj409.png)

- Figure 47: Object 410 (129×76, black) — see wizardmerge.pdf (object file: extracted_graphics/black-low-contrast-landscape-129x76-obj410.png)

- Figure 48: Object 411 (189×79, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-189x79-obj411.png)

- Figure 49: Object 412 (151×76, black) — see wizardmerge.pdf (object file: extracted_graphics/black-low-contrast-landscape-151x76-obj412.png)

- Figure 50: Object 413 (189×79, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-189x79-obj413.png)

- Figure 51: Object 414 (169×76, black) — see wizardmerge.pdf (object file: extracted_graphics/black-low-contrast-landscape-169x76-obj414.png)

- Figure 52: Object 415 (148×155, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-portrait-148x155-obj415.png)

- Figure 53: Object 416 (298×329, black) — see wizardmerge.pdf (object file: extracted_graphics/black-low-contrast-portrait-298x329-obj416.png)

- Figure 54: Object 417 (148×155, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-portrait-148x155-obj417.png)

- Figure 55: Object 455 (31×30, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-31x30-obj455.png)

- Figure 56: Object 456 (158×88, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-158x88-obj456.png)

- Figure 57: Object 457 (147×91, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-147x91-obj457.png)

- Figure 58: Object 458 (200×142, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-200x142-obj458.png)

- Figure 59: Object 459 (32×32, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-square-32x32-obj459.png)

- Figure 60: Object 460 (183×84, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-183x84-obj460.png)

- Figure 61: Object 461 (173×87, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-173x87-obj461.png)

- Figure 62: Object 462 (32×32, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-square-32x32-obj462.png)

- Figure 63: Object 463 (183×83, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-183x83-obj463.png)

- Figure 64: Object 464 (173×87, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-173x87-obj464.png)

- Figure 65: Object 465 (32×32, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-square-32x32-obj465.png)

- Figure 66: Object 466 (159×88, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-159x88-obj466.png)

- Figure 67: Object 467 (147×91, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-147x91-obj467.png)

- Figure 68: Object 468 (32×33, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-portrait-32x33-obj468.png)

- Figure 69: Object 469 (158×88, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-158x88-obj469.png)

- Figure 70: Object 470 (147×91, black) — see wizardmerge.pdf (object file: extracted_graphics/black-solid-landscape-147x91-obj470.png)

- Figure 71: Object 476 (31×30, dark gray) — see wizardmerge.pdf (object file: extracted_graphics/dark-gray-detailed-landscape-31x30-obj476.png)

- Figure 72: Object 477 (158×88, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-158x88-obj477.png)

- Figure 73: Object 478 (147×91, black) — see wizardmerge.pdf (object file: extracted_graphics/black-low-contrast-landscape-147x91-obj478.png)

- Figure 74: Object 479 (200×142, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-200x142-obj479.png)

- Figure 75: Object 480 (32×32, dark gray) — see wizardmerge.pdf (object file: extracted_graphics/dark-gray-detailed-square-32x32-obj480.png)

- Figure 76: Object 481 (183×84, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-183x84-obj481.png)

- Figure 77: Object 482 (173×87, black) — see wizardmerge.pdf (object file: extracted_graphics/black-low-contrast-landscape-173x87-obj482.png)

- Figure 78: Object 483 (32×32, dark gray) — see wizardmerge.pdf (object file: extracted_graphics/dark-gray-detailed-square-32x32-obj483.png)

- Figure 79: Object 484 (183×83, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-183x83-obj484.png)

- Figure 80: Object 485 (173×87, black) — see wizardmerge.pdf (object file: extracted_graphics/black-low-contrast-landscape-173x87-obj485.png)

- Figure 81: Object 486 (32×32, dark gray) — see wizardmerge.pdf (object file: extracted_graphics/dark-gray-detailed-square-32x32-obj486.png)

- Figure 82: Object 487 (159×88, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-159x88-obj487.png)

- Figure 83: Object 488 (147×91, black) — see wizardmerge.pdf (object file: extracted_graphics/black-low-contrast-landscape-147x91-obj488.png)

- Figure 84: Object 489 (32×33, dark gray) — see wizardmerge.pdf (object file: extracted_graphics/dark-gray-detailed-portrait-32x33-obj489.png)

- Figure 85: Object 490 (158×88, mid gray) — see wizardmerge.pdf (object file: extracted_graphics/mid-gray-detailed-landscape-158x88-obj490.png)

- Figure 86: Object 491 (147×91, black) — see wizardmerge.pdf (object file: extracted_graphics/black-low-contrast-landscape-147x91-obj491.png)

- Figure 87: Object 515 (1913×1363, light gray blue) — see wizardmerge.pdf (object file: extracted_graphics/light-gray-blue-detailed-landscape-1913x1363-obj515.png)

- Figure 88: Object 535 (1812×918, black) — see wizardmerge.pdf (object file: extracted_graphics/black-detailed-landscape-1812x918-obj535.png)

- Figure 89: Object 543 (1913×1363, light gray) — see wizardmerge.pdf (object file: extracted_graphics/light-gray-detailed-landscape-1913x1363-obj543.png)

- Figure 90: Object 554 (1812×918, dark gray) — see wizardmerge.pdf (object file: extracted_graphics/dark-gray-detailed-landscape-1812x918-obj554.png)

- Figure 91: Object 601 (2049×322, unspecified palette) — see wizardmerge.pdf (object file: extracted_graphics/jpeg-landscape-2049x322-obj601.jpg)

- Figure 92: Object 602 (2049×322, unspecified palette) — see wizardmerge.pdf (object file: extracted_graphics/jpeg-landscape-2049x322-obj602.jpg)

