Hướng dẫn local hiện hành: [demo Windows](REALTIME_DEMO_GUIDE.md),
[ML Studio](TRAINING_STUDIO_GUIDE.md) và [báo cáo T034–T043](T034_T043_FINAL_REPORT.md).
Formal real-world acceptance vẫn xem [readiness và blocker](INDEPENDENT_READINESS.md).

Phần handoff ngày 03/11/2026 bên dưới là nội dung lịch sử, được giữ để tra cứu;
các trạng thái candidate và số liệu trong phần đó không thay thế báo cáo mới hơn.

# ShieldVI — Evidence handoff, 03/11/2026

[Technical report](TECHNICAL_REPORT.md) · [Error analysis](ERROR_ANALYSIS.md) · [Reproduction/demo](REPRODUCTION.md) · [Artifact inventory](ARTIFACTS.json).

REAL0/200. Synthetic500/500 (200 imported,300 newly authored),5115 AI labels/human0. Eleven successful batch manifests. [Dataset](../../../datasets/synthetic_conversations/genz_v2/README.md) contains annotated JSONs, API-clean JSONs, CSVs, JSONLs and provenance. Technical validation passes; semantic novelty/naturalness are not established.

Candidate NOT_TRAINED:11340 rows prepared; local CUDA and exact GPU/cost receipt missing. V1/threshold0.41/defaultV1.1/test/DB remain unchanged. Development-only V1 Macro-F1=0.739974 on617 AI references; Hybrid target coverage31.43%, repeated recall0/7. No improvement or real-world performance claim.

T028,T029,T031 remain BLOCKED; T030 synthetic-development evaluation, T032 verification and this evidence-only T033 handoff are complete. Original T020 captures support a separate B0–B3 replay on five previously used fixtures; they do not turn the new challenge into an original-baseline ablation. Missing experiments and unresolved errors are retained here. This handoff does not certify a new model release.
