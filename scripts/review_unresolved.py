import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import LawClient,ApiError
from pipeline.snapshot import write_json
from scripts.collect import search

def main():
    c=LawClient(); result={}
    for query in ('교정기관 간판','교정공무원 예절'):
        result[query]={}
        for nw in (1,2):
            try:
                items,ev=search(c,'admrul',query=query.replace(' ',''),nw=nw)
                result[query][str(nw)]={'items':items,'evidence':ev}
                print(json.dumps({'query':query,'nw':nw,'items':items},ensure_ascii=False),flush=True)
            except (ApiError,ValueError) as e: print('REVIEW_QUERY_FAILED')
    write_json('data/reports/unresolved_evidence.json',result)

if __name__=='__main__': main()
