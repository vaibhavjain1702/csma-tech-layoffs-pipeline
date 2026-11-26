#!/usr/bin/env python3
"""Produce descriptive, text, and conversation statistics as CSVs.

Keyword flags are retrieval heuristics, not validated thematic labels.
Uses Python's standard library; no notebooks, UI, or paid models are required.
"""
import argparse
import csv
import json
import re
from collections import Counter,defaultdict
from datetime import datetime,timezone
from project import research_db,ANALYSIS,PREPROCESS,ensure_dirs,export_query
from research_common import URL

WORDS=re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*",re.UNICODE)
# Baseline function words. Negation and the retrieval words are deliberately retained.
STOP=set('a an the this that these those i me my mine we us our ours you your yours he him his she her hers it its they them their theirs and or but if as at by for from in into on of to with is am are was were be been being do does did have has had will would can could should may might just very really also so than then there here what when where who which how any some all each every much many more most other about over under out up down through while because get got going go said says say https http www com'.split())


def weighted_quantile(counts,q):
    total=sum(counts.values())
    if not total:return None
    position=(total-1)*q;lower=int(position);upper=min(lower+1,total-1)
    values={};cumulative=0
    for value,count in sorted(counts.items()):
        cumulative+=count
        for rank in (lower,upper):
            if rank not in values and rank<cumulative:values[rank]=value
        if len(values)==len({lower,upper}):break
    return values[lower]+(values[upper]-values[lower])*(position-lower)


def save_rows(path,columns,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(columns);writer.writerows(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--match',choices=['direct','broad'],default='direct')
    parser.add_argument('--top-terms',type=int,default=100)
    parser.add_argument('--min-documents',type=int,default=3)
    args=parser.parse_args()
    if args.top_terms<1 or args.min_documents<1:parser.error('Counts must be positive')
    ensure_dirs();generated={}
    with research_db() as db:
        generated['monthly_summary']=export_query(db,ANALYSIS/'monthly_summary.csv','''SELECT
            r.subreddit,r.kind,r.created_month AS month,count(*) AS records,
            sum(r.direct_layoff) AS direct_keyword_matches,sum(r.broad_layoff) AS broad_keyword_matches,
            round(100.0*sum(r.direct_layoff)/count(*),3) AS direct_match_percent,
            sum(r.text_state='available') AS available_bodies,sum(r.text_state='removed') AS removed_bodies,
            sum(r.text_state='deleted') AS deleted_bodies,sum(r.text_state='empty') AS empty_bodies,
            sum(f.author_unknown) AS unknown_authors,sum(f.likely_bot) AS bot_name_flags,
            round(avg(r.score),3) AS mean_score,
            round(avg(CASE WHEN r.text_state='available' THEN f.word_count END),3) AS mean_available_body_words
            FROM records r JOIN features f USING(kind,id)
            GROUP BY r.subreddit,r.kind,r.created_month ORDER BY r.subreddit,r.kind,r.created_month''')
        print('Monthly coverage and text statistics complete',flush=True)
        generated['preprocessing_audit']=export_query(db,PREPROCESS/'audit.csv','''SELECT r.kind,
            count(*) AS records,sum(f.author_unknown) AS unknown_authors,
            sum(f.likely_bot) AS bot_name_flags,sum(length(f.quoted_text)>0) AS bodies_with_quote_lines,
            sum(f.urls_json!='[]') AS bodies_with_urls,
            sum(r.text_state IN ('removed','deleted') AND f.clean_text!='') AS unavailable_bodies_with_clean_text,
            sum(f.char_count!=length(f.clean_text)) AS inconsistent_character_counts
            FROM records r JOIN features f USING(kind,id) GROUP BY r.kind''')
        generated['reply_quality']=export_query(db,ANALYSIS/'reply_quality.csv','''SELECT r.subreddit,
            e.parent_kind,e.depth_status,count(*) AS replies,
            sum(e.parent_present=0) AS missing_parents,
            sum(e.child_author_key IS NULL) AS unknown_child_authors,
            sum(e.parent_author_key IS NULL) AS unknown_parent_authors,
            sum(e.same_thread=0) AS cross_thread_parents,
            sum(e.reply_delay_seconds<0) AS negative_reply_delays
            FROM reply_edges e JOIN records r ON r.kind='comments' AND r.id=e.child_id
            GROUP BY r.subreddit,e.parent_kind,e.depth_status''')
        generated['thread_summary']=export_query(db,ANALYSIS/'thread_summary.csv','''SELECT subreddit,
            post_present,count(*) AS threads,sum(collected_comment_count) AS collected_comments,
            round(avg(collected_comment_count),3) AS mean_collected_comments,
            max(collected_comment_count) AS largest_collected_thread,
            round(avg(max_resolved_depth),3) AS mean_max_resolved_depth,
            max(max_resolved_depth) AS deepest_resolved_branch,
            sum(unresolved_depth_count) AS comments_with_unresolved_depth,
            sum(post_direct_layoff=1) AS direct_matching_posts,
            sum(direct_comment_count>0) AS threads_with_direct_matching_comments
            FROM threads GROUP BY subreddit,post_present''')
        distributions=defaultdict(Counter)
        for row in db.execute('''SELECT subreddit,kind,direct_layoff,score,count(*) AS frequency
            FROM records WHERE score IS NOT NULL GROUP BY subreddit,kind,direct_layoff,score'''):
            distributions[tuple(row[:3])][row[3]]=row[4]
        stats=[]
        for key,histogram in sorted(distributions.items()):
            n=sum(histogram.values())
            stats.append((*key,n,round(sum(value*count for value,count in histogram.items())/n,3),
                *(weighted_quantile(histogram,q) for q in [.5,.75,.9,.99]),min(histogram),max(histogram)))
        save_rows(ANALYSIS/'engagement_summary.csv',['subreddit','kind','direct_keyword_match','known_scores','mean_score','median_score','p75_score','p90_score','p99_score','min_score','max_score'],stats)
        generated['engagement_summary']=len(stats)
        print('Engagement, thread, and data-quality statistics complete',flush=True)
        # Only matching documents are used for exploratory lexical counts.
        flag='direct_layoff' if args.match=='direct' else 'broad_layoff'
        totals=defaultdict(Counter);documents=defaultdict(Counter);n_documents=Counter()
        for row in db.execute(f'''SELECT r.subreddit,r.kind,r.title,f.own_text
            FROM records r JOIN features f USING(kind,id) WHERE r.{flag}=1'''):
            subreddit,kind,title,body=row;group=(subreddit,kind);n_documents[group]+=1
            # Titles and bodies remain separate so a bigram cannot cross their boundary.
            # Stopwords break bigrams; they are not removed before adjacency is counted.
            frequencies=Counter()
            for text in [title or '',body or '']:
                tokens=[word.lower().replace('’',"'") for word in WORDS.findall(URL.sub(' ',text))]
                frequencies.update((1,w) for w in tokens if len(w)>=3 and w not in STOP)
                frequencies.update((2,a+' '+b) for a,b in zip(tokens,tokens[1:]) if len(a)>=2 and len(b)>=2 and a not in STOP and b not in STOP)
            totals[group].update(frequencies);documents[group].update(frequencies.keys())
        term_rows=[]
        for group in sorted(totals):
            for ngram in (1,2):
                terms=[(term,df) for (n,term),df in documents[group].items() if n==ngram and df>=args.min_documents]
                for term,df in sorted(terms,key=lambda r:(-r[1],r[0]))[:args.top_terms]:
                    term_rows.append((*group,ngram,term,df,totals[group][(ngram,term)],n_documents[group],round(100*df/n_documents[group],3)))
        save_rows(ANALYSIS/f'terms_{args.match}.csv',['subreddit','kind','ngram','term','document_count','occurrence_count','matching_documents','document_percent'],term_rows)
        generated['lexical_terms']=len(term_rows)
    manifest={'generated_utc':datetime.now(timezone.utc).isoformat(),'match':args.match,
        'top_terms_per_group_and_ngram':args.top_terms,'minimum_document_frequency':args.min_documents,
        'lexical_text':'Post title and own_text; line-prefixed quotations and URLs excluded; lowercase; no stemming; conservative function-word stoplist; negation retained.',
        'quantiles':'Linear interpolation over observed non-null scores, using exact frequency histograms.',
        'interpretation':'Keyword counts are not validated relevance. Monthly changes reflect changing collection coverage. Thread metrics describe collected comments only.',
        'output_rows':generated}
    (ANALYSIS/'analysis_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(generated,indent=2),flush=True)


if __name__=='__main__':main()
