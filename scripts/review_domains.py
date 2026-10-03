"""Explicit evidence-reviewed relevance mappings; never legal instructions."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json

# Manual relevance review against the official evidence artifact, keyed by stable
# identity. These are classifications, not resolver exceptions or legal findings.
MAPPINGS={
 'admrul-2046965':('분류·가석방',['수용·보안']),
 'admrul-26424':('인사·조직',[]),
 'admrul-26465':('의료',[]),
 'admrul-26678':('기타',[]),
 'admrul-26917':('인사·조직',[]),
 'admrul-28315':('정보화',[]),
 'admrul-28558':('인사·조직',['급식·복지']),
 'admrul-28644':('인권·청원',[]),
 'admrul-28645':('인권·청원',[]),
 'admrul-28712':('기타',[]),
 'admrul-28718':('급식·복지',[]),
 'admrul-28763':('인사·조직',['수용·보안']),
 'admrul-32482':('급식·복지',[]),
 'admrul-32484':(None,[]),
 'admrul-32485':('인사·조직',['작업·직업훈련']),
 'admrul-32486':('기타',[]),
 'admrul-32495':('급식·복지',['보관금품']),
 'admrul-34791':('작업·직업훈련',['교육·교화']),
 'admrul-35334':('분류·가석방',[]),
 'admrul-36282':('작업·직업훈련',[]),
 'admrul-36283':('작업·직업훈련',[]),
 'admrul-37037':('의료',[]),
 'admrul-37383':('분류·가석방',['수용·보안']),
 'admrul-37401':('분류·가석방',[]),
 'admrul-37575':('기타',[]),
 'admrul-37576':('급식·복지',[]),
 'admrul-37579':('인사·조직',[]),
 'admrul-37580':('수용·보안',['인권·청원','인사·조직']),
 'admrul-37581':('인사·조직',[]),
 'admrul-37583':('작업·직업훈련',[]),
 'admrul-37584':('교육·교화',[]),
 'admrul-37585':('교육·교화',['작업·직업훈련','급식·복지','의료']),
 'admrul-37586':('교육·교화',['접견·외부교통']),
 'admrul-37587':('급식·복지',['인사·조직']),
 'admrul-37588':('급식·복지',['인사·조직']),
 'admrul-37589':('급식·복지',[]),
 'admrul-37590':('보관금품',[]),
 'admrul-37730':('급식·복지',['인사·조직']),
 'admrul-37922':('민영교도소',[]),
 'admrul-38225':('분류·가석방',['수용·보안']),
 'admrul-39881':('인사·조직',[]),
 'admrul-40159':('수용·보안',['교육·교화']),
 'admrul-43058':('급식·복지',[]),
 'admrul-46978':('인사·조직',[]),
 'admrul-51868':(None,[]),
 'admrul-54074':('분류·가석방',[]),
 'admrul-56055':('심리치료',[]),
 'admrul-59009':('민원',[]),
 'admrul-61378':('인사·조직',[]),
 'law-001668':('수용·보안',['접견·외부교통','보관금품','분류·가석방','교육·교화','작업·직업훈련','급식·복지','의료','인권·청원']),
 'law-002027':('민영교도소',['수용·보안']),
 'law-002049':('분류·가석방',[]),
 'law-002608':('인사·조직',[]),
 'law-004057':('수용·보안',[]),
 'law-005630':('수용·보안',['접견·외부교통','보관금품','분류·가석방','교육·교화','작업·직업훈련','급식·복지','의료','인권·청원']),
 'law-006521':('인사·조직',[]),
 'law-006524':('인사·조직',['수용·보안']),
 'law-009144':('민영교도소',[]),
 'law-009163':('민영교도소',[]),
 'law-010752':('인사·조직',[]),
 'law-010878':('작업·직업훈련',[]),
 'law-010883':('수용·보안',['접견·외부교통','보관금품','분류·가석방','교육·교화','작업·직업훈련','급식·복지','의료','인권·청원','심리치료']),
 'law-011092':('작업·직업훈련',[]),
 'law-011097':('작업·직업훈련',[]),
 'law-011894':('기타',[]),
 'law-012347':('급식·복지',['인사·조직']),
 'law-012557':('급식·복지',[]),
 'law-012676':('급식·복지',[]),
}

def main():
    registry=json.loads(Path('data/registry/rules.json').read_text(encoding='utf-8'))
    evidence=json.loads(Path('data/reports/domain_evidence.json').read_text(encoding='utf-8'))
    if set(MAPPINGS)!=set(r['canonical_id'] for r in registry): raise ValueError('DOMAIN_REVIEW_COVERAGE_CHANGED')
    records=[]
    for rule in registry:
        cid=rule['canonical_id']; primary,secondary=MAPPINGS[cid]; ev=evidence[cid]
        records.append({'canonical_id':cid,'current_name':rule['current_name'],'primary_domain':primary,'secondary_domains':secondary,'review_status':'REVIEWED' if primary else 'REVIEW','classification_basis':{'method':'OFFICIAL_METADATA_AND_SCOPE_REVIEW','title':ev['current_name'],'official_department':ev['official_department'],'purpose':ev['purpose'],'supporting_articles':ev['supporting_articles'],'scope':ev['scope'],'article_headings':ev['article_headings'],'historical_scope_evidence':ev.get('historical_scope_evidence'),'official_source_url':ev['official_source_url'],'version_id':ev['version_id'],'metadata_hash':ev['metadata_hash'],'body_hash':ev['body_hash'],'reviewer':'CODEX_EVIDENCE_REVIEW','legal_interpretation':False,'rationale':'제목·공식 소관부서·목적 또는 조문 표제에 명시된 주제를 업무 검색용으로 연결함.' if primary else '보고·현황 업무는 여러 분야에 걸쳐 있어 통제 분류의 주 분야를 확정할 추가 업무담당자 검토가 필요함.'}})
    write_json('data/registry/business_domains.json',{'registry_version':'1.0','ui_label':'관련 업무 분야','review_policy':'Evidence review for information organization; not human agency approval or legal interpretation. REVIEW remains unclassified. Re-review on title/body changes.','rules':records})

if __name__=='__main__': main()
