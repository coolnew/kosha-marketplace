# Kosha marketplace

Community search recipes and review-only insight packs for [Kosha](https://github.com/coolnew/kosha), the
disk-usage and file-search tool. Recipes translate whole phrases into inspectable
queries over recorded file metadata. A match is not a recommendation to delete
anything. Loaded recipes work offline and do not execute scripts.

| Pack | Qualified ID | Version | Platform |
| --- | --- | --- | --- |
| [Linux Essentials](packages/recipes/coolnew/linux-essentials/1.0.0/pack.json) | `coolnew/linux-essentials` | 1.0.0 | Linux |
| [Windows Essentials](packages/recipes/coolnew/windows-essentials/1.0.0/pack.json) | `coolnew/windows-essentials` | 1.0.0 | Windows |
| [Search Power Tools](packages/recipes/coolnew/search-power-tools/1.0.0/pack.json) | `coolnew/search-power-tools` | 1.0.0 | All supported OSes |
| [Assistant session review](packages/insights/coolnew/assistant-session-review/1.0.0/pack.json) | `coolnew/assistant-session-review` | 1.0.0 | All supported OSes; requires new insight capability |

**Insight compatibility:** first published support is [Kosha 0.10.9](https://github.com/coolnew/kosha/releases/tag/v0.10.9),
with the `insight.locations.v1` engine capability. Older released versions
show it as unavailable and cannot install it. These are valuable
conversation records, not disposable cache; this pack provides review-only
findings and no cleanup actions. See [insight usage and authoring](INSIGHTS.md).

The Essentials packs cover development, server, database, office, design, video,
and audio files. Search Power Tools demonstrates exact aliases, typed size,
duration and path templates, named regex captures, and nonexecuting typo
suggestions. Its [corpus](packages/recipes/coolnew/search-power-tools/1.0.0/cases.jsonl)
checks successful translations, malformed values, injection-like text and typos.

## Install

Use a current Kosha build supporting indexed catalogs and extended recipes:

```sh
kosha marketplace sync
kosha marketplace search
kosha marketplace show coolnew/search-power-tools
kosha marketplace get coolnew/search-power-tools
kosha search --describe --json "documents larger than 20 MB"
kosha marketplace list
kosha marketplace uninstall coolnew/search-power-tools
```

For OS-specific recipes, get `coolnew/linux-essentials` or
`coolnew/windows-essentials`. Search shows compatibility; unsupported kinds or
capabilities show an unavailable reason. Publisher names identify packages;
they are not verified author signatures. Short IDs work only when unambiguous.

Sync pins the root, indexes and downloads to one Git commit and verifies index
hashes, byte lengths and counts before replacing the saved catalog. Get checks
artifact bytes, metadata, schema and required capabilities before installation.
Sync leaves installed packs alone. Search/show and installed recipes work
offline; sync/get need a connection. Get refuses an already installed identity.
Review updates before removing the old managed copy and installing its replacement.

Alternatively, download a pack's **Raw** JSON from a full commit SHA on GitHub,
or clone this repository. From a clone:

```sh
kosha marketplace install packages/recipes/coolnew/search-power-tools/1.0.0/pack.json
```

To validate or try it without installing:

```sh
kosha search --describe --json --recipes packages/recipes/coolnew/search-power-tools/1.0.0/pack.json "documents larger than 20 MB"
```

Install copies the source into `recipe-packs/PUBLISHER/pack-ID.json` under Kosha's
configuration directory. Uninstall removes only the managed copy, even when that
copy is corrupt; your downloaded original and personal recipes are preserved.
In the GUI, use **Sync recipe marketplace**, search for **marketplace recipe
packs**, or use **Install a recipe pack?** for local files.

## Format and authoring

[catalog.json](catalog.json) uses schema 1 and references hashed JSONL indexes,
including [indexes/recipes.jsonl](indexes/recipes.jsonl). Each index record has
kind, publisher, metadata, platforms, required capabilities, artifact path,
exact byte length and SHA-256. Author files live under:

```text
packages/recipes/PUBLISHER/ID/VERSION/
  manifest.json
  pack.json
  cases.jsonl       # optional author test corpus
```

Edit manifests and artifacts, then generate the catalog/indexes with
`python xtask-marketplace.py --root .`. Do not hand-edit generated hashes or
counts. An empty `platforms` list means all supported OSes. Per-rule `os` filters
control active recipes; manifest platforms control catalog availability.

Packs use schema 1 with `kind`, `metadata`, `requires`, and `recipes`. Supported
rules are `exact` (the default, with optional aliases), `template`, `regex`, and
`fuzzy-suggestions`. Templates and named regex captures bind typed values into
the query AST; captured text cannot inject query operators. Fuzzy typos produce
suggestions and never execute a corrected query. Declare every capability used,
including rules scoped to another OS. Unknown fields are errors. Future package
kinds may be cataloged as unavailable metadata. New insight-capable builds also
install the separate review-only contract in [INSIGHTS.md](INSIGHTS.md); recipe
capabilities do not authorize insight or plugin execution.

Follow the public [recipe authoring guide](https://github.com/coolnew/kosha/blob/main/docs/manual/recipe-authoring.md)
for complete manifest/corpus examples, field types, conflicts, limits and layered
validation, and the [marketplace reference](https://github.com/coolnew/kosha/blob/main/docs/manual/marketplace.md)
for engine budgets and trust boundaries. The
[query reference](https://github.com/coolnew/kosha/blob/main/docs/manual/query-language.md)
describes resulting DSL. A successful describe exit alone can be a built-in or
literal fallback: check Recipe entities, captures, expected DSL and synthetic
search results.

This owner-approved pre-release replacement retains catalog/pack schema `1`
and package versions `1.0.0`; Kosha is not publicly released yet. It replaces the
old flat `recipes/` layout. Existing pinned commits remain intact, and current
Kosha clients can also read legacy inline catalogs. After publication, changed
pack contents should use a new version with the same publisher/ID.

We maintain this repository directly through reviewed pull requests. See
[CONTRIBUTING.md](CONTRIBUTING.md), [MAINTAINING.md](MAINTAINING.md), and
[SECURITY.md](SECURITY.md) for checks, DCO sign-off, review and publication.

## License and attribution

Unless otherwise noted, this repository, including its seed recipe packs, is
dual-licensed under [MIT](LICENSE-MIT) OR [Apache-2.0](LICENSE-APACHE), at your
option. The seed packs originate from Kosha and retain their IDs, versions,
OS filters, and exact bytes.

Copyright (c) 2026 Neeraj Sharma <neerajsharma.9@outlook.com> and The kosha contributors.
Contributors retain copyright in their contributions. The [DCO](DCO) has its own
original Linux Foundation attribution and is reproduced verbatim.
