# Local measured performance

Three authenticated browser contexts, four synthetic messages, actual approved-default V1.1 / default-v5. No new training or production load test.

| Measurement | n | P50 ms | P95 ms |
|---|---:|---:|---:|
| ack_fetch_ms | 4 | 20.5 | 31 |
| enqueue_sql_insert_ms | 4 | 0.157 | 0.179 |
| enqueue_commit_spacing_ms | 4 | 0.0 | 0 |
| queue_wait_ms | 4 | 37.5 | 50 |
| ai_analysis_ms | 4 | 74.215 | 123.395 |
| fanout_snapshot_render_observation_ms | 4 | 668.5 | 732 |
| author_analysis_visible_ms | 4 | 880.0 | 900 |

- ACK uses browser Resource Timing fetch duration through same-origin Vite proxy.
- Enqueue SQL duration is actual INSERT execution before commit, joined only to committed messages; commit/lock time is in ACK. Enqueue spacing is millisecond notification spacing in one atomic content/job commit, not isolated queue insertion CPU time.
- AI analysis includes neural/cache and context/target/repeated processing.
- Fanout includes SSE polling window, snapshot fetch, render and Playwright observation; not isolated network time.

Hardware: AMD64 Family 25 Model 80 Stepping 0, AuthenticAMD; logical CPUs 12, neural process capped2threads. Percentiles have tiny samples and are not release SLOs.
