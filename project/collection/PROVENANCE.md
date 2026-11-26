# Data collection provenance

How the raw Reddit data behind this project was collected, what it covers, where it stopped, and what we know and do not know about why.
All times are UTC unless marked IST (UTC+5:30). Evidence is given as `file:line` (files in this folder, copied unchanged from the October `Project/` folder) or as a number we measured on 26 Nov 2026.

Project: "Solidarity or Blame: how Reddit communities discuss disruption in technology employment" (CSE3729 Computational Social Media Analysis).

## 1. What was collected, in one paragraph

Every post and every comment that the Arctic Shift archive returned for three subreddits (r/cscareerquestions, r/technology, r/programming) between 2025-01-01 and the collection date: **115,213 posts and 2,859,037 comments in 29,821 JSON batch files (6,163,721,355 bytes, about 5.74 GiB)**, saved on 23-24 Sep 2026. Nothing was filtered by keyword at collection time. Coverage is uneven (section 5): r/cscareerquestions has no posts, and the r/technology and r/programming comments stop months before the collection date.

## 2. The API

| Item | Value | Evidence |
|---|---|---|
| Service | Arctic Shift, a community-run historical Reddit archive (not Reddit's own API) | `src/collector.py:18` |
| Base URL | `https://arctic-shift.photon-reddit.com/api` | `src/collector.py:18` |
| Endpoints | `posts/search` and `comments/search` | `src/collector.py:113-114` |
| Parameters | `subreddit`, `after` (epoch seconds), `before` (epoch seconds), `limit`, `sort` | `src/collector.py:125-131` |
| `limit` | 100 (`limit_per_request`) | `config/collection_config.yaml:42`, `src/collector.py:25` |
| `sort` | `asc` (oldest first, so `after` can be moved forward) | `src/collector.py:130` |
| `after` / `before` | `after` starts at the config start date (2025-01-01) or the checkpoint; `before` is the config end date (2026-12-31) | `src/collector.py:36-38`, `:108-109`, `config/collection_config.yaml:12-14` |
| Paging | after each page, `after` is set to the newest `created_utc` in the page (+1 second if it did not advance) and written to a checkpoint | `src/collector.py:143-149` |
| Delay and retries | 0.1 s between requests, 5 retries, exponential back-off; the config comment says "Speeding this up!" | `config/collection_config.yaml:42-45`, `src/collector.py:52,67,74` |
| Storage | one JSON file per page per calendar month: `raw/YYYY-MM/<posts|comments>_batch_<epoch-ms>.json` | `src/collector.py:94-103` |

Almost every file holds exactly 100 items (29,665 of 29,821 files); the rest are short remainders, for example a page that straddles a month boundary and is split across two month folders.

## 3. There is no keyword filter at collection time

- The request parameters (`src/collector.py:125-131`) contain no search term. The collector downloads everything a subreddit posted in the window.
- The 23 layoff keywords in `config/collection_config.yaml:17-39` are read only by `src/processor.py:17,19-23,52` for the early pilot CSV (section 7). `collect` mode never touches them.
- The submitted Archive pipeline therefore screens the full corpus afterwards (`Archive/scripts/screen_disruption.py`, `disruption_rules.py`). That is why the analysis denominators are "all collected comments", not "keyword hits".

## 4. Configured versus collected subreddits

`config/collection_config.yaml:3-10` lists **7** subreddits: technology, cscareerquestions, programming, ExperiencedDevs, antiwork, jobs, careerguidance.
**3** are in the raw data (cscareerquestions, technology, programming). Measured with `verify_raw_timeline.py`: no ExperiencedDevs, antiwork, jobs or careerguidance file exists in `SUBJ/raw/`. The collector loops over the configured list in order (`src/collector.py:111-114`), so after r/programming the run either found nothing for the remaining four or was stopped (section 6).

## 5. Coverage and checkpoints

Checkpoint files (`checkpoints/*.json`, `{"last_timestamp": <epoch>}`) hold the newest content date fetched per (type, subreddit). Converted:

| Checkpoint | Epoch | Content date (UTC) | File written (UTC) |
|---|---|---|---|
| comments_cscareerquestions | 1790177306 | 2026-09-23 15:28 | 2026-09-23 15:29 |
| comments_programming | 1765530449 | **2025-12-12 09:07** | 2026-09-23 18:37 |
| comments_technology | 1749498694 | **2025-06-09 19:51** | 2026-09-24 20:42 |
| posts_programming | 1790178618 | 2026-09-23 15:50 | 2026-09-23 17:09 |
| posts_technology | 1790255462 | 2026-09-24 13:11 | 2026-09-24 13:14 |
| posts_cscareerquestions | **no file** | | |

The newest content date inside the raw batches equals the checkpoint in all five cases (checked with `verify_raw_timeline.py`; the checkpoint is the epoch second, the script prints it to the minute).

What this means for the analysis:

| Stream | Coverage | Complete up to the collection date? |
|---|---|---|
| r/cscareerquestions comments | 2025-01-01 to 2026-09-23 (962,337) | yes |
| r/cscareerquestions posts | none (0) | **no, never saved** |
| r/technology comments | 2025-01-01 to **2025-06-09** (1,657,900) | **no**, 15 months short |
| r/technology posts | 2025-01-01 to 2026-09-24 (76,782) | yes |
| r/programming comments | 2025-01-01 to **2025-12-12** (238,800) | **no**, 9 months short |
| r/programming posts | 2025-01-01 to 2026-09-23 (38,431) | yes |

Consequence: any cross-community comparison must use a shared window. This is why the headline layoff-share comparison (R1) uses Jan-Jun 2025, where all three communities have comments.

## 6. Collection timeline (from the epochs in the batch file names)

The file name `<type>_batch_<epoch-ms>.json` is the save time (`src/collector.py:99`). We re-read all 29,821 files (each file's first and last save time and its subreddit) with `verify_raw_timeline.py`; the output is reproduced here.

| Stream | Files | Items | First saved (UTC) | Last saved (UTC) |
|---|---|---|---|---|
| posts r/technology | 789 | 76,782 | 2026-09-23 06:43 | 2026-09-24 13:14 |
| comments r/technology | 16,584 | 1,657,900 | 2026-09-23 07:46 | 2026-09-24 20:42 |
| comments r/cscareerquestions | 9,644 | 962,337 | 2026-09-23 10:31 | 2026-09-23 15:29 |
| posts r/programming | 405 | 38,431 | 2026-09-23 15:29 | 2026-09-23 17:09 |
| comments r/programming | 2,399 | 238,800 | 2026-09-23 17:09 | 2026-09-23 18:37 |

Discrepancy to note: an earlier count gave 779 (technology posts) and 391 (programming posts) files. Counting the files on disk gives **789 and 405** (1,194 post files in total; 28,627 comment files; 29,821 overall, which matches `Archive/outputs/01_profile/profile.json` (`file_count`) and `CSMA_Project_Complete_Guide.md`, section 4). The item totals (115,213 posts, 2,859,037 comments) agree either way. Comment counts agree exactly.

Reconstructed order of events. It matches the collector's loop order (per subreddit: posts, then comments), and the last save of each stream agrees to the minute with the modification time of its checkpoint file:

1. **21 Sep (16:23 IST)**: the pilot (section 7) is produced from an earlier collection whose raw files are no longer on disk.
2. **23 Sep, 06:31-06:37**: `src/collector.py` and `config/collection_config.yaml` are last edited (file times, UTC). The main collection starts 6 minutes later.
3. **Run 1, 23 Sep**:
   - technology posts 06:43 to 07:46 (787 files);
   - technology comments 07:46 to 10:30 (4,453 files). They stop at content date **2025-02-01 21:39**, well before the end of the archive, and the run moves straight on;
   - cscareerquestions comments 10:31 to 15:29. There is no cscareerquestions posts step visible (no files, no checkpoint);
   - programming posts 15:29 to 17:09;
   - programming comments 17:09 to 18:37, ending at content date **2025-12-12 09:07**. Nothing is saved for the four remaining subreddits afterwards.
4. **Gap of 18.6 hours** (18:37 on 23 Sep to 13:14 on 24 Sep; IST: 00:07 to 18:44).
5. **Run 2, 24 Sep**: resumes technology only. The last 2 technology post files are saved at 13:14. Technology comments restart at 13:14 from content date **2025-02-01 21:40**, i.e. exactly where run 1 had stopped, and run for 7.5 hours (12,131 files) up to **2025-06-09 19:51** at 20:42.
6. **25 Sep 02:14 IST (24 Sep 20:44 UTC)**: `Project/data/raw.zip` is created, two minutes after the last checkpoint write.

### Why did the comment streams stop early?

What the evidence shows: the technology comment stream stopped twice at an arbitrary content date (2025-02-01, then 2025-06-09), and the r/programming comment stream stopped at 2025-12-12, while the same code reached the collection date for r/cscareerquestions comments and for both post streams. In run 1 the technology stop was followed immediately (within a minute) by the next subreddit, which is the behaviour of the code path below.

**The collector cannot tell "no more data" from "the API failed".** Both end the stream the same way and without an error:

- `_make_request` (`src/collector.py:46-77`) returns `None` when the API replies with a non-timeout `error` field (`:56-63`) and returns an empty list `[]` after the retries are used up (`:76-77`). On a timeout `error` it sleeps and retries (`:59-62`).
- `_collect_items` treats both as "finished": `if not items:` logs "No more ... found" at INFO level and `break`s (`src/collector.py:136-138`). The checkpoint is not advanced, the loop moves to the next stream, and the exit code stays 0.
- No file logging was configured (`setup_logging(name)` is always called without `log_file`: `src/collector.py:13`, `src/utils.py:13,26`), and `logs/` was empty. So the console output is gone.

Our assessment: the cause is either this silent-stop path (for instance Arctic Shift timeouts or errors on large result sets) or an interrupted run (a stopped terminal, a sleeping Mac; the 18.6-hour gap and the zip two minutes after the last write are consistent with a manual stop at the end). **No logs were kept, so this cannot be confirmed.** What we can say for certain is that the data on disk stops where the checkpoints say.

The same path explains the missing r/cscareerquestions posts: no `posts_cscareerquestions_checkpoint.json` exists and there are 0 r/cscareerquestions posts among the 1,194 post files, which means the first `posts/search` request for that subreddit returned nothing usable and the loop moved on to its comments.

## 7. The early pilot dataset (not in the main database)

`Project/data/processed/posts.csv` and `comments.csv` (written 21 Sep 2026, 16:23 IST; `reports/QA_REPORT.md`):

- **4,376 posts**: r/cscareerquestions 2,780, r/technology 1,456, r/programming 114, r/ExperiencedDevs 26. They span 2023-01 to 2026-09 (cscareerquestions 2023-01-03 to 2026-09-20).
- **All 4,376 post bodies are empty** (`QA_REPORT.md`: "Missing bodies: 4376"). These are titles only.
- **1,915 comments**, all in January and early February 2023 (cscareerquestions 407, programming 439, technology 1,069), 1,501 of them "orphans" whose post is not in the file.
- They were produced by `src/processor.py`, which keeps a record only if its title/body matches one of the 23 keywords (`:17-23,52`), then `src/privacy.py` replaced the author by a salted hash.
- **They are NOT in the main database.** `Archive/data/processed/reddit.sqlite` is built only from `raw/` (`Archive/scripts/profile_data.py:81`, `Archive/scripts/project.py:8`), and `raw/` starts on 2025-01-01. The pilot's raw files (2023-2026, including ExperiencedDevs) are not on this Mac: the earliest file in `raw/` was saved on 23 Sep. No result in the report depends on the pilot. Treat it as an early smoke test, and do not cite its numbers as part of the corpus.

## 8. Where the raw data lives

| Location | Content | Note |
|---|---|---|
| `SUBJ/raw/` (`.../Computational Social Media/raw`) | 21 monthly folders, 2025-01 to 2026-09, 29,821 JSON files, 6,163,721,355 bytes (about 6.16 GB, 5.74 GiB) | this is what the Archive pipeline expects at `ROOT/'raw'` (`Archive/scripts/project.py:8`); `Archive/` itself does **not** contain `raw/` |
| `Project/data/raw/` | identical: same 21 folders, same file count and same byte size per month (compared on 26 Nov) | the original collector output folder |
| `SUBJ/raw.zip` | 623,122,190 bytes, created 26 Nov 2026 18:48 IST | zip of `SUBJ/raw/` made for submission |
| `Project/data/raw.zip` | 643,427,582 bytes, created 25 Sep 2026 02:14 IST | made straight after collection stopped |

To run the Archive pipeline from scratch, place (or symlink) `raw/` next to `scripts/` inside `Archive/`.

Raw files keep the original Reddit author names (`author` field). They are not pseudonymised.

## 9. Pseudonymisation: two different schemes

- **Collector side (pilot only):** the environment variable `CSMA_SALT` (named in `config/collection_config.yaml:48`) is read by `src/privacy.py:16`, not by the collector itself. If it is not set, the literal fallback `"CSMA_DEFAULT_SALT"` is used and a warning is logged (`:17-18`). The hash is `sha256(author + salt)` (`:23`). The value actually used for the pilot was not recorded here; this document does not print it.
- **Archive side (the analysis):** `author_key = 'u_' + sha256(author.lower())[:24]`, **without a salt**, and `[deleted]`/`[removed]`/empty authors become `NULL` (`Archive/scripts/research_common.py:11-14`). The two schemes give different keys for the same person, so pilot hashes cannot be joined to Archive keys. A key without a salt can be reversed by hashing a list of known usernames; the project owner has said privacy is out of scope for the submission, so nothing was changed, but the limitation should be stated if asked.

## 10. TLS verification is disabled

`requests.get(..., verify=False)` at `src/collector.py:53`, with the warning silenced at `:10-11`. The comment says it is "for the community API". This means the connection to arctic-shift.photon-reddit.com was not authenticated, so a man-in-the-middle could have altered responses. The data was cross-checked indirectly (0 duplicate records, 0 JSON parse errors in `Archive/outputs/01_profile`), but not against a second source.

## 11. Known issues and the fix we would make

These describe a fix only. The copied code in this folder is deliberately left as it ran, because it is the provenance record.

| # | Issue | Evidence | Fix we would make |
|---|---|---|---|
| 1 | Silent stop: API error and end of data look the same | `collector.py:63,77,136-138` | Return a status, not `None`/`[]`. Treat a stream as finished only on a valid empty page whose `after` is past the newest known item; on error retry with back-off, then raise and exit non-zero. |
| 2 | No log file, so the cause of the early stops cannot be found | `utils.py:13,26`; `logs/` empty | Log to `logs/collect_<date>.log` with every request, status, item count and the first and last `created_utc` of each page. |
| 3 | r/cscareerquestions posts missing | no checkpoint, 0 files | Request in small windows (one month, then one week) instead of one open-ended range, so a large query cannot time out; run posts for this subreddit first and check the count against the archive's own totals. |
| 4 | r/technology and r/programming comments end in 2025 | checkpoints | Resume from the checkpoints with fix 1 and windowed requests (not done: the project owner chose not to download more data). The analysis already works on a shared window. |
| 5 | Page boundary can lose items | `collector.py:143-149`: next `after` equals the newest second already seen; the data has 0 duplicates, which suggests `after` is exclusive, so further items from that same second on the next page could be skipped. Not measured. | Re-request with `after = newest - 1` and deduplicate by `id`. |
| 6 | TLS check off | `collector.py:53` | `verify=True`; if the host's certificate fails, pin its CA bundle instead of disabling the check. |
| 7 | `retry_backoff_factor` in the config is never read; back-off base 2 is hard-coded | `collection_config.yaml:45`, `collector.py:67,74` | Read it from the config. |
| 8 | `main.py` catches every exception, prints it and exits 0 | `main.py:18-19` | Log with traceback and `sys.exit(1)`. |
| 9 | `process` mode loads everything into memory and was designed for the small pilot; it is unusable at 2.9 million records | `processor.py:27-78` | Not needed: the Archive pipeline (`profile_data.py` to `preprocess_data.py`, streaming into SQLite) replaced it. |
| 10 | Hard-coded default salt; unsalted keys in the Archive | `privacy.py:16`; `research_common.py:14` | Require `CSMA_SALT` (fail if unset) and use a keyed hash (HMAC-SHA256) in `author_key`. |

## 12. How to re-check these numbers

```
python3 -B verify_raw_timeline.py "/Users/vaibhav/Study/Sem 7/Computational Social Media/raw"
```

Reads the 29,821 files (about 50 seconds) and prints the table in section 6 plus the newest content date per stream, the number of files holding exactly 100 items (29,665 of 29,821), every gap of more than 30 minutes between saves (the 18.6 h gap between the two runs) and, per stream, how many files lie before and after such a gap (r/technology comments: 4,453 before, 12,131 after). It never writes anything.

The content date at which run 1 stopped for r/technology comments (2025-02-01 21:39) and the date at which run 2 resumed (2025-02-01 21:40) come from the first and last item of the files either side of that gap; they are not printed by the script.
