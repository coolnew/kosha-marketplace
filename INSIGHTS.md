# Review-only insight packs

In builds after 0.10.7, optional insight packs add explanations of known storage
locations to CLI and GUI findings. They are separate from search recipes and
from your personal `rules.d` files. Older releases show this package kind as
unavailable; syncing a new catalog does not add engine support to an old binary.

The first capability, `insight.locations.v1`, matches exact recorded directory locations and offers **review only**. It never proposes a Trash,
empty-cache or permanent-delete action. Session histories can be valuable user
data. A location being large does not make it disposable, and a pack does not
infer your profession or inspect conversations.


## Use and manage packs

```sh
kosha marketplace sync
kosha marketplace search sessions
kosha marketplace show coolnew/assistant-session-review
kosha marketplace get coolnew/assistant-session-review
kosha marketplace list
kosha . --insights
kosha marketplace uninstall insight-pack:coolnew/assistant-session-review
```

Use the actual catalog ID returned by search; catalog content can change.
`marketplace validate FILE` checks a local artifact without installing, scanning
or downloading. `marketplace install FILE` imports a validated copy. `list`
prints `kind:publisher/id` removal keys. A bare name or publisher/ID still works
for removal when unambiguous; use the printed key if recipes and insights share
an identity. A corrupt managed regular file can be removed by its stored key.

The GUI command palette installs, downloads and removes both kinds. Pack changes
refresh findings from the current recorded tree, without rescanning. Results
remain about that scan's time and scope. The CLI applies packs with `--insights`;
use an explicit cache option if you want a recorded drive scan instead of a fresh
scan. Sync alone never installs, updates or activates a pack.

## Author a pack

```json
{
  "schema": 1,
  "kind": "insight-pack",
  "metadata": {
    "publisher": "example",
    "id": "session-review",
    "version": "1.0.0",
    "title": "Session history review",
    "description": "Find a known history location without classifying it as disposable."
  },
  "requires": ["insight.locations.v1"],
  "platforms": [],
  "insights": [{
    "id": "session-history",
    "title": "Review session history",
    "detail": "Keep conversations you value. Review the owning application's retention options.",
    "subject": "directory",
    "location": {"base": "home", "path": ".assistant/sessions"},
    "action": "review-only"
  }]
}
```

Use a structured `location` with exactly `base` and `path`. All keys use single
words or snake_case. The same shape works in personal `rules.d` files.

| Base | Meaning of `path` | Example |
| --- | --- | --- |
| `home` | Relative to the detected account's home | `.codex/sessions` |
| `scan_root` | Relative to this scan's root | `build/artifacts` |
| `absolute` | Fully anchored Unix, Windows drive or UNC path | `/opt/example/records` |
| `cache` | Relative to the current account's OS cache root | `example/cache` |
| `temp` | Relative to the process temporary directory | `example` |
| `local_app_data` | Relative to Windows Local AppData; unavailable on other OSes | `Example/records` |

An empty relative `path` selects the base directory itself. Cache roots are
Local AppData on Windows, `~/Library/Caches` on macOS, and absolute
`XDG_CACHE_HOME` or `~/.cache` on other Unix systems. Tools can use different
locations: these bases do not discover custom profiles or app-specific overrides.
Providers describe the account/environment running Kosha, not the original
account or machine that produced an imported snapshot. `scan_root` is useful
for portable snapshot-relative packs; absolute paths are machine-specific.

Paths are literal and case-preserving, limited to 32 normal components and
1,024 UTF-8 bytes. Both slash styles are accepted. Windows extended drive and
UNC spellings (`\\?\D:\folder`, `\\?\UNC\server\share\folder`) normalize to their
ordinary spellings. Device namespaces, parent traversal, dot and empty components
are refused. No globs, regexes, fuzzy matching, environment expansion, content
extraction or executable hooks exist. Unknown providers or a target outside the
recorded scan yield no match. A matching filename is not a matching directory.
Author-supplied locations never trigger filesystem reads or another scan.

The unreleased `under-home` prototype has been removed without aliases. Replace
it with `"location": {"base": "home", "path": "..."}`; all location rules require
`"action": "review-only"`, including personal rules. Older prototype packs must
be reauthored/reinstalled; syncing alone never upgrades an installed copy.

`platforms` is empty for all OSes or a unique subset of `windows`, `linux`,
`macos`. Put OS-specific paths in separate packs with the appropriate filter.
All rules are validated even on an inactive OS. Titles, details and subjects
are limited to 160, 4,096 and 80 UTF-8 bytes. IDs follow the standard package
identifier rules; a finding's ID includes its marketplace publisher and pack.
Unknown fields, undeclared capabilities and any destructive action are refused.

At most 32 insights fit in a 256 KiB artifact. The managed store supports 32
packs and 64 rules in total, counting inactive OS rules too. Installation checks
the prospective store under a writer lock; rejection preserves earlier packs.
Matching uses binary lookup in the scan's existing child-name index. It adds no
per-file index or full-tree traversal for each insight; each rule resolves at
most 32 authored components. The ordinary minimum finding size still applies.
Recorded missing/unreadable data cannot establish an absent location or an exact
current size. Review-only findings contribute zero to the reclaimable total.

For the public marketplace, use
`packages/insights/PUBLISHER/ID/VERSION/{manifest.json,pack.json}` and a generated
`indexes/insights.jsonl` shard. Manifest metadata, platforms and required
capability must exactly match the artifact. The generator checks the contract;
`--cli /path/to/kosha` also invokes the native validator without installation.
Test positive paths, similar-name decoys, all declared bases, missing providers, wrong homes, scan subroots, inactive
OSes, permission gaps and byte/rule limits with synthetic data. Never seed real
conversation records or private paths. Publish changed pack content under a new
pack version. Unsupported future capabilities remain unavailable on old clients.

## Storage, trust and cleanup

Managed copies live in configuration `insight-packs/PUBLISHER/pack-ID.json`.
Uninstall removes only that managed copy; it preserves your source artifact,
personal rules, recipes and scanned files. Ordinary scanning and analysis use
installed copies offline. Only an explicit sync/download contacts the marketplace.
Downloaded bytes, metadata, length and SHA-256 must agree with the commit-pinned
catalog. Hashes establish byte consistency, not independent author trust.

Use the owning application's supported cleanup controls for tool-managed data.
For example, uv documents that direct cache modification is unsafe; use its
supported `uv cache clean` or `uv cache prune` commands after reviewing their
scope. Kosha displays guidance and does not run these commands. See
[uv cache safety](https://docs.astral.sh/uv/concepts/cache/#cache-safety).
