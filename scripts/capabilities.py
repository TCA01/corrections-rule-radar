"""Live feasibility probes. Structured success != semantic capability success."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import LawClient,ApiError
from pipeline.registry import unwrap,as_list,normalized_title,identifiers
from pipeline.normalize import snapshot
from pipeline.snapshot import write_json,save_snapshot
from scripts.collect import search

def walk(value):
    if isinstance(value,dict):
        yield value
        for v in value.values(): yield from walk(v)
    elif isinstance(value,list):
        for v in value: yield from walk(v)

def run():
    c=LawClient(); reports={}; payloads={}
    probes=[
        ('LAW_OLD_NEW','lawService.do',{'target':'oldAndNew','ID':'001668'}),
        ('ADMIN_OLD_NEW','lawService.do',{'target':'admrulOldAndNew','LID':'36282'}),
        ('LAW_CHANGE_HISTORY','lawSearch.do',{'target':'lsHstInf','regDt':'20260929','org':'1270000','display':100}),
        ('ARTICLE_HISTORY','lawService.do',{'target':'lsJoHstInf','ID':'001668','JO':'000100','display':100}),
        ('ARTICLE_DAY_HISTORY','lawSearch.do',{'target':'lsJoHstInf','ID':'001668','fromRegDt':'20260101','toRegDt':'20261003'}),
        ('LAW_APPENDICES','lawSearch.do',{'target':'licbyl','search':2,'query':'형의 집행 및 수용자의 처우에 관한 법률 시행규칙','display':100}),
        ('ADMIN_APPENDICES','lawSearch.do',{'target':'admbyl','search':2,'query':'교도작업운영지침','display':100}),
        ('DELETION_HISTORY','lawSearch.do',{'target':'delHst','knd':2,'frmDt':'20260101','toDt':'20261003','display':100}),
        ('SYSTEM_MAP','lawService.do',{'target':'lsStmd','ID':'001668'}),
    ]
    for name,endpoint,params in probes:
        try:
            if name=='LAW_CHANGE_HISTORY':
                items,evs=search(c,'lsHstInf',regDt=params['regDt'],org=params['org'])
                obj={'LawHistory':{'law':items,'totalCnt':len(items)}}; ev={'pages':evs}
            else:
                obj,ev=c.fetch(endpoint,**params)
            root=unwrap(obj); payloads[name]=obj
            nodes=list(walk(root)); fields={k for n in nodes for k in n}
            if name.endswith('OLD_NEW'):
                passed={'구조문_기본정보','신조문_기본정보','구조문목록','신조문목록'}<=fields and not any(n.get('신구법존재여부')=='N' for n in nodes)
            elif name=='SYSTEM_MAP': passed='상하위법' in fields and '기본정보' in fields
            elif name=='ARTICLE_HISTORY': passed='조문변경일' in fields or '조문변경이력' in fields or ('조문번호' in fields and len(nodes)>3)
            elif name=='ARTICLE_DAY_HISTORY': passed='조문정보' in fields
            elif name=='LAW_CHANGE_HISTORY': passed=any(n.get('법령ID')=='001668' for n in nodes)
            elif name=='LAW_APPENDICES': passed='별표일련번호' in fields and any(n.get('관련법령ID')=='010883' for n in nodes)
            elif name=='ADMIN_APPENDICES': passed='별표일련번호' in fields and any(n.get('관련행정규칙명')=='교도작업운영지침' for n in nodes)
            else: passed='삭제일자' in fields and '일련번호' in fields
            reports[name]={'status':'PASS' if passed else 'FAIL','reason':None if passed else 'SEMANTIC_PROOF_INCOMPLETE','root_fields':list(root),'response_fields':sorted(fields),'evidence':ev,'request_endpoint':endpoint}
        except (ApiError,ValueError) as e:
            reports[name]={'status':'FAIL','reason':e.code if isinstance(e,ApiError) else str(e),'http_status':getattr(e,'status',None),'request':params,'request_endpoint':endpoint}
        print(name,reports[name]['status'],reports[name].get('reason'),flush=True)
        write_json('data/reports/capabilities.json',reports)
    # Real-world cases, plus real historical bodies for replay.
    histories={}; fixtures=Path('tests/fixtures'); fixtures.mkdir(parents=True,exist_ok=True)
    for title in ('교도작업운영지침','교도작업특별회계운영지침','가석방 업무지침'):
        try:
            items,evs=search(c,'admrul',query=title,nw=2)
            items=[i for i in items if normalized_title(i.get('행정규칙명',''))==normalized_title(title)]
            histories[title]={'versions':items,'evidence':evs}
            if title=='교도작업운영지침' and items:
                current_obj,current_ev=c.fetch('lawService.do',target='admrul',LID=identifiers(items[0],'admrul')[0])
                current_serial=unwrap(current_obj)['행정규칙기본정보']['행정규칙일련번호']
                historical=[i for i in items if identifiers(i,'admrul')[1]!=current_serial]
                _,serial=identifiers(sorted(historical,key=lambda i:i['발령일자'],reverse=True)[0],'admrul')
                po,pe=c.fetch('lawService.do',target='admrul',ID=serial)
                old=snapshot(po,'admrul',serial,pe); save_snapshot(old)
                no,ne=c.fetch('lawService.do',target='admrul',LID=old['stable_identifier'])
                ns=unwrap(no)['행정규칙기본정보']['행정규칙일련번호']; new=snapshot(no,'admrul',ns,ne)
                write_json(fixtures/'admin_old.json',po); write_json(fixtures/'admin_new.json',no)
                write_json(fixtures/'replay_provenance.json',{'admin_old':pe,'admin_new':ne})
        except (ApiError,ValueError,KeyError) as e:
            histories[title]={'status':'REVIEW','reason':e.code if isinstance(e,ApiError) else 'HISTORY_SCHEMA_OR_NO_RESULT'}
    write_json('data/reports/known_cases.json',histories)
    write_json('data/staging/capability_payloads.json',payloads)
    print('CAPABILITIES_COMPLETE',flush=True)

if __name__=='__main__':
    try: run()
    except ApiError as e: print(e.code); sys.exit(1)
    except Exception: print('CAPABILITIES_ABORTED'); sys.exit(1)
