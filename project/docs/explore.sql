-- Execute against data/processed/reddit.sqlite using SQLite or Python sqlite3.

-- Actual UTC monthly coverage and explicit keyword shares.
SELECT created_month, kind, count(*) AS records,
       sum(direct_layoff) AS direct_mentions,
       round(100.0 * sum(direct_layoff) / count(*), 2) AS direct_mention_percent
FROM records GROUP BY created_month, kind ORDER BY created_month, kind;

-- Subreddit composition.
SELECT subreddit, kind, count(*) AS records,
       sum(direct_layoff) AS direct_mentions
FROM records GROUP BY subreddit, kind ORDER BY kind, records DESC;

-- Comments from explicit keyword-matching posts, including replies with no keyword.
SELECT c.id, c.created_utc, c.subreddit, p.id AS post_id,
       p.title AS post_title, c.parent_id, c.text, c.score
FROM records c JOIN records p ON p.kind='posts' AND c.link_id='t3_' || p.id
WHERE c.kind='comments' AND p.direct_layoff=1 AND c.text_state='available'
LIMIT 100;

-- Reconstruct a selected thread: replace POST_ID with a post ID.
SELECT id, parent_id, created_utc, text, score, text_state
FROM records WHERE kind='comments' AND link_id='t3_POST_ID'
ORDER BY created_utc;

-- Most discussed keyword-matching posts; reported counts are snapshot metadata.
SELECT id, created_month, subreddit, title, num_comments, score
FROM records WHERE kind='posts' AND direct_layoff=1
ORDER BY num_comments DESC LIMIT 30;
