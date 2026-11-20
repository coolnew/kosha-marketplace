# Contributing

Recipe improvements, documentation, and reproducible bug reports are welcome.
Use [issues](https://github.com/coolnew/kosha-marketplace/issues) for marketplace
problems and proposals. Kosha application bugs belong in
[Kosha's issue tracker](https://github.com/coolnew/kosha/issues).

## Workflow

1. Fork and clone this repository; create a branch from `main`.
2. Keep changes focused. Discuss a new pack or format change in an issue first.
3. Edit the package manifest, artifact and optional JSONL corpus under
   `packages/recipes/PUBLISHER/ID/VERSION/`. Keep publisher/ID stable; use a new
   version for changed published content, then regenerate catalog/indexes.
   The owner-approved pre-release format replacement retains versions `1.0.0`.
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
python xtask-marketplace.py --root . --check
python scripts/validate.py
python -m unittest test_xtask_marketplace
python -m unittest discover -s tests
python xtask-dco.py
```

The DCO check needs committed history. On a branch, use
`python xtask-dco.py origin/main..HEAD` to check only your new commits.
CI checks manifests, deterministic indexes, hashes, lengths/counts, corpus
shape, LF endings and sign-offs. It does not parse Kosha rules or execute corpus
expectations. Validate those with a current compatible Kosha build:

```sh
python xtask-marketplace.py --root . --check --cli /path/to/kosha
python scripts/validate.py --kosha /path/to/kosha
```

These load every recipe pack and check platform-applicable positive/negative
JSONL cases without scanning. Kosha validates every rule, including inactive OS
rules, capabilities, regexes and typed bindings. Check Recipe entities/captures
as well as exit status to distinguish recipes from built-in/literal fallbacks.
Describe each changed phrase on its intended OS and test it against a small
synthetic tree, recording expected matches and non-matches. Do not include
personal file inventories, private paths, or credentials in reports.

## Recipe review

Read the public [recipe authoring guide](https://github.com/coolnew/kosha/blob/main/docs/manual/recipe-authoring.md)
before writing rules. Regenerate with `python xtask-marketplace.py --root .`
without `--check` after intentional manifest/artifact edits; review the outputs.

Use clear whole phrases and narrow, understandable DSL. Avoid duplicate phrases
on the same OS. Use `os` for platform-specific locations. Catalog platforms must
describe exactly where the pack has active entries. Do not infer that caches,
database files, logs, or creative projects are safe to delete. Recipes contain
query data only; executable payloads and downloads are outside this catalog.
Keep packs within 1 MiB/256 rules, with at most 64 template/regex rules per
file. Regexes have at most 16 total capture groups, including unnamed groups.
Declare exact/template/regex/fuzzy capabilities across every OS rule. Include
working sample phrases and corpus cases for aliases, typed values, malformed
input, ambiguity, injection-like text, fallback and typos.

The active engine limits all sources together to 8,192 rules, 128 patterns,
32,768 phrases/aliases and 1,024 fuzzy phrases/aliases, with a conservative
16 KiB bound-output budget. Root catalogs are bounded to 256 KiB, each shard to
2 MiB, all catalog bytes to 16 MiB, and listed entries to 16,384. The generator
checks distribution budgets; Kosha checks rule semantics and active budgets.
Publisher names and hashes are identities/integrity checks, not signatures.

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

## Review-only insights

Insight packages use `packages/insights/PUBLISHER/ID/VERSION/`. Follow
[INSIGHTS.md](INSIGHTS.md) for the exact home-path, review-only contract and
resource limits. They cannot use recipe DSL, commands, regexes or destructive
actions. Keep session histories out of source fixtures. Validate all packages
with an insight-capable Kosha CLI before publication; old clients keep this
kind unavailable. Do not add optional recipe `cases` corpora to insight manifests.
