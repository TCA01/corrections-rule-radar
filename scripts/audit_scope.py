"""Report-only live scope audit. Never sync, save snapshots, or publish.

Reuse the official identity resolver with its two write boundaries redirected
to audit evidence. Production fingerprints include contents and modification times.
"""
import json
import hashlib
import sys
from pathlib import Path
from functools import partial
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import LawClient, ApiError
from pipeline.operations import now
from pipeline.operations.metrics import Metrics
from pipeline.snapshot import write_json
from pipeline.registry import identifiers, unwrap, detail_url
from pipeline.normalize import snapshot
from scripts import collect

OUT = Path('data/reports/phase1c_evidence')
KEYWORDS = '교정 교정시설 교정직 교도관 교도소 구치소 수용자 수형자 교도작업 가석방 교정교육 사회복귀 중독재활 보관금품'.split() + ['수용자 의료', '수용자 급식', '국가공무원 복무', '국가공무원 인사운영처리지침', '인사운영처리', '공무원 인사운영']

def fingerprint():
    values = {}
    for directory in ('data/registry', 'data/seed', 'data/snapshots', 'public/api/v1', 'schemas', 'web/src'):
        for path in sorted(Path(directory).rglob('*')):
            if path.is_file():
                values[str(path)] = [hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns]
    return values

def protected_changes(before, after):
    return [p for p in set(before)|set(after) if not p.startswith('web') and before.get(p)!=after.get(p)]

def redirect(path, value):
    write_json(OUT / Path(path).name, value)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before = fingerprint(); write_json(OUT/'production_before.json', before)
    metrics = Metrics()
    client = LawClient(cache='data/raw_cache/phase1c', metrics=metrics)
    # Resolver's persistence seams are overridden only in this standalone process.
    collect.write_json = redirect
    collect.save_snapshot = lambda value: None
    collect.LawClient = lambda **kwargs: client
    print('OFFICIAL_IDENTITY_AUDIT_STARTED', flush=True)
    collection = collect.run(metrics=metrics, quiet=True)
    print('OFFICIAL_IDENTITY_AUDIT_COMPLETE', flush=True)
    searches=[]; found={}; errors=[]
    queries=[('MINISTRY_CURRENT', {'org':'1270000','nw':1})]
    queries += [(word, {'query':word,'nw':1}) for word in KEYWORDS]
    for label, params in queries:
        try:
            items, evidence = collect.search(client, 'admrul', **params)
            searches.append({'query':label,'parameters':params,'count':len(items),'items':items,'evidence':evidence})
            for item in items:
                stable, serial = identifiers(item, 'admrul')
                found[stable] = item
            print('SEARCH_COMPLETE '+label+' '+str(len(items)), flush=True)
        except (ApiError, ValueError) as exc:
            errors.append({'stage':'search','query':label,'error':str(exc)})
        write_json(OUT/'searches.json', searches)
    current={row['canonical_id'] for row in collection['registry']}
    bodies={}
    for stable, item in found.items():
        if 'admrul-'+stable in current: continue
        title=item.get('행정규칙명','')
        # Inspect every uncovered rule in correction keyword results, and broad
        # personnel/duty/discipline/ethics/organization rules in the MoJ census.
        in_keyword=any(s['query']!='MINISTRY_CURRENT' and any(str(i.get('행정규칙ID'))==stable for i in s['items']) for s in searches)
        broad=any(w in title for w in ('공무원','인사','징계','복무','직제','윤리','교정','수용','교도','가석방','재활'))
        if not (in_keyword or broad): continue
        _, serial=identifiers(item,'admrul')
        try:
            payload, ev=client.fetch('lawService.do',target='admrul',ID=serial)
            record={'list_item':item,'evidence':ev,'official_url':detail_url('admrul',serial),'payload':payload}
            try: record['snapshot']=snapshot(payload,'admrul',serial,ev)
            except ValueError as exc: record['body_review_reason']=str(exc)
            bodies['admrul-'+stable]=record
        except (ApiError,ValueError) as exc: errors.append({'stage':'body','canonical_id':'admrul-'+stable,'error':str(exc)})
        write_json(OUT/'candidate_bodies.json', bodies)
    maps=[]
    for stable in ('001668','010878','002027'):
        try:
            payload,ev=client.fetch('lawService.do',target='lsStmd',ID=stable)
            maps.append({'canonical_id':'law-'+stable,'payload':payload,'evidence':ev})
        except (ApiError,ValueError) as exc: errors.append({'stage':'system_map','canonical_id':'law-'+stable,'error':str(exc)})
    write_json(OUT/'system_maps.json', maps)
    after=fingerprint()
    write_json(OUT/'integrity.json', {'finished_at':now(),'production_unchanged':not protected_changes(before,after),'all_observed_files_unchanged':before==after,'changed_paths':[p for p in set(before)|set(after) if before.get(p)!=after.get(p)],'protected_changed_paths':protected_changes(before,after),'metrics':metrics.report(),'errors':errors,'official_resolved':len(collection['registry']),'candidate_bodies':len(bodies)})
    print('AUDIT_COLLECTION_COMPLETE', flush=True)
    if protected_changes(before,after): raise ValueError('PRODUCTION_CHANGED')

if __name__=='__main__':
    main()
