# Realtime demo

From the project root in PowerShell:

```powershell
.\scripts\demo_realtime_studio.ps1
```

The launcher creates a new local SQLite database and demo accounts, random
service credentials and free loopback ports. It starts the opt-in Social/AI
factories, incremental worker, both frontends and idle CPU training/evaluation
workers. Seven independent Chrome contexts open and log in automatically:
five normal accounts (Alice, Bob, Carol, Dave, Emma), moderator and Studio.
Credentials never enter URLs or bundles. The main screen is the Social Feed:
create a post, then other accounts select its card and comment/reply.
AI loads the existing approved V1.1 default, threshold0.41 and default-v5 rules.
This is separate from the existing research Dashboard/runtime.

For manual login with a password you know, start a new session using:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_realtime_studio.ps1 -AskPassword
```

Enter a12–128character password when prompted (input is hidden). This password
is used for `live_alice`, `live_bob`, `live_carol`, `live_dave`, `live_emma` and
`live_admin` in that new disposable demo session. It is not written to a
credential file, URL or log. It cannot recover the random password of an older
session. Automatic browser login remains available; default runs still generate
a random password. Each session uses its own printed frontend URLs.

Wait until the console prints `DEMO_READY` and Chrome opens. Startup now prints
each service, elapsed wait and its log path. In the startup-fix check, AI alone
took21.5seconds to become ready. Ctrl+C cancels startup/stops the demo; it is not
needed to proceed. If a service exceeds90seconds or exits, read the named log.
Operator interruption now stops owned processes without a Python traceback.

Database preparation also prints separate Base schema and Live schema steps,
elapsed time and dedicated log paths (`T043_base_schema.log` and
`T043_live_schema.log`). Each step has a90second limit and stops its owned
process on timeout or Ctrl+C. `Ctrl+C received` means startup was interrupted;
run the launcher again and wait for `DEMO_READY` to use the interfaces.

Five-to-seven-minute walkthrough:

The feed shows compact post cards with author initials, timestamp and a
**Đang xem** badge on the selected post. Use **Xem bài và bình luận** to open
or refocus that post. The feed updates automatically; pagination appears only
when there are more posts than one page can show.

Selecting **Xem bài và bình luận** now scrolls to the selected post and focuses
the composer once its snapshot has loaded. It is directly below the post,
above the comment list and pagination. **Viết bình luận** is a real button:
click it to focus the text field, type, then use **Gửi tin nhắn**. Clicking the
same post again focuses the composer again; background refresh does not steal
focus or clear drafts. If using a tab opened before this UI update, reload it
once. The comment text field is labeled **Nội dung tin nhắn** and its submit
button is **Gửi tin nhắn** in the current live screen.

Account usernames now appear in the feed, post and comment headers. Use
**Trả lời** on a comment: the composer shows `@username` and the quoted parent;
the saved reply shows its author and `Trả lời @username`. The actual parent ID
is sent to Social API and AI context; a reply alone never means an attack.
Moderator shows readable actor/target names with canonical IDs retained in
evidence. Names are display metadata and do not change the classifier input.

This extension includes backend changes: a browser refresh alone cannot load
new Python routes into an already-running server. Stop the old demo and start
again with `demo_realtime_studio.ps1 -AskPassword`, then use the newly opened
tabs/URLs. The launcher creates a new demo session; older session DBs and logs
remain in their original `reports/task_rollout_20261104/demo_*` directories.
The UI falls back to the older public feed while an old server is still running.

### Quick JSON test inside Admin

1. Open the Moderator/Admin `/live.html` page and log in as `live_admin`.
2. Select **Test AI bằng JSON** next to **Hàng chờ realtime**.
3. Paste a conversation JSON, choose **Nhập file JSON**, or **Nạp JSON mẫu**.
4. Click **Phân tích hội thoại**. Progress shows analyzed/total comments; use
   **Hủy phân tích** to stop between comments.
5. Read raw score separately from Assessment/Policy, reply recipient separately
   from attack target, and inspect Context/lexicon plus repeated evidence.
6. **Tải kết quả JSON** exports the complete analysis for that input.

The input shape matches the basic old Dashboard: `thread_id`, optional
`profile: "conservative"`, `comments[]` with `comment_id`, `user_id`, `text`,
timezone-aware `timestamp` and optional `parent_id`, `mentioned_user_ids`.
Parents must precede replies; maximum50comments/128KiB. Use pseudonymous actor
IDs and parent links rather than embedding human reference labels. Test data is
not posted or added to training; results are temporary in memory and should be
exported before restarting. The server-side job uses the current approved model
and default-v5, threshold0.41. It does not offer a model/threshold override.

This tab needs the new Python backend routes. For an already-running demo,
stop it and relaunch with `demo_realtime_studio.ps1 -AskPassword`, then use the
newly opened Admin tab. Earlier demo session DBs/logs remain in reports; a new
launch does not automatically reopen its old Social posts or transient tests.

1. Alice uses **Đăng bài**. The new card appears in the other accounts' feeds
   after policy publication; select **Xem bài và bình luận**. Alice adds a
   normal comment. Bob receives it after existing publication
   policy; queued text is private to its author/staff. Neither page needs reload.
2. Bob uses Reply on Alice's message. Send two explicit personal insults at
   least a second apart. Read actual scores and grounded actor→target evidence
   in Moderator Live. A reply alone is not an attack. AI does not hide content.
3. Try intervention, a quoted insult, apology or non-directed profanity. Explain
   the separate raw/context/lexicon/policy layers and v5 language limitations;
   do not promise every sentence gets the right label.
4. Moderator selects the comment, reads full context and supplies a reason to
   hide. The author retains the hidden item, appeals, and the moderator reloads
   detail, reviews the appeal and restores. Review/audit are manual and versioned.
5. Show Dataset/Labeling/Training/Models tabs. Use the dedicated synthetic smoke
   file for training if demonstrating a new operator-started run; it does not
   replace existing models. See the other guides for the full workflow.

Stop from another PowerShell window:

```powershell
.\scripts\demo_realtime_stop.ps1
```

Ctrl+C in the owning launcher also stops its processes. Interactive demo data
and logs stay in the printed reports/task_rollout_20261104/demo_* directory.
A new launch creates a new session; it does not resume the old account sessions.
Do not enter real private data. No reset, DROP, push or deploy is performed.

Automated checks (headless, no training): `-HeadlessCheck` runs the real neural
two-client/moderator workflow; `-InteractiveCheck` checks seven automatic logins,
all Studio tabs and the actual stop script. `-FeedCheck` additionally checks
five users posting/commenting, repeated evidence, deep links, review/appeal,
reconnect, literal XSS text, long threads and owned AI offline/recovery.
`-StudioCheck` replays synthetic upload/export and solo annotation UI tests.
These checks retain a fresh demo DB; automated synthetic labels are not human gold.
For a weak machine, keep the CPU trainer idle and wait for truthful PENDING/
COMPLETED states. If a checkpoint is unavailable, startup reports the error;
there is no automatic fake-score fallback.

## Downloaded exports

New headed demo windows retain exports in the printed session directory's
`downloads/` folder. JSON/CSV/JSONL files keep their real extension and a readable
prefix with UTC timestamp/nonce, avoiding replacement on repeated downloads.
Chrome's Show in folder opens that location. Existing windows created before
the fix need a new browser context; frontend refresh alone cannot reset the old
Playwright download policy. See [export fix and current environment limits](../../realtime_moderation/DOWNLOAD_EXPORT_FIX.md).
