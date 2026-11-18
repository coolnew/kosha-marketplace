# Security policy

Report suspected vulnerabilities privately to Neeraj Sharma at
**neerajsharma.9@outlook.com**. Include the catalog commit SHA, affected publisher/pack ID
and version, Kosha version, OS, and a minimal synthetic reproduction.
Avoid public exploit details until the maintainer has reviewed the report.
Do not send credentials, personal indexes, or unredacted private paths.

Reports about catalog integrity, unsafe paths, misleading recipes, and pack
validation are in scope. Ordinary errors and requests belong in
[issues](https://github.com/coolnew/kosha-marketplace/issues).
Fixes target the current catalog on `main`; there is no guaranteed response
or remediation time. Older installed packs do not update automatically.

SHA-256 checks consistency with a catalog snapshot; it is not a publisher's
digital signature. Review pack provenance and queries. A matching file is not
necessarily safe to delete. For application vulnerabilities, follow
[Kosha's security policy](https://github.com/coolnew/kosha/blob/main/SECURITY.md).

Publisher names are catalog identities, not verified signatures. Index hashes,
lengths and counts and artifact capabilities must match the pinned snapshot.
Typed captures bind values into a parsed query; they do not grant execution or
write access. Unknown package kinds and unsupported capabilities cannot enable
plugins or scripts. Report bypasses of size, regex or aggregate matching budgets.
