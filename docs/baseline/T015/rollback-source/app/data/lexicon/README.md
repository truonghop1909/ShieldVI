# Offline lexical data for ShieldVI

This directory is a versioned snapshot, not a live web service. Detection loads
`active.json` once at Python import. It never downloads these lists while analyzing
comments. Restart FastAPI after changing/rebuilding the data.

## Sources and attribution

The exact revisions, pinned raw URLs, local license files, SHA-256 checksums and
per-source counts are recorded in [manifest.json](manifest.json). Unmodified input
files and upstream documentation are retained in [sources/](sources/).

| Source | Declared upstream license | Local license |
| --- | --- | --- |
| [Vietnamese Offensive Words](https://github.com/blue-eyes-vn/vietnamese-offensive-words) — Copyright (c) 2023 Blue Eyes | MIT | [MIT text](sources/blue_eyes_vi_LICENSE.md) |
| [LDNOOBW V2 Vietnamese](https://raw.githubusercontent.com/LDNOOBWV2/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words_V2/main/data/vi.txt) | CC0-1.0 | [CC0 text](sources/ldnoobw_v2_LICENSE) |
| [LDNOOBW V2 English](https://raw.githubusercontent.com/LDNOOBWV2/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words_V2/main/data/en.txt) | CC0-1.0 | [CC0 text](sources/ldnoobw_v2_LICENSE) |

LDNOOBW V2 aggregates multiple collections. Its upstream [source attribution](sources/ldnoobw_v2_SOURCES.md)
and [README](sources/ldnoobw_v2_README.md) are retained alongside its declared license.
Language hints in source filenames are not assumed to be accurate for every entry.

## Import and activation policy

1. Decode UTF-8/BOM, normalize Unicode NFC, casefold and collapse whitespace.
2. Remove empty lines, full-line comments (`#` or `//`), control-character entries
   and entries with no alphanumeric characters. Keep punctuation within words.
3. Deduplicate exact normalized entries across all sources and merge provenance.
   Accents are preserved: `các`, `cặc` and `cac` are not interchangeable.
4. Apply only the aliases/patterns explicitly audited in `reviewed_rules.json`.
   These have `enabled_reviewed` status. This engineering review is not a human
   gold dataset or a measured accuracy claim.
5. Known ordinary/polysemous words are `excluded`. All other imports are
   `pending_review` with a provisional `ambiguous` category. They are not enabled
   or compiled as regexes. Presence in an upstream list is not approval.

`candidates.json` is the complete deduplicated review queue with canonical terms,
language hints, categories, activation status, reasons and source IDs.
`active.json` contains the reviewed import subset plus the project's explicit
aliases and bounded obfuscation patterns. Extra project aliases are counted
separately from entries actually imported from the three sources.

To approve a candidate, read its real usage, language and possible harmless
meanings; add a narrow alias/canonical mapping or explicit pattern in
`reviewed_rules.json`, choose one of the four categories below, and add regression
tests including a harmless contrast. Do not bulk-enable the pending queue.

| Category | Behavior |
| --- | --- |
| `profanity` | Presence of swearing; suggests reading the context, not a TOXIC label. |
| `directed_insult` | Potential insulting expression; a direct-attack candidate additionally needs an addressee or a rude imperative. |
| `ambiguous` | Reviewed abbreviation/polysemous form; shown as context only, without raising lexical review/risk. |
| `other_sensitive` | Medical, educational or news terminology; shown as context only, without treating it as profanity or an attack. |

Quoted/reported/apology contexts are explained and suppress the direct-attack
candidate. A profanity occurrence may still warrant manual reading. This is a
heuristic, not complete semantic understanding. Unaccented ambiguous words such
as `lon`, `cac`, `cu` and `buoi` do not become confident profanity matches.

## Rebuild and verification

From the repository root, using the project's Python environment:

```powershell
.\.venv\Scripts\python.exe scripts/import_lexicon.py
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd --prefix frontend run build
```

The default rebuild is offline and deterministic. To restore the exact pinned
upstream files, explicitly run `scripts/import_lexicon.py --download`. Updating
source revisions requires editing `sources/snapshots.json` and reviewing the diff;
new entries remain disabled unless included in the reviewed policy.

The matcher uses Unicode word boundaries, longest non-overlapping phrases and
explicit obfuscation rules. Returned spans and `matched_form` preserve the original
text, including casing and decomposed accents. `canonical_form`, `language`,
`reason`, `source_ids`, `start` and `end` are additive lexical-evidence fields;
existing endpoints and review storage are unchanged. ViSoBERT probabilities,
the deployment threshold 0.41 and repeated-harassment evidence remain independent.

## Snapshot counts (2026-10-29)

- Input: **14,240** lines from three dictionaries.
- Cleanup: **471** removed (24 comments, 11 invalid, 436 cross-source duplicates;
  zero blank lines or within-source duplicates in this snapshot).
- Unique imports: **13,769**.
- Imported entries enabled after explicit review: **224**.
- Pending review and disabled: **13,528**.
- Reviewed ordinary/polysemous entries excluded: **17**.
- Runtime: **20** reviewed rule families, **244** explicit aliases including
  project additions, plus narrowly bounded obfuscation patterns.

Per-source enabled counts can overlap because an entry may come from several
sources. Use the deduplicated totals in `manifest.json` when reporting global counts.
