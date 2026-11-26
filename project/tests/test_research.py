"""Meaningful boundary checks for text preservation and graph reconstruction."""
import sys
import unittest
import tempfile
import csv
import sqlite3
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gephi'/'scripts'))
from research_common import author_key,domain_of,prepare_text,thread_depths
from preliminary_analysis import weighted_quantile
from export_gephi import author_graph,validate_files
from summarize_annotations import summarize
from disruption_rules import screen,FACETS
from screen_disruption import build_screen


class DisruptionScreenTests(unittest.TestCase):
    def test_general_ai_and_programming_redundancy_are_not_sufficient(self):
        self.assertEqual(screen('AI image generation','Redundancy makes our storage robust.'),{})
        self.assertIn('ai_work_change',screen('AI and developer hiring',''))

    def test_anchors_do_not_cross_field_boundaries(self):
        self.assertNotIn('ai_work_change',screen('AI image generation','I am searching for a job.'))
        result=screen('','AI will not replace developer jobs.')
        self.assertIn('ai_work_change',result)  # Denial is still retrieved, not labelled endorsement.
        self.assertEqual(result['ai_work_change'][0]['field'],'own_text')

    def test_quoted_and_url_only_terms_do_not_trigger_screen(self):
        prepared=prepare_text('> AI eliminates developer jobs.\nMy day was fine. https://example.org/layoffs')
        self.assertEqual(screen('',prepared['own_text']),{})
        self.assertIn('layoffs',screen('Layoffs announced',''))

    def test_sparse_build_retains_ids_and_reuse_and_rolls_back_incomplete_build(self):
        db=sqlite3.connect(':memory:')
        db.execute('CREATE TABLE records(kind TEXT,id TEXT,title TEXT)')
        db.execute('CREATE TABLE features(kind TEXT,id TEXT,own_text TEXT)')
        db.executemany('INSERT INTO records VALUES (?,?,?)',[('posts','a','Layoffs announced'),('comments','a',None),('comments','b',None)])
        db.executemany('INSERT INTO features VALUES (?,?,?)',[('posts','a',''),('comments','a','AI affects developer jobs.'),('comments','b','Lovely picture.')])
        db.commit();build_screen(db)
        self.assertEqual(db.execute('SELECT kind,id FROM disruption_screen ORDER BY kind').fetchall(),[('comments','a'),('posts','a')])
        self.assertEqual(db.execute('SELECT records_scanned FROM screening_builds').fetchone()[0],3)
        build_screen(db)  # Reuses identical complete rules.
        db.execute("DELETE FROM features WHERE id='b'");db.commit()
        with self.assertRaises(ValueError):
            with db:build_screen(db,rebuild=True)
        self.assertEqual(db.execute('SELECT count(*) FROM disruption_screen').fetchone()[0],2)
        db.close()


class PreparationTests(unittest.TestCase):
    def test_negation_and_quote_attribution_are_preserved(self):
        text='I am NOT okay &amp; I cannot sleep. 😔\n> It is your fault.\nNo, it is not. https://example.org/a.'
        result=prepare_text(text)
        self.assertIn('NOT okay & I cannot sleep. 😔',result['own_text'])
        self.assertNotIn('your fault',result['own_text'])
        self.assertEqual(result['quoted_text'],'It is your fault.')
        self.assertEqual(result['urls'],['https://example.org/a'])
        self.assertIn('your fault',result['clean_text'])

    def test_removed_content_does_not_become_a_document(self):
        self.assertEqual(prepare_text('[removed]',False)['word_count'],0)
        self.assertEqual(prepare_text('[removed]',False)['clean_text'],'')

    def test_unknown_authors_never_merge_into_a_shared_person(self):
        self.assertIsNone(author_key('[deleted]'))
        self.assertIsNone(author_key(None))
        self.assertEqual(author_key('ExampleReader'),author_key('examplereader'))
        self.assertNotEqual(author_key('ReaderA'),author_key('ReaderB'))
        self.assertEqual(domain_of('https://example.org/a'),'example.org')


class ConversationTests(unittest.TestCase):
    def test_structural_depth_does_not_require_submission_content(self):
        comments=[{'id':'a','parent_id':'t3_missing'},{'id':'b','parent_id':'t1_a'},{'id':'c','parent_id':'t1_b'}]
        self.assertEqual(thread_depths(comments,'t3_missing'),{'a':(1,'resolved'),'b':(2,'resolved'),'c':(3,'resolved')})

    def test_missing_intermediate_parent_does_not_invent_depth(self):
        comments=[{'id':'a','parent_id':'t1_absent'},{'id':'b','parent_id':'t1_a'}]
        self.assertEqual(thread_depths(comments,'t3_root'),{'a':(None,'missing_parent'),'b':(None,'missing_parent')})

    def test_cycle_and_invalid_parent_are_bounded(self):
        comments=[{'id':'a','parent_id':'t1_b'},{'id':'b','parent_id':'t1_a'},{'id':'c','parent_id':'nonsense'}]
        result=thread_depths(comments,'t3_root')
        self.assertEqual(result['a'],(None,'cycle'))
        self.assertEqual(result['b'],(None,'cycle'))
        self.assertEqual(result['c'],(None,'invalid_parent'))

    def test_long_chain_avoids_python_recursion_limit(self):
        comments=[{'id':str(i),'parent_id':'t3_root' if i==0 else 't1_'+str(i-1)} for i in range(1500)]
        self.assertEqual(thread_depths(comments,'t3_root')['1499'],(1500,'resolved'))


class AnalysisTests(unittest.TestCase):
    def test_frequency_quantiles_interpolate_without_expanding_records(self):
        self.assertEqual(weighted_quantile({0:2,10:2},.5),5)
        self.assertEqual(weighted_quantile({0:2,10:2},.9),10)
        self.assertEqual(weighted_quantile({7:1},.99),7)
        self.assertIsNone(weighted_quantile({},.5))

    def test_codes_count_once_per_record_and_blanks_stay_unreviewed(self):
        progress,labels=summarize([{'kind':'comments','id':'a','relevance':'relevant','themes':'Fear; fear; Advice'},
            {'kind':'comments','id':'b','relevance':'','themes':''}])
        self.assertEqual(progress[('','','unreviewed')],1)
        self.assertEqual(labels[('themes','fear','','')],1)
        self.assertEqual(labels[('themes','advice','','')],1)

    def test_new_dimensions_stay_separate_from_themes(self):
        _,labels=summarize([{'kind':'comments','id':'a','experiences':'Job search',
            'explanations':'AI; ai','future_expectations':'Uncertain','themes':''}])
        self.assertEqual(labels[('experiences','job search','','')],1)
        self.assertEqual(labels[('explanations','ai','','')],1)
        self.assertEqual(labels[('future_expectations','uncertain','','')],1)
        self.assertFalse(any(key[0]=='themes' for key in labels))

    def test_author_graph_preserves_direction_weight_and_exclusions(self):
        db=sqlite3.connect(':memory:')
        db.execute('''CREATE TABLE selected_edges(child_author_key TEXT,parent_author_key TEXT,
            parent_present INTEGER,same_thread INTEGER,thread_id TEXT,created_utc INTEGER)''')
        db.executemany('INSERT INTO selected_edges VALUES (?,?,?,?,?,?)',[
            ('u_A','u_B',1,1,'t3_one',100),('u_A','u_B',1,1,'t3_two',110),
            ('u_B','u_A',1,1,'t3_one',120),('u_A','u_A',1,1,'t3_one',130),
            ('u_A',None,0,None,'t3_missing',140)])
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary);manifest=author_graph(db,path,1)
            self.assertEqual(manifest['nodes'],2);self.assertEqual(manifest['edges'],2)
            self.assertEqual(manifest['total_retained_replies'],3)
            with (path/'edges.csv').open(newline='') as f:edges=list(csv.DictReader(f))
            weights={(r['Source'],r['Target']):int(r['Weight']) for r in edges}
            self.assertEqual(weights,{('u_A','u_B'):2,('u_B','u_A'):1})
            self.assertEqual(validate_files(path)['dangling_endpoints'],0)
        db.close()


if __name__=='__main__':unittest.main()
