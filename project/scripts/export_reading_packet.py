#!/usr/bin/env python3
"""Export full focus texts and bounded context for offline reading/notebooks."""
import json
from project import SAMPLE as OUT,ensure_dirs
from dataset import research_db, record, context


def export_packet(out=OUT/'employment'):
    ensure_dirs()
    sample=json.loads((out/'reading_sample.json').read_text())
    destination=out/'reading_packet.jsonl'
    with research_db() as db, destination.open('w') as output:
        for item in sample:
            focus=record(db,item['kind'],item['id'])
            # The selected sample's metadata takes precedence over legacy sample membership.
            focus.update({'sample_id':item['sample_id'],'sample_group':item['group'],'stratum':item['stratum']})
            thread=db.execute('SELECT * FROM threads WHERE thread_id=?',(focus['thread_id'],)).fetchone()
            packet={'sample':item,'record':focus,'thread':dict(thread) if thread else None,
                    'context':context(db,focus),'context_limits':{'ancestors':30,'direct_replies':40}}
            output.write(json.dumps(packet,ensure_ascii=False)+'\n')
    print(f'Reading packet: {len(sample)} records with full text and bounded context',flush=True)


if __name__=='__main__':export_packet()
