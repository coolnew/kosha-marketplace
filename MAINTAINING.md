# Maintaining the marketplace

This is the source of truth for the public catalog. Changes are developed and
reviewed here; no private Kosha checkout or promotion tooling is required.
Keep application code and query-language changes in the Kosha repository.

## Review and publish

1. Review provenance, licensing, phrase collisions, supported OSes, and query
   behavior. Require DCO sign-off on every contributed commit and no
   `Co-authored-by` trailers. Run repository CI and compatible Kosha CLI checks.
2. For changed published packs, require a new version with the same publisher/ID.
   The owner-approved pre-release format replacement keeps schema 1 and versions
   1.0.0. Edit manifests, artifacts and corpora; regenerate with
   `python xtask-marketplace.py --root .`, then check using
   `python xtask-marketplace.py --root . --check --cli /path/to/kosha`.
   Commit matching artifacts, manifests, indexes and root together. The tool
   derives exact byte lengths, hashes and counts without bumping versions.
3. Merge reviewed changes to `main`. Preserve sign-offs when merging or
   squashing, and sign off any new merge or squash commit yourself. Do not
   attribute someone else's DCO certification without their consent.
4. Record the resulting full commit SHA. Verify unauthenticated downloads of
   `catalog.json`, all referenced index shards and changed artifacts from
   `https://raw.githubusercontent.com/coolnew/kosha-marketplace/<SHA>/<path>`.
   Recheck their lengths, counts and hashes. GitHub source archives must include
   the manifests, indexes, corpora and packs.
5. With an isolated Kosha profile, sync, search, show, get, resolve a host-OS
   phrase, and uninstall. Confirm other-OS entries are inactive, offline use
   works after install, and personal recipes and downloaded originals survive
   uninstall. Check qualified IDs, typed captures, ambiguity errors and typo
   suggestions without executable queries. Unsupported kinds/capabilities must
   show unavailable reasons. Check GUI discovery, installation and interpretation.

A merge to `main` publishes the next catalog snapshot; a tag or separate
release is not required. Sync updates cached discovery without replacing
installed packs. Users explicitly remove and reinstall a pack to update it.
Publish corrections with a new pack version rather than rewriting history.
Removing an entry stops future discovery but does not remove installed copies.

## Retaining old versions

Only one version per publisher/ID may be listed. Use `listed:false` in an older
manifest to retain its artifacts without advertising them. Generated indexes
exclude author-only `cases` and `listed` fields. Remove retired index files
deliberately after review; the generator refuses stale extra shards and never
deletes them. Maintain the indexed layout only; do not generate flat compatibility copies.

## Repository settings

Repository administrators should protect `main`, require pull requests and
passing **Catalog validation** and **DCO** checks, and disable force pushes and
branch deletion. Require an independent review when another maintainer is
available. These settings are configured in GitHub, not by the files in this
repository. Keep Actions permissions read-only and avoid workflows that run
untrusted pull-request code with secrets or write tokens.

Triage bugs and proposals in issues. For security or conduct reports, use the
private email in the corresponding policy. Keep policy changes public and
reviewable; document compatibility changes before altering the catalog format.

## Insight capability boundary

The first insight kind keeps schema 1 and uses a new explicit capability,
`insight.known-home-review.v1`. It permits only review-only exact home paths,
32 components per rule, 32 rules per 256 KiB pack, and 64 rules across installed
managed packs. See [INSIGHTS.md](INSIGHTS.md). Unknown capabilities stay unavailable
on old clients. The generator checks artifact/manifest agreement; `--cli` also
runs the native side-effect-free validator. Test install/findings/remove with
an isolated synthetic home before pushing. Do not infer a persona or add
history-deletion, shell, AI-sharing or app-cleanup behavior to this capability.
