# Analyst demo UX polish follow-up

Starting HEAD: `0da9b6bef946606337664d7d2712e28555a4b853`.

## Delivered

The demo creates a self-contained static HTML review index with relative media
links, separate representative/diagnostic/rejected sections, visible ballward
cues, a compact 16-column CSV and the unchanged detailed export schema. The
media-run tables now contain actual copied paths and explicit support states.
The CLI finishes with the index path and 2/2/1 role counts. No server, framework
or internet connection is required to use the resulting package.

## Five-example acceptance

| Example | Presentation outcome |
|---|---|
| Home P2 5355.64 | Role and low-ballward/localized interpretation are clearer, with a direct clip link. The two-second clip and missing contributor values remain unresolved. |
| Home P1 336.76 | High-ballward label and 0.730 share are explicit above the media; existing ten-second clip is directly accessible. |
| Home P2 4443.16 | Goalkeeper-distribution special context is prominent. Historical 12-link overlay remains unchanged. |
| Home P1 978.32 | Clearly diagnostic with no strong link; text explains that zero links does not mean no attacker movement. |
| Home P1 1734.72 | Separate red REJECTED section states impossible native-frame movement and QC-only use. No rejected GIF enters the default package. |

## Unresolved requirements

The closed attacker-linked summary does not serialize the defender contribution
triplet for 5355.64 or the individual strong-link records. Its renderer consumes
in-memory trajectories, contributions and pair records, obtained by the historical
pipeline through scoring and link construction. The inspected saved local audit
packages contain media and compact summaries, not these missing records.

Consequently this pass does not produce extended attacker-linked clips, reduce
the historical link overlays, or fabricate the absent contributor triplet.
Their completion needs a separately authorized bounded recovery/recomputation
of the exact selected-window inputs, or an authoritative saved cache containing
them. The requested no-rescoring boundary was preserved. Historical pixels are
not used to infer numerical values or to identify links for removal.

The static index uses only existing closed values. The goalkeeper-distribution
label applies to the current closed Game 2 diagnostic, not a general inference
that distributed linkage implies goalkeeper distribution. Selection rules and
all five selected identities are unchanged.

## Validation

Focused facade/index tests: 13 passed. Portable suite: 725 passed, 21 deselected,
1 expected failure. Full suite including available provider tests: 745 passed,
1 skipped, 1 expected failure. Compilation, relative-link validation,
deterministic double-package generation and private-path checks passed.
A fresh temporary clone using the existing Python environment and an explicit
external public-data root produced the same 17-file package byte-for-byte as
both local runs. This checks checkout portability, not dependency installation.
The paper firewall has no blocking findings and 42 unresolved-path warnings;
the changed-artifact guard has no findings. All 753 tracked submission,
scientific-output and application-artifact files in the preservation set are
byte-identical to the starting commit, including the production scorer.

## Verdict

**DEMO UX STILL NEEDS WORK**

Navigation and status presentation are ready for review. Full media acceptance
requires resolving the missing selected-window inputs under explicit authority.
