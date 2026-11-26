"""Project paths and shared output helpers for the command-line pipeline."""
import csv
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'raw'
PROCESSED=ROOT/'data'/'processed'
DB_PATH=PROCESSED/'reddit.sqlite'
OUTPUTS=ROOT/'outputs'
PROFILE=OUTPUTS/'01_profile'
PREPROCESS=OUTPUTS/'02_preprocessing'
TABLES=OUTPUTS/'03_tables'
ANALYSIS=OUTPUTS/'04_analysis'
SAMPLE=OUTPUTS/'05_sample'
GEPHI_ROOT=ROOT/'gephi'
GEPHI=GEPHI_ROOT/'exports'
ANNOTATIONS=ROOT/'annotations'
CACHE=ROOT/'.cache'


def ensure_dirs():
    for path in (PROCESSED,PROFILE,PREPROCESS,TABLES,ANALYSIS,SAMPLE,GEPHI,ANNOTATIONS):
        path.mkdir(parents=True,exist_ok=True)


@contextmanager
def research_db():
    db=sqlite3.connect(f'file:{DB_PATH}?mode=ro',uri=True,timeout=30)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA cache_size=-16384')
    try:
        yield db
    finally:
        db.close()


def export_query(db,path,query,parameters=()):
    cursor=db.execute(query,parameters)
    count=0
    with path.open('w',encoding='utf-8',newline='') as output:
        writer=csv.writer(output)
        writer.writerow([field[0] for field in cursor.description])
        for row in cursor:writer.writerow(row);count+=1
    return count
