# Contributing

Recipe improvements, documentation, and reproducible bug reports are welcome.
Use [issues](https://github.com/coolnew/kosha-marketplace/issues) for marketplace
problems and proposals. Kosha application bugs belong in
[Kosha's issue tracker](https://github.com/coolnew/kosha/issues).

## Workflow

1. Fork and clone this repository; create a branch from `main`.
2. Keep changes focused. Discuss a new pack or format change in an issue first.
3. Edit the pack, bump `metadata.version` for changed published content, and
   update its catalog metadata and SHA-256 together. Keep the pack ID stable.
4. Run the checks below, then commit with `git commit -s` and open a pull request.
   Include the purpose, affected OS, example phrases, expected matches and
   non-matches, and the Kosha version and validation results.

Use UTF-8 and LF line endings for text files on every platform. `.gitattributes`
and `.editorconfig` describe these defaults. JSON must not have comments, extra
fields, or a byte-order mark. Preserve notices and attribution. New Python
source should carry the project's SPDX license and copyright header.

## Checks

Python 3.12+ is sufficient for repository checks; no third-party packages needed:

```sh
python scripts/validate.py
python -m unittest discover -s tests
python xtask-dco.py
```

The DCO check needs committed history. On a branch, use
`python xtask-dco.py origin/main..HEAD` to check only your new commits.
CI checks structure, hashes, platform coverage, LF endings, and commit sign-offs.
It does not parse Kosha's query language. Validate DSL with a compatible Kosha
build before submitting pack changes:

```sh
python scripts/validate.py --kosha /path/to/kosha
```

This runs `kosha search --describe --recipes FILE files` for every pack.
Kosha validates all recipes, including those scoped to a different OS.
Also describe each changed phrase on its intended OS and test it against a small
synthetic tree, recording expected matches and non-matches. Do not include
personal file inventories, private paths, or credentials in reports.

## Recipe review

Use clear whole phrases and narrow, understandable DSL. Avoid duplicate phrases
on the same OS. Use `os` for platform-specific locations. Catalog platforms must
describe exactly where the pack has active entries. Do not infer that caches,
database files, logs, or creative projects are safe to delete. Recipes contain
query data only; executable payloads and downloads are outside this catalog.
Keep packs within 1 MiB and 256 recipes, and the catalog within 256 KiB and
256 entries. Preserve tag order when copying metadata to the catalog.

## Developer Certificate of Origin

Every commit must include your DCO sign-off. Read [DCO](DCO) before signing.
Configure your own Git name and email, then use:

```sh
git commit -s -m "fix(recipes): narrow the log-file query"
```

Git adds `Signed-off-by: Your Name <your.email@example.com>`. This certifies your
right to submit under the project license. It is not a cryptographic signature
or copyright assignment. Do not add `Co-authored-by` trailers. Multiple people
in the contribution chain may add their own sign-offs when appropriate.
For a missing sign-off on your latest commit, use
`git commit --amend -s --no-edit`. Coordinate before rewriting a shared branch.

Contributions are licensed `MIT OR Apache-2.0`. The project notice is
`Copyright (c) 2026 Neeraj Sharma <neerajsharma.9@outlook.com> and The kosha contributors`.
You retain copyright in your work. Preserve third-party notices; submit only
material you have the right to contribute under these terms. Keep the DCO text
and its Linux Foundation attribution verbatim.

Follow our [code of conduct](CODE_OF_CONDUCT.md). Maintainers review changes
before merging; there is no guaranteed response time.
