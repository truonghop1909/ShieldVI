# Solo Annotation Studio

Open studio.html → Labeling and choose an ACCEPTED dataset version. The blind
view removes source labels and AI suggestions from conversation responses.
Read the full thread, actor pseudonyms, timestamps and parent links. Select a
comment, choose CLEAN/TOXIC/UNCERTAIN (shortcuts C/T/U outside text fields), target,
category, severity and context flags. UNCERTAIN requires notes. Labels are never
guessed. Target must be another participant. Repeated evidence must contain this
comment plus earlier, same-actor, same-target annotated attacks at distinct times.

Autosave waits 800ms and uses expected_revision. Explicitly complete Round 1,
then independently read/confirm Round 2 using the same authenticated reviewer.
Real-data review requires >=300 seconds since the last Round 1 update; synthetic
workflow demos allow zero gap and are not human gold. No second reviewer is
invented and no inter-annotator agreement is reported. Changing Round 1 makes
the old Round 2 confirmation stale and blocks snapshot export. Label changes
require a reason. History remains append-only. Resolve conflicts before leaving
the editor; a browser reload needs an explicit discard confirmation when dirty.

Export snapshot requires valid Round 2 for every comment and creates a separate,
hashed receipt and child dataset version. Source labels never change. UNCERTAIN
can remain in an exported reference but prevents binary training eligibility.
Snapshot state LOCKED refers to immutable exported evidence; the working review
session can continue, invalidating its current Round 2 as appropriate. Synthetic
origin/reference labels remain synthetic, including browser test entries.

Only admin can access Studio; reviewer_id comes from server authentication.
Session tokens are memory-only. Real sources remain quarantined pending rights
and privacy checks; Studio annotation does not waive T028 human acceptance.

T040_backend_fixed.log:20 related PASS. T040_browser_result.json:6 Chrome checks
cover unlabeled import, full context/blind view, autosave/two rounds, snapshot,
Round1 invalidation, blocked stale export and history. These are explicitly
synthetic browser automation, not human annotations. The first E2E exposed a
navigation race resetting notes; removing the editor during a pending navigation
and rejecting stale navigation responses fixed it. The failed log is retained.
