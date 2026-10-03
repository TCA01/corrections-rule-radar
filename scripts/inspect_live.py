import json
import sys
import urllib.request
import urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import LawClient,ApiError

def main():
    c=LawClient()
    for target,kwargs in [('admrul',{'ID':'2100000285400'}),('law',{'ID':'001668'})]:
        try:
            obj,ev=c.fetch('lawService.do',target=target,**kwargs)
            print(json.dumps({'target':target,'root_keys':list(obj),'preview':str(obj)[:5500]},ensure_ascii=False))
        except ApiError as e: print(e.code)
    url='https://www.law.go.kr/'+urllib.parse.quote('행정규칙/영치금품관리지침/(1165,20170918)',safe='/(),')
    try:
        with urllib.request.urlopen(url,timeout=30) as r:
            raw=r.read()
            Path('data/raw_cache/link_example.html').write_bytes(raw)
            print('PUBLIC_LINK_FINAL',r.url)
    except Exception: print('PUBLIC_LINK_FAILED')

if __name__=='__main__': main()
