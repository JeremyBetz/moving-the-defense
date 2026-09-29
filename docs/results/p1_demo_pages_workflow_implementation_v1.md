# Manual analyst demo Pages workflow implementation v1

Date: 2026-09-28. Verdict: **A. READY TO INTEGRATE PAGES WORKFLOW**.
Starting HEAD: `c059df5fd40a4156cbea83236fed3de37cb356a3` on clean
`codex/p1-audit-demo-hardening`. No deployment has been run. Pages remains a
separately authorized configuration and deployment step.

## Workflow and security contract

The [workflow](../../.github/workflows/deploy-analyst-demo-pages.yml) has exactly
one trigger, `workflow_dispatch`, with no inputs, push, PR or schedule trigger.
Ordinary commits do not deploy. An authorized operator must explicitly dispatch
it (normally Actions → Run workflow); GitHub also supports authenticated API/CLI
dispatch, so this is not a technical guarantee of a physical button click.

The single deployment job additionally requires `refs/heads/main` and the
`workflow_dispatch` event. It runs on `ubuntu-latest`, with a 15-minute timeout,
the `github-pages` environment and the standard deployment URL output.
Concurrency group `pages` uses `cancel-in-progress: false`; in-flight deployments
are not cancelled. GitHub may replace pending queued runs with newer ones, so
this is serialization, not a guarantee that every queued dispatch is executed.

Permissions are exactly `contents: read`, `pages: write`, `id-token: write`.
Unspecified permissions are not granted. Checkout does not persist credentials.
There are no custom secrets, personal tokens, broad repository write grants,
dependency installs, Python setup, analytical calls or media generation.
The gate uses runner-provided `python3` and standard-library code only.

Official latest releases and their commit refs were checked through GitHub's
read-only API before pinning:

| Action | Release | Immutable commit |
| --- | --- | --- |
| actions/checkout | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| actions/configure-pages | v6.0.0 | `45bfe0192ca1faeb007ade9deae92b16b8254a0d` |
| actions/upload-pages-artifact | v5.0.0 | `fc324d3547104276b827a68afc52ff2a11cc49c9` |
| actions/deploy-pages | v5.0.1 | `368f82528645a54fb793d4d04e342629a3f51346` |

The pinned action definitions were inspected. Configure Pages receives explicit
`enablement: false`: it must not bootstrap Pages configuration. The upload
action packages the specified directory as artifact root, excludes hidden
files, and retains the artifact for one day. Its pinned composite definition
also pins the underlying upload-artifact action. The deployment step consumes
the standard `github-pages` artifact.

This follows the [official static Pages workflow pattern](https://github.com/actions/starter-workflows/blob/main/pages/static.yml),
but omits its automatic push trigger and replaces whole-repository upload with
the reviewed directory. Version tags in the starter template can lag releases;
the immutable refs above were resolved from the official release repositories.

## Exact package gate

Order: checkout → validate → configure existing Pages → upload → deploy.
Validation deliberately precedes configuration and upload. Any failed step
prevents subsequent steps; there is no continue-on-error or bypass input.

The shell step executes read-only Python validation. It checks pinned SHA-256
identities for the public manifest, allowlist protocol and exporter source
before importing that source's standard-library presentation validator.
The manifest pin is
`4f8ba5051ef90077091724a1faa7fe1c42a43e8e9febef17456fda3afdf9036f`.
This prevents a coordinated payload-plus-manifest alteration from passing as
the reviewed package. A future demo revision needs a separate review and an
explicit gate-pin update, not merely a new manifest.

The exact 11 files are:

```text
index.html
styles.css
manifest.json
assets/representative/home_p2_5355.64.png
assets/representative/home_p2_5355.64.gif
assets/representative/home_p1_336.76.png
assets/representative/home_p1_336.76.gif
assets/diagnostic/home_p2_4443.16.png
assets/diagnostic/home_p2_4443.16.gif
assets/rejected/home_p1_1734.72.png
assets/rejected/home_p1_1734.72.gif
```

Inventory comparison includes expected parent directories and rejects extra
directories as well as extra files. It rejects missing files, symlinks (including
the package root and `docs`), special files, hidden entries, unexpected extensions,
CSV/source/cache payloads and traversal paths. No directory discovery selects
publication assets. Upload path is literally `docs/demo`, not `docs` or `.`.

The existing validator verifies exact manifest schema, source lineage, approved
metric fields, media identities, all ten payload hashes, deterministic HTML/CSS,
allowlisted HTTPS links and local relative links. The pinned manifest itself is
the eleventh checked file. The validator is used only for comparison; neither
its exporter nor any scientific routine is invoked and no files are generated.

Additional lightweight text checks reject obvious private filesystem URLs or
paths in HTML/CSS/JSON, including home and temporary directory prefixes. These
checks supplement exact byte identity and structural validation, not a broad
binary grep or a claim of comprehensive secret detection. The eight binary
media files must retain the exact already-approved hashes. No raw coordinates,
stable player IDs, technical CSVs or local caches enter the artifact. Existing
provider-derived raster media still permit approximate positional recovery;
deployment does not confer broader redistribution permission.

## URL and configuration contract

Consistent with the [closed deployment review](p1_demo_pages_workflow_review_v1.md),
uploading `docs/demo` as artifact root makes the expected public entry:

`https://jeremybetz.github.io/moving-the-defense/`

There is no additional `/demo/` path. No site links were changed. Relative
stylesheet, manifest and media paths already passed project-subpath checks.
There is no Jekyll build and no `.nojekyll` addition.

Before a separately authorized dispatch, set Repository → Settings → Pages →
Build and deployment → Source: **GitHub Actions**. Configure the `github-pages`
environment to permit deployment from `main` only, with no tag bypass. The
workflow's branch condition supplements rather than replaces environment
protection. Do not infer these settings from the workflow file; verify them
in the eventual deployment pass. No settings were changed here.

## Validation and remaining operational checks

- Focused workflow/exporter tests: 40 passed. Tests execute the actual embedded
  shell gate against the reviewed package and isolated tampered fixtures;
  no GitHub action is dispatched.
- Portable suite excluding `provider_data`: 769 passed, 22 deselected and one
  expected failure. Test compilation passed; no provider-backed tests ran.
- Rejected fixtures cover extra CSV, hidden file, extra directory, symlink,
  missing/tampered media, changed manifest, private-path text and modified
  validator source. Altered validator code is rejected before import.
- YAML parsed locally with PyYAML and workflow shape checked. Contract tests
  cover manual trigger, branch/event gate, exact permissions, concurrency,
  environment, immutable action pins, upload scope and absence of regeneration.
- No `actionlint` executable was available. YAML parsing, contract tests and
  official input-definition inspection are not a claim of a completed GitHub
  service-side run; that remains deliberately deferred.
- The reviewed package gate passes locally, including manifest, media hashes,
  public-text privacy checks and HTML/link validation.
- All 753 protected files and all 11 demo files are byte-identical to the
  starting commit. Exporter source and output hashes remain unchanged.
- Paper firewall passes with 42 existing nonblocking unresolved-path findings;
  changed-artifact/publication guard and whitespace checks pass.

After authorized integration, normal push and manual dispatch, verify logged-out
HTTP success, correct content types and hashes for the manifest and all ten
payload files. Check desktop/mobile layout, GIF playback, static links,
reduced-motion posters, collapsed diagnostic/QC sections and rejected labels.
Inspect the exact uploaded artifact inventory, not only selected live URLs.
Confirm the deployed commit and all eight media hashes, and only then publish a
live README link. No live verification is claimed in this implementation pass.

Rollback: unpublish Pages if necessary, revert/correct the workflow through
normal commits and remove live navigation links. Merely disabling the workflow
does not necessarily remove an already served site. Do not rewrite history.

**Next action:** perform a separately authorized bounded integration/deployment
pass: merge the reviewed branch into main, push normally, set Pages source to
GitHub Actions and main-only environment protection, manually run the reviewed
workflow, then verify the live site logged out.
