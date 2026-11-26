-- Candidate discussions with available replies, retaining missing-root status.
SELECT thread_id,subreddit,post_present,collected_comment_count,
       distinct_known_authors,max_resolved_depth,unresolved_depth_count
FROM threads WHERE post_broad_layoff=1 OR broad_comment_count>0
ORDER BY collected_comment_count DESC LIMIT 30;

-- Inspect incomplete branches explicitly rather than assigning guessed depths.
SELECT child_id,thread_id,parent_fullname,parent_present,same_thread,depth_status
FROM reply_edges WHERE depth_status!='resolved' LIMIT 30;

-- Most frequently observed known-author reply pairs (no meaning assigned).
SELECT source_author,target_author,reply_count,thread_count
FROM author_reply_edges ORDER BY reply_count DESC LIMIT 30;

-- Selected focus records and their collection context.
SELECT s.sample_id,s.group_name,s.stratum,r.kind,r.id,r.title,r.text,
       t.post_present,t.collected_comment_count
FROM reading_sample s JOIN records r USING(kind,id)
JOIN threads t ON t.thread_id=CASE WHEN r.kind='posts' THEN 't3_'||r.id ELSE r.link_id END
ORDER BY s.sample_id;

-- Basic substring search in keyword candidates; replace phrase as needed.
SELECT r.kind,r.id,r.subreddit,r.title,substr(f.clean_text,1,200) AS preview
FROM records r JOIN features f USING(kind,id)
WHERE r.broad_layoff=1 AND
      (lower(r.title) LIKE '%severance%' OR lower(f.own_text) LIKE '%severance%')
ORDER BY r.created_utc DESC LIMIT 20;

-- Broader employment candidates: lexical screens, not validated relevance.
-- Join by kind AND id; facets may overlap. Evidence preserves matched terms/fields.
SELECT r.kind,r.id,r.subreddit,r.title,substr(f.own_text,1,400) AS own_preview,
       s.ai_work_change,s.hiring_conditions,s.economic_policy,s.evidence_json
FROM disruption_screen s JOIN records r USING(kind,id)
JOIN features f USING(kind,id)
WHERE s.ai_work_change=1
ORDER BY r.created_utc DESC LIMIT 30;

-- Separate employment pilot; existing reading_sample remains the layoff pilot.
SELECT s.sample_id,s.group_name,s.stratum,r.kind,r.id,r.title,r.text,
       t.post_present,t.collected_comment_count
FROM reading_sample_employment s JOIN records r USING(kind,id)
JOIN threads t ON t.thread_id=CASE WHEN r.kind='posts' THEN 't3_'||r.id ELSE r.link_id END
ORDER BY s.sample_id;
