# Analyst demo deployment review v1

Review date: 2026-09-28.
Starting HEAD: `1e3f206d39bdd476741f35dc2e4355725823343c`.
Branch: `codex/p1-audit-demo-hardening`.

## Decision

**A. DEPLOY STATIC GITHUB PAGES DEMO**

This is a recommendation for a separately authorized implementation and
publication pass, not authorization to deploy now. The current pass records
only this review. No site files, repository settings, science, media or
submission artifacts are changed; no push or merge is performed.

## Verified public surface

The preceding read-only review verified a clean worktree at the starting HEAD.
GitHub reported a public repository with `has_pages: false`, no homepage and
no configured Pages site. The local workflow directory was empty; no Pages
configuration was found. Live `main` was
`6ecab49d8a1b663f9d962ef218e78992b7a2d3d3`, and its README did not yet contain
the current analyst-demo command. These are observations at review time, not
guarantees about future remote state.

The existing generated package passed its file-hash, relative-link and
private-path checks. A temporary localhost server verified navigation beneath
the simulated project prefix `/moving-the-defense/`. The page has no scripts
or external runtime requirement. Its mobile layout is functional but too wide:
at a 390-pixel viewport, each metrics table had a 1,924-pixel scroll width
inside a 297-pixel container. Public presentation should replace these tables
with compact responsive metric cards.

The [bounded-media review](p1_selected_window_demo_media.md) records the
underlying deterministic five-example package. This deployment review did not
regenerate it or rerun any analysis.

## Deployment options

| Criterion | Repo-only HTML | Static GitHub Pages | Do not deploy |
|---|---|---|---|
| Implementation effort | Low | Low–moderate | None |
| Maintenance | Low | Low | None |
| Reproducibility | Strong | Strong with identical checked-in assets | Local only |
| Public clarity | Download/open friction | Direct, intentional experience | No public demo |
| Paper/application confusion | Moderate without framing | Low with explicit framing | Lowest exposure |
| Existing media compatibility | Full | Full | Local only |
| Portability | Strong | Strong; also downloadable | Limited reach |
| Relative-path risk | Low if downloaded together | Low with isolated site root | None |
| Reviewer usefulness | Moderate | High | Low |

Repo-only HTML is a viable fallback: download the complete directory and open
its index locally. A GitHub source-file link is not an equivalent hosted HTML
experience. Pages adds a direct public URL without a framework or analytical
backend. Use an isolated static artifact rather than publishing the entire
repository or current documentation tree. GitHub supports branch sources or
custom artifact workflows; the latter limits this deployment to its intended
directory. See [publishing-source guidance](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Public experience and visibility

Use this title and subtitle:

> Moving the Defense — Analyst Demo
>
> Exploratory application of the Project 1 relational-reorganization metric.

Place this disclaimer before the examples:

> This is an exploratory descriptive review tool.
> It does not infer marking, causation, tactical success, or player value.

Briefly explain rapid reorganization, trajectory integrity, ball orientation
and descriptive attacker linkage. Visibility is fixed:

- Default: Home P2 5355.64 and Home P1 336.76, with GIFs, bounded
  interpretations and responsive metric cards.
- Collapsed advanced diagnostic: Home P2 4443.16, prominently labelled
  goalkeeper-distribution special context.
- Omit Home P1 978.32 from the compact public page. Retain it unchanged in
  the local five-example package and technical documentation. This is a
  visibility choice, not a change to scientific selection.
- Collapsed QC section: Home P1 1734.72, explicitly labelled
  `REJECTED — trajectory integrity failure` and
  `impossible native-frame movement detected`. Never present it as valid
  analyst evidence.

Cards show selected raw metres, one-second increase, reference percentile,
the contributor triplet, ballward information and supported linkage
category/count. Links express frozen geometric criteria, not defensive
assignments. Retain the three-link display cap and the 12-link total for the
special-context diagnostic. Reduced-motion users receive static posters and
explicit GIF links.

End with reproduction links, Metrica attribution and a distinct “Paper versus
application” section. The paper concerns off-ball movement direction and
localized defensive reorganization; this demo is exploratory descriptive
application work, not additional paper evidence. Prefer co-occurrence,
association, movement orientation and spatial linkage language. Do not assert
causation, defensive quality, tactical success or marking.

## Public-safety boundary

No private paths, coordinate tables or stable player-key fields were found in
the inspected generated text artifacts. Nevertheless, the local linkage cache
and detailed CSV exports must not be published. The public export should
contain only four approved PNG/GIF pairs and explicitly selected presentation
fields, with no raw tracking/event rows or dependency on a local cache path.

The media are provider-derived: approximate positions can be recovered from
pixels. Rasterization is not anonymization or a general redistribution
permission. Confirm the exact new asset allowlist under existing Metrica
publication guidance before publishing, retaining attribution to the
[official Metrica sample-data source](https://github.com/metrica-sports/sample-data).
This review does not create a publication-policy exception.

The four media pairs total 6,296,185 bytes, approximately 6.30 MB. They fit well
within the current [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).
Historical v1–v5 packages remain unchanged and are not repurposed as writable
deployment destinations.

## Separately authorized implementation plan

Add a presentation-only exporter at `src/export_analyst_demo_site.py`, focused
tests, and a dedicated `docs/demo/` artifact containing:

```text
docs/demo/
  index.html
  manifest.json
  assets/
    home_p2_5355.64.png
    home_p2_5355.64.gif
    home_p1_336.76.png
    home_p1_336.76.gif
    home_p2_4443.16.png
    home_p2_4443.16.gif
    home_p1_1734.72.png
    home_p1_1734.72.gif
```

Keep CSS self-contained and require no external runtime. Update README and
the API guide with public/local routes, preserving the research-first
hierarchy. Add a manually triggered Pages workflow that validates and uploads
only `docs/demo`; it must never access provider data or execute analysis.

Proposed explicit export command:

```bash
.venv/bin/python src/export_analyst_demo_site.py \
  --input /path/to/verified-demo-package \
  --output docs/demo
```

Verify the input manifest, exact five identities and roles before copying the
four public media pairs byte-for-byte. Emit only allowlisted summary fields,
relative asset paths and provenance hashes. Fail on unexpected identities,
missing support, hash disagreement or an existing destination. For an update,
generate into a new temporary destination and review the comparison before
replacing the public artifact. Normal tests must not silently regenerate media.

Do not change scoring, thresholds, example selection, possession/integrity/
ball/linkage rules, historical media or submission artifacts. Implementation
is a separate focused change; this review commit contains no exporter,
workflow or public assets.

## Deployment configuration and acceptance

Expected URL, not currently deployed:

`https://jeremybetz.github.io/moving-the-defense/`

Use reviewed files on `main` through GitHub Actions. Upload `docs/demo` as the
artifact root so `index.html` serves the project URL directly. No site build,
backend or custom domain is required. A repository administrator must set
Settings → Pages → Source to GitHub Actions and restrict the `github-pages`
environment to `main`. Use minimal deployment permissions and pinned official
actions. Merge, push, enabling Pages and dispatching the workflow each remain
subject to separate explicit authorization.

Acceptance checks for that future implementation:

- Entry page and every asset resolve locally and beneath the project prefix.
- Desktop and 390-pixel mobile layouts are readable without wide metric tables.
- Advanced/QC sections start collapsed; rejected content is never representative.
- Only allowlisted files ship: no caches, detailed exports, private paths,
  symlinks or external runtime dependencies.
- Attribution, paper/reproduction links and interpretation boundaries are correct.
- Two exports are byte-identical, with media hashes matching the approved input.
- Publication guards, link checks and whitespace checks pass; frozen artifacts
  remain byte-identical.
- After separately authorized deployment, verify the live page and assets
  logged out.

## Review-only closure and next action

Commit only this report as `docs: review P1 demo deployment options`.
Do not push, merge, implement the site or change GitHub settings in this pass.

Recommended next action after this report is committed: separately authorize
the bounded static-export implementation and exact public asset allowlist;
keep deployment itself gated until that implementation has passed review.
