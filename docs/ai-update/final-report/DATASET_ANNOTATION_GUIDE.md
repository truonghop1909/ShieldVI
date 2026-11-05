# Dataset and annotation guide

Datasets accepts UTF-8 CSV/JSON/JSONL <=1MiB and1000comments. ZIP/code/model files
are rejected. Map canonical field names to CSV columns; preview the original
file and normalized50-row pages. Inspect row errors, PII/formula warnings,
exact/near overlap, source hashes and thread splits before using a version.
Duplicate requests replay one version. A changed source/annotation produces a
separate child version, never overwrites its parent. Export CSV/JSONL/report
through the authenticated UI.

For an unlabeled dataset, choose UNLABELED and omit label values. Open Labeling,
read the entire conversation and select each comment. Choose CLEAN/TOXIC/
UNCERTAIN, category, severity, target/context flags and repeated evidence.
UNCERTAIN requires notes. Raw AI predictions/source labels are hidden in blind
mode. A reply recipient is not automatically a directed attack target.

Wait for autosave confirmation, complete Round1, then read and confirm Round2
with the same account. Real-data review requires >=300seconds since the last
Round1 update. Synthetic demos allow zero gap and remain synthetic reference.
Changing Round1 invalidates the previous Round2. A conflict requires reloading
and reviewing the current revision; do not overwrite it silently. Label changes
need a reason. Inspect history and export a locked annotation snapshot once
every comment has valid Round2. It creates a new immutable dataset version.
UNCERTAIN may stay in the reference export but cannot become a binary target.

Admin is the current authorized Studio role. Browser test annotations are
explicitly synthetic automation, not a human review. Real uploads remain
quarantined until source URL/license/consent/receipt and privacy are verified.
Uploading a HUMAN_REVIEWED claim does not establish human gold.

T028 still requires200real conversations, permitted provenance, anonymization,
development/test leakage audit and your own two review rounds. No request to
label immediately is made. A single reviewer is not two independent annotators.
Formal T029/T030 release evidence cannot be replaced with synthetic metrics.

Details: [Datasets](../../ml_studio/DATASETS.md),
[solo annotation](../../ml_studio/ANNOTATION.md), and the existing formal
[readiness report](FINAL_READINESS_REPORT.md).
