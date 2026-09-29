# Analyst demo Pages workflow review v1

Review date: 2026-09-28. Decision: **B. READY FOR ACTIONS-BASED PAGES DEPLOYMENT**.
This is architecture readiness, not a deployed site or an implemented workflow.

Starting checkpoint: `fa612378416bc5bd726ad08a4e3fb0f3717dfc53`, clean
`codex/p1-audit-demo-hardening`. This pass changes only this report. No workflow,
repository setting, merge, push, provider access, analytical execution or media
regeneration is authorized or performed.

## Current state and public boundary

Read-only GitHub API checks report public repository
`JeremyBetz/moving-the-defense`, default branch `main`, `has_pages: false`,
and HTTP 404 for the Pages endpoint. Together these indicate Pages is not
configured; this is not inferred from local files alone. Live main remains
`6ecab49d8a1b663f9d962ef218e78992b7a2d3d3`.

There are no deployment workflow files, `_config.yml`, `.nojekyll`, `Gemfile`
or `CNAME` in the tracked repository. The prepared source of deployment truth
is the checked-in [11-file package](../demo/manifest.json), governed by its
[publication allowlist](../protocols/p1_demo_public_asset_allowlist_v1.md).

At the starting checkpoint, `docs/` contains 193 tracked files:

| Content | Files |
| --- | ---: |
| Markdown documentation | 172 |
| Curated demo (HTML, CSS, JSON, four PNG/GIF pairs) | 11 |
| Governed/supporting figures (SVG, PNG, PDF) | 10 |

The Markdown population includes 49 protocols, 46 result reports, manuscript,
supplement, governance, research history, operational submission checklists,
API instructions and navigation. No local untracked/ignored files, symlinks or
underscore-prefixed paths were found under `docs/`. A targeted text scan found
no private home or temporary-directory paths. This is not a comprehensive
secrets audit or a fresh publication approval for every historical document.

These tracked documents are intended public repository records, but **they are
not the approved website**. Whole-folder publication would make documents and
figure files eligible for direct hosting, subject to the chosen build's
exclusions and transformations. With Jekyll disabled, Markdown may be served
as files rather than useful rendered navigation. Links that reach outside
`docs/` to source, outputs or submission files would not automatically acquire
corresponding website targets. Checklists and historical protocols could also
be mistaken for current website guidance. No specific raw provider payload was
identified in this directory inventory; the objection is a broader and
unreviewed hosting surface, not a claim of discovered secret data.

Ignored workstation files do not reach Pages merely by existing locally: Pages
builds from Git commits or an explicitly uploaded artifact. Future committed
files under a branch-based source would, however, enter its publication scope.
Do not rely on directory indexing or absence of navigation to protect files:
predictable direct URLs remain the relevant exposure boundary. The local test
server's directory-listing behavior is not evidence of Pages behavior.

## Deployment comparison and Jekyll decision

| Mode | Assessment |
| --- | --- |
| `main`, `/docs` | Technically sufficient for the demo, but publishes a much broader source tree and automatically follows source-branch updates. Not recommended under the exact asset contract. |
| Actions, artifact root `docs/demo` | Recommended. Upload only reviewed bytes; no site generation, analytics or provider dependencies. A small manually triggered workflow provides the necessary boundary. |
| Dedicated publication branch | Possible, but introduces another synchronization surface with no advantage over the narrowly scoped artifact upload here. |

**Is a custom workflow needed?** Not for static HTML in general. Yes for the
recommended exact-directory, manual-only deployment architecture. Branch/folder
hosting cannot select `docs/demo` directly: its supported source folders are
root or `/docs`. Even branch-based Pages uses GitHub's deployment infrastructure;
“no workflow” means no repository-authored deployment workflow.

GitHub documents branch/folder and Actions publication, source-folder choices,
manual triggers and default-branch environment protection in its
[publishing-source guidance](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

Branch publication normally uses Jekyll. If that alternative were separately
approved, put `.nojekyll` at `docs/.nojekyll`, the selected publishing root,
to request unprocessed static serving. A repository-root file is not the
correct substitute when `/docs` is the source. There are currently no affected
underscore paths in the demo. The recommended Actions workflow uploads the
static directory directly, with no Jekyll build and no `.nojekyll` needed.
Nothing was added during this review.

## URLs and verified paths

Recommended future entry:
`https://jeremybetz.github.io/moving-the-defense/`.

Alternative whole-`docs` entry:
`https://jeremybetz.github.io/moving-the-defense/demo/`.

The account/repository identity matches the Git remote and GitHub API. Neither
URL is claimed live. Uploading `docs/demo` as artifact root places its index at
the project root, not at an additional `demo/` prefix.

A temporary loopback static server simulated both prefixes. All 11 files under
each prefix returned HTTP 200 with byte-for-byte agreement: 22 comparisons.
Content types were `text/html`, `text/css`, `application/json`, `image/png` and
`image/gif` as appropriate. The HTML uses relative asset/style/manifest paths
and fragment navigation, with no root-relative asset assumptions. Repository,
README, reproduction, API, candidate-PDF and Metrica attribution links are
explicit HTTPS destinations, not fragile cross-root website paths.

The page was inspected in a desktop browser and at 390 pixels. The mobile
document width and scroll width were both 390 pixels; no horizontal overflow
was detected. Advanced and rejected sections start collapsed. Four native
`picture` sources select static PNG posters for `prefers-reduced-motion: reduce`,
with explicit GIF links retained. This pass verified that wiring structurally;
it did not force the system motion preference or claim an emulated runtime
test. Full GIF rendering and mobile card inspection also passed during the
preceding static-package preparation; no media bytes have changed since then.

## Source of truth and separately authorized integration

The contract is: generation code → explicit exporter → reviewed static package
→ commit → Pages. Do not regenerate on push or during deployment. The future
workflow validates the checked-in package and uploads only that directory.
Keep the existing “prepared, not yet deployed” README wording until live checks
pass; do not publish a dead future link as an active demo.

In a separately authorized implementation/deployment pass:

1. Add and review a manual-only `workflow_dispatch` workflow with pinned official
   actions, read-only checkout, only necessary Pages/OIDC deployment permissions,
   an explicit `main` gate and exact package/hash validation. Do not invoke the
   exporter, install analytical dependencies or read provider data.
2. Fetch origin and compare `origin/main` with the reviewed baseline above.
   Stop on unexpected advancement; do not silently rebase or force-push.
3. Normally merge the reviewed application branch into main. Validate the
   protected artifact set and static package before an explicitly authorized
   normal push. Verify the public committed files and final main revision.
4. In GitHub, use **Repository → Settings → Pages → Build and deployment →
   Source: GitHub Actions**. This terminology is documented by GitHub; the
   authenticated settings UI was not changed or exercised in this review.
5. Create/configure the `github-pages` environment with a selected-branch rule
   admitting only `main` and no tag-based bypass. Confirm the deployment job
   uses it. Do not accept a broader default protection rule merely because
   the environment was auto-created.
6. Dispatch the reviewed workflow on main and inspect the exact successful
   deployment revision and artifact. No custom domain or backend is needed.
7. Complete the logged-out acceptance checks below. Only then add a live demo
   link in a separately reviewed small documentation commit.

For comparison only, the rejected branch-source alternative would use
Settings → Pages → Build and deployment → Source: Deploy from a branch →
Branch: main → Folder: /docs → Save. Do not perform those steps under the
recommended architecture.

## Post-deployment acceptance and rollback

After separate authorization and deployment, require:

- Logged-out HTTP success for the project-root index, stylesheet, manifest,
  all four PNGs and all four GIFs, including diagnostic and rejected assets.
- Correct content types and decoded response-body hashes matching the reviewed
  payloads. Compare all eight media hashes and exact HTML/CSS content; transport
  compression is not a reason to compare compressed wire bytes instead.
- Confirm the deployed manifest corresponds to the approved commit and contains
  only the approved fields/files. Inspect the deployment artifact inventory,
  not just whether a few guessed forbidden URLs return 404.
- Desktop/mobile layout, actual GIF playback, all links, collapsed sections,
  explicit rejected labeling, and reduced-motion poster behavior on a browser
  with that preference enabled where available.
- No cache, technical CSV, coordinates, stable player identities, credentials,
  tokens, private filesystem paths or unapproved files in the deployment artifact.

The checked package contains no scripts, remote fonts, analytics, form or
backend. Hosting adds ordinary requests to GitHub's CDN, not a provider-data
processing path. External links create normal navigation only when followed.
Images remain provider-derived and permit approximate positional recovery;
static hosting does not turn them into anonymized data or broaden permission.

Rollback: unpublish/disable Pages first if exposure or misleading presentation
is discovered. Revert or correct the deployment change through normal commits
and remove any live navigation link as needed. Disabling a workflow alone does
not necessarily remove an already published site. Never rewrite Git history.

## Validation and closure

- Exact public inventory, schemas, committed exporter identity, frozen allowlist,
  provenance, all payload/media hashes, local links and private-path scan: pass.
- Approved external HTTPS links: checked anonymously; all six returned HTTP 200.
- Both local URL-prefix simulations and byte/content-type checks: pass.
- Focused exporter tests: 29 passed; no provider tests or analytical reruns.
- All 753 protected tracked files match the starting checkpoint byte-for-byte.
- Paper firewall: pass, with 42 existing nonblocking unresolved-path findings.
- Changed-artifact guard and whitespace validation: pass.

No demo content, science, historical artifacts, example selection, submission
material or GitHub settings changed. This report is the only intended commit:
`docs: review analyst demo Pages workflow`.

**Next action:** separately authorize implementation and review of the minimal
manual-only, exact-package Pages workflow; keep deployment gated until approved.
