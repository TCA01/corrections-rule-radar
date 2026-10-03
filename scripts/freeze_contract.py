"""Record an explicitly reviewed candidate, or check for schema drift."""
import argparse
import hashlib
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json
from pipeline.validation import assert_schema_freeze

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--record-reviewed-candidate',action='store_true')
    args=parser.parse_args(); root=Path(__file__).resolve().parents[1]
    if args.record_reviewed_candidate:
        hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'schemas').glob('*.schema.json'))}
        write_json(root/'schemas/api_v1_candidate.lock.json',{'API_V1_CANDIDATE':True,'schema_version':'1.4','schema_sha256':hashes,'review_document':'docs/phase1f_contract.md'})
    assert_schema_freeze(); print('API_V1_CANDIDATE_FREEZE_PASS')

if __name__=='__main__': main()
