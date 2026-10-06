"""Audit-only independent full-body comparison; never publishes legal data."""
import json, hashlib, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import LawClient
from pipeline.law_api.search import search
from pipeline.normalize import snapshot
from pipeline.registry import unwrap, as_list
from pipeline.diff.effective_states import full_articles
from pipeline.snapshot import write_json

ROOT = Path(__file__).resolve().parents[1]

def independent(body):
    # Independent traversal: no production article grouping/text normalization.
    def lines(node):
        if isinstance(node, str): return [node.strip()] if node.strip() else []
        if isinstance(node, list): return [s for n in node for s in lines(n)]
        if isinstance(node, dict):
            return [s for k in ('조문내용','항내용','호내용','목내용','내용','항','호','목') for s in lines(node.get(k))]
        return []
    result = {}
    for row in as_list(body['articles']['조문단위']):
        if row.get('조문여부') != '조문': continue
        number = str(int(row['조문번호']))
        if row.get('조문가지번호'): number += '의' + str(int(row['조문가지번호']))
        result[number] = {'key': row['조문키'], 'title': row.get('조문제목',''), 'text': '\n'.join(lines(row))}
    return result

def compare(before, after):
    left, right = independent(before['body']), independent(after['body'])
    result = []
    for n in sorted(left.keys() | right.keys(), key=lambda n: tuple(map(int,n.split('의')))):
        a,b = left.get(n),right.get(n)
        if a == b: continue
        def digest(v): return hashlib.sha256(json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',',':')).encode()).hexdigest() if v else None
        result.append({'article_number':n, 'article_key':(b or a)['key'], 'before_hash':digest(a), 'after_hash':digest(b), 'reason':'ADDED' if a is None else 'REMOVED' if b is None else 'TEXT_CHANGED' if a['text'] != b['text'] else 'STRUCTURE_CHANGED'})
    return result

def run():
    folder=ROOT/'data/staging/phase1k-audit'; folder.mkdir(parents=True, exist_ok=True)
    client=LawClient(cache=folder/'raw')
    items, evidence=search(client,'eflaw',LID='001671',nw='2,3')
    exact=[i for i in items if str(i.get('법령ID'))=='001671']
    write_json(folder/'search.json', {'items':exact,'evidence':evidence})
    states=[]
    for item in sorted(exact,key=lambda i:i['시행일자']):
        if item.get('현행연혁코드') not in ('현행','시행예정'): continue
        serial=str(item['법령일련번호']); day=item['시행일자']
        payload,ev=client.fetch('lawService.do',target='eflaw',MST=serial,efYd=day)
        state=snapshot(payload,'law',serial,ev); states.append(state)
        write_json(folder/(day+'.json'),state)
    payload,ev=client.fetch('lawService.do',target='oldAndNew',MST='288579')
    write_json(folder/'promulgation.json',{'payload':payload,'evidence':ev})
    pairs=[]
    for before,after in zip(states,states[1:]):
        changes=compare(before,after); prod=full_articles(before,after)
        pairs.append({'before_version':before['version_id'],'before_date':before['metadata']['effective_date'],'after_version':after['version_id'],'after_date':after['metadata']['effective_date'],'independent_changes':changes,'production_numbers':[a['article_number'] for a in prod], 'match': [a['article_number'] for a in changes]==[a['article_number'] for a in prod], 'cumulative':compare(states[0],after)})
    report={'states':[{'version_id':s['version_id'],'metadata':s['metadata'],'hashes':s['hashes'],'evidence':s['evidence'],'article_count':len(independent(s['body']))} for s in states], 'transitions':pairs, 'official_comparison_keys':list(unwrap(payload))}
    write_json(ROOT/'data/reports/phase1k_comparison_audit.json',report)
    print(json.dumps(report,ensure_ascii=False))

def crosscheck():
    folder=ROOT/'data/staging/phase1k-audit'
    read=lambda p:json.loads(p.read_text(encoding='utf8'))
    states=[read(folder/(d+'.json')) for d in ('20261002','20270205','20270805','20271231')]
    package=read(folder/'promulgation.json'); root=unwrap(package['payload'])
    # Audit the actual comparative table, retaining official row numbers.
    groups={}
    for side in ('구조문','신조문'):
        active=None; rows={}
        for row in as_list(root[side+'목록']['조문']):
            content=re.sub(r'<[^>]*>','',row['content']).strip()
            match=re.match(r'^제\s*(\d+)\s*조(?:의\s*(\d+))?',content)
            if match: active=match[1]+('의'+match[2] if match[2] else '')
            if active: rows.setdefault(active,[]).append({'row':row['no'],'text':content})
        groups[side]=rows
    numbers=set(groups['구조문'])|set(groups['신조문'])
    transitions=[{a['article_number'] for a in compare(x,y)} for x,y in zip(states,states[1:])]
    # Article 199-2 has institution-dependent commencement in the structured
    # addendum, while its text is already present in every returned API body.
    clause=next(a for a in states[1]['body']['addenda']['부칙단위'] if str(a['부칙공포번호'])=='21857')
    flat=[]
    def strings(v):
        if isinstance(v,str): flat.append(v)
        elif isinstance(v,list):
            for x in v: strings(x)
    strings(clause['부칙내용'])
    commencement='\n'.join(flat).split('제2조(')[0]
    rows=[]
    for n in sorted(numbers,key=lambda n:tuple(map(int,n.split('의')))):
        stage='2027-02-05' if n in transitions[0] else '2027-08-05' if n in transitions[1] else 'LATER_OR_OTHER_STAGED_DATE' if n=='199의2' else 'ALREADY_BY_2026-10-02'
        rows.append({'article_number':n,'transition':stage,'before_rows':groups['구조문'].get(n,[]),'after_rows':groups['신조문'].get(n,[]),'present_in_A':n in independent(states[0]['body'])})
    report=read(ROOT/'data/reports/phase1k_comparison_audit.json')
    report['promulgation']={'before_metadata':root['구조문_기본정보'],'after_metadata':root['신조문_기본정보'],'article_count':len(rows),'articles':rows,'commencement_clause':commencement,'evidence':package['evidence'],'count_unit':'Distinct Criminal Procedure Act article numbers in the official old/new table; excludes addendum amendments to other statutes.'}
    from collections import Counter
    report['promulgation']['distribution']=dict(Counter(r['transition'] for r in rows))
    if (folder/'package-281865.json').exists():
        package_before=read(folder/'package-281865.json'); package_after=read(folder/'package-288579.json')
        all_changes=compare(package_before,package_after)
        assert {r['article_number'] for r in all_changes}==numbers
        report['promulgation']['full_body_changes']=all_changes
        report['promulgation']['full_body_count']=len(all_changes)
        old_map=independent(package_before['body']); new_map=independent(package_after['body']); current_map=independent(states[0]['body'])
        for row in rows:
            n=row['article_number']
            row['differs_from_previous_promulgation_at_A']=current_map.get(n)!=old_map.get(n)
            row['package_text_matches_A']=current_map.get(n)==new_map.get(n)
        report['promulgation']['subsequent_amendment_note']='Article 245-12 is already present at A but paragraph 6 was further corrected by law 22009. Use actual current MST 290189, not archived MST 288579 with the same 2026-10-02 date.'
    write_json(ROOT/'data/reports/phase1k_comparison_audit.json',report)
    print(json.dumps({'count':len(rows),'distribution':report['promulgation']['distribution'],'numbers':sorted(numbers)},ensure_ascii=True))

def package_bodies():
    folder=ROOT/'data/staging/phase1k-audit'; client=LawClient(cache=folder/'raw')
    for serial in ('281865','288579'):
        payload,ev=client.fetch('lawService.do',target='law',MST=serial)
        write_json(folder/('package-'+serial+'.json'),snapshot(payload,'law',serial,ev))
    old=json.loads((folder/'package-281865.json').read_text(encoding='utf8'))
    new=json.loads((folder/'package-288579.json').read_text(encoding='utf8'))
    print(json.dumps({'old':old['metadata'],'new':new['metadata'],'changes':compare(old,new)},ensure_ascii=True))

def legal_fingerprint():
    return {p.relative_to(ROOT).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mtime_ns':p.stat().st_mtime_ns}
            for rel in ('public/api/v1','data/snapshots') for p in (ROOT/rel).rglob('*.json') if p.name!='ops-status.json'} | {
            rel:{'sha256':hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()} for rel in ('data/registry/state.json','data/registry/events.json','data/registry/change_history.json')}

def legal_check(save=False):
    path=ROOT/'data/staging/phase1k_legal_before.json'
    if save: write_json(path,legal_fingerprint()); return
    before=json.loads(path.read_text(encoding='utf8')); after=legal_fingerprint()
    report=json.loads((ROOT/'data/reports/production_sync.json').read_text(encoding='utf8'))
    report['legal_bytes_mtimes_snapshot_set_preserved']=before==after
    report['changed_legal_files']=[k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)]
    write_json(ROOT/'data/reports/phase1k_live_sync.json',report)
    print(json.dumps(report,ensure_ascii=True))

if __name__=='__main__':
    if '--crosscheck' in sys.argv: crosscheck()
    elif '--package' in sys.argv: package_bodies()
    elif '--baseline' in sys.argv: legal_check(True)
    elif '--check' in sys.argv: legal_check()
    else: run()
