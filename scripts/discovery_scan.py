"""Daily official table scan; weekly full outgoing-link identity audit."""
import json
from pathlib import Path
from pipeline.corrections_seed import URLS,parse_seed
from pipeline.operations import now
from pipeline.snapshot import write_json
from scripts.collect import public_page,run as full_collect

ROOT=Path(__file__).resolve().parents[1]
def signatures(entries):
    return sorted((r['source_kind'],r['category'],r['seed_name'],r['outgoing_url'],r.get('department')) for r in entries)
def run(*,metrics=None,full_audit=False):
    previous=json.loads((ROOT/'data/seed/corrections.json').read_text(encoding='utf-8')); entries=[]; at=now()
    for kind,url in URLS.items():
        values,_=parse_seed(public_page(url,metrics),kind,at); entries+=values
    changed=signatures(entries)!=signatures(previous['entries'])
    report={'last_attempt':at,'table_changed':changed,'entry_count':len(entries),'full_identity_audit':bool(changed or full_audit)}
    write_json(ROOT/'data/reports/discovery_scan.json',report)
    # Changes are resolved by the original official evidence resolver. Membership
    # drift still requires review and blocks publication in sync(), not auto-add.
    return full_collect(metrics=metrics,quiet=True) if changed or full_audit else None
