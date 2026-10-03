"""Select actual old/new official versions, then use the production diff engine."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import LawClient,ApiError
from pipeline.registry import identifiers,unwrap
from pipeline.normalize import snapshot
from pipeline.diff import compare,future_events
from pipeline.snapshot import write_json,save_snapshot
from scripts.collect import search

def run():
    c=LawClient(); coll=json.loads(Path('data/staging/collection.json').read_text(encoding='utf-8'))
    fixtures=Path('tests/fixtures'); fixtures.mkdir(parents=True,exist_ok=True)
    current=coll['snapshots']['law-001668']
    items,evs=search(c,'eflaw',LID=current['stable_identifier'],nw=1)
    historic=[i for i in items if i.get('현행연혁코드')=='연혁' and identifiers(i,'law')[1]!=current['version_id'] and i['시행일자']<current['metadata']['effective_date'].replace('-','')]
    chosen=sorted(historic,key=lambda i:(i['시행일자'],i['공포일자']),reverse=True)[0]
    _,serial=identifiers(chosen,'law')
    po,pe=c.fetch('lawService.do',target='eflaw',MST=serial,efYd=chosen['시행일자'])
    old=snapshot(po,'law',serial,pe); save_snapshot(old)
    write_json(fixtures/'law_old_response.json',po)
    candidates={}
    for path in Path('data/snapshots').rglob('*.json'):
        s=json.loads(path.read_text(encoding='utf-8')); candidates.setdefault(s['canonical_id'],[]).append(s)
    cases={}; at='2026-10-03T00:00:00+00:00'
    cases['law']={'old':old,'new':current,'events':compare(old,current,at),'expected_type':'RULE_AMENDED'}
    for kind,expected in [('admin','RULE_AMENDED'),('rename','RULE_RENAMED'),('appendix','APPENDIX_CHANGED'),('repeal','RULE_REPEALED')]:
        if kind=='admin':
            # Explicit validation case belongs in this test harness only.
            po=json.loads((fixtures/'admin_old.json').read_text(encoding='utf-8'))
            no=json.loads((fixtures/'admin_new.json').read_text(encoding='utf-8'))
            provenance=json.loads((fixtures/'replay_provenance.json').read_text(encoding='utf-8'))
            ps=unwrap(po)['행정규칙기본정보']['행정규칙일련번호']; ns=unwrap(no)['행정규칙기본정보']['행정규칙일련번호']
            previous=snapshot(po,'admrul',ps,provenance['admin_old']); new=snapshot(no,'admrul',ns,provenance['admin_new'])
            cases[kind]={'old':previous,'new':new,'events':compare(previous,new,at),'expected_type':expected}
            continue
        found=None
        for cid,versions in sorted(candidates.items()):
            new=coll['snapshots'].get(cid)
            if not new or (kind=='admin' and new['source_kind']!='admrul'): continue
            if kind=='rename' and new['metadata']['name']!='보관금품 관리지침': continue
            for previous in versions:
                if previous['metadata']['effective_date']>new['metadata']['effective_date']: continue
                events=compare(previous,new,at,repeal_evidence=new.get('repeal_evidence'))
                if any(e['change_type']==expected for e in events):
                    found={'old':previous,'new':new,'events':events,'expected_type':expected}; break
            if found: break
        if found: cases[kind]=found
        else: cases[kind]={'status':'FAIL','reason':'NO_REAL_PAIR_PROVED'}
    futures=[s for vs in coll['future'].values() for s in vs]
    cases['future']={'old_versions':[],'new_versions':futures,'events':future_events([],futures,at),'expected_type':'FUTURE_EFFECTIVE_VERSION'}
    reports={}
    for kind,case in cases.items():
        write_json(fixtures/(kind+'_replay.json'),case)
        reports[kind]={'status':'PASS' if any(e['change_type']==case.get('expected_type') for e in case.get('events',[])) else 'FAIL','event_types':[e['change_type'] for e in case.get('events',[])],'canonical_id':case.get('new',{}).get('canonical_id'),'evidence':case.get('old',{}).get('evidence')}
    write_json('data/reports/replay.json',reports)
    print(json.dumps(reports,ensure_ascii=False),flush=True)

if __name__=='__main__':
    try: run()
    except ApiError as e: print(e.code); sys.exit(1)
    except Exception: print('REPLAY_BUILD_FAILED'); sys.exit(1)
