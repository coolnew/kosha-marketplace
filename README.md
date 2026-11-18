# Kosha marketplace

Community recipe packs for [Kosha](https://github.com/coolnew/kosha), the
disk-usage and file-search tool. Recipes translate whole phrases into Kosha's
query language. They select files and directories; a match is not a recommendation
to delete anything.

| Pack | ID | Version | Platform |
| --- | --- | --- | --- |
| [Linux Essentials](recipes/linux.json) | `linux-essentials` | 1.0.0 | Linux |
| [Windows Essentials](recipes/windows.json) | `windows-essentials` | 1.0.0 | Windows |

Both packs cover development, server, database, office, design, video, and audio
files. Choose the pack for the OS running Kosha. Some phrases overlap between
packs; OS filters keep the other platform's recipes inactive.

## Install

With a Kosha build that supports the public marketplace:

```sh
kosha marketplace sync
kosha marketplace search database
kosha marketplace show linux-essentials
kosha marketplace get linux-essentials
```

On Windows, use `windows-essentials` instead. Sync saves the catalog from `main`
at a specific Git commit. Get checks the pack's SHA-256 and metadata against
that saved catalog before installing it. Search and show use the saved catalog
offline; get needs a network connection. Installed recipes work offline.

Alternatively, open either pack link above and download its **Raw** JSON file,
or clone this repository. For reproducible downloads, select a full commit SHA
on GitHub before downloading. From a clone:

```sh
kosha marketplace install recipes/linux.json
kosha marketplace list
kosha search --describe "large rotated system logs"
kosha marketplace uninstall linux-essentials
```

For Windows, install `recipes/windows.json` and try `windows update logs`.
Install copies the source into Kosha's managed recipe directory. Uninstall
removes the installed copy, preserving your download and personal recipes.
Installing an existing ID fails; review a new version before uninstalling the
old version and installing its replacement.

To try a pack without installing it:

```sh
kosha search --describe --recipes recipes/linux.json files
kosha search --describe --recipes recipes/windows.json files
```

In Kosha's GUI, use **Sync recipe marketplace**, then search for **marketplace
recipe packs** in the command palette. Local files use **Install a recipe pack…**.
See the [Kosha recipe manual](https://github.com/coolnew/kosha/blob/main/docs/manual/search-recipes.md)
for query syntax, personal recipes, and platform behavior. These commands require
a Kosha build supporting the corresponding feature; older releases may not.

## Format and contributions

[catalog.json](catalog.json) uses catalog schema 1. Each entry contains
`kind: "recipe-pack"`, nested `metadata` matching its pack exactly (including
tag order), `platforms`, a relative `recipes/*.json` path, and the SHA-256 of
the pack's exact bytes. An empty `platforms` array means every supported OS.

Packs use `schema: 1`, `kind: "recipe-pack"`, `metadata`, and `recipes`.
Metadata contains `id`, `title`, `version`, `description`, and `tags`. Each recipe
contains `phrase`, `dsl`, and an optional `os` (`linux`, `windows`, or `macos`).
Omitting `os` makes a recipe available everywhere. Keep IDs stable and bump the
pack version for changes; schema numbers describe the layout, not pack releases.
Do not add fields or comments to version 1 JSON.

We maintain this repository directly through reviewed pull requests. See
[CONTRIBUTING.md](CONTRIBUTING.md) for checks, DCO sign-off, and review criteria,
[MAINTAINING.md](MAINTAINING.md) for catalog publication, and
[SECURITY.md](SECURITY.md) for private vulnerability reports.

## License and attribution

Unless otherwise noted, this repository, including its seed recipe packs, is
dual-licensed under [MIT](LICENSE-MIT) OR [Apache-2.0](LICENSE-APACHE), at your
option. The seed packs originate from Kosha and retain their IDs, versions,
OS filters, and exact bytes.

Copyright (c) 2026 Neeraj Sharma <neerajsharma.9@outlook.com> and The kosha contributors.
Contributors retain copyright in their contributions. The [DCO](DCO) has its own
original Linux Foundation attribution and is reproduced verbatim.
