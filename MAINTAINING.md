# Maintaining the marketplace

This is the source of truth for the public catalog. Changes are developed and
reviewed here; no private Kosha checkout or promotion tooling is required.
Keep application code and query-language changes in the Kosha repository.

## Review and publish

1. Review provenance, licensing, phrase collisions, supported OSes, and query
   behavior. Require DCO sign-off on every contributed commit and no
   `Co-authored-by` trailers. Run repository CI and compatible Kosha CLI checks.
2. For pack changes, require a new version with the same stable ID. Update the
   catalog metadata and SHA-256 in the same commit. Hash exact LF file bytes:
   `python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('recipes/linux.json').read_bytes()).hexdigest())"`.
3. Merge reviewed changes to `main`. Preserve sign-offs when merging or
   squashing, and sign off any new merge or squash commit yourself. Do not
   attribute someone else's DCO certification without their consent.
4. Record the resulting full commit SHA. Verify unauthenticated downloads of
   `catalog.json` and all changed packs from
   `https://raw.githubusercontent.com/coolnew/kosha-marketplace/<SHA>/<path>`.
   Recheck their hashes. GitHub source archives must include the packs.
5. With an isolated Kosha profile, sync, search, show, get, resolve a host-OS
   phrase, and uninstall. Confirm other-OS entries are inactive, offline use
   works after install, and personal recipes and downloaded originals survive
   uninstall. Check GUI flows for changes affecting discovery or installation.

A merge to `main` publishes the next catalog snapshot; a tag or separate
release is not required. Sync updates cached discovery without replacing
installed packs. Users explicitly remove and reinstall a pack to update it.
Publish corrections with a new pack version rather than rewriting history.
Removing an entry stops future discovery but does not remove installed copies.

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
