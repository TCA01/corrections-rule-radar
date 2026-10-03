import json
import re
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]
    def handle_data(self, data):
        if data.strip(): self.parts.append(data.strip())

def main():
    names = ['lsNwListGuide','lsNwInfoGuide','lsEfYdListGuide','lsEfYdInfoGuide','lsHstListGuide','lsChgListGuide','lsDayJoRvsListGuide','lsJoChgListGuide','lsStmdInfoGuide','oldAndNewInfoGuide','admrulOldAndNewInfoGuide','datDelHstGuide','admrulListGuide','admrulInfoGuide']
    source=Path('data/raw_cache/guide.html').read_text(encoding='utf-8')
    names += re.findall(r"openApiGuide\('([^']*(?:Byl|byl)[^']*)'\)",source)
    out={}
    for n in names:
        try:
            with urllib.request.urlopen('https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName='+n,timeout=30) as r: raw=r.read()
            p=Text(); p.feed(raw.decode('utf-8'))
            text='\n'.join(p.parts)
            start=text.find('요청 URL')
            out[n]=text[start:]
            Path('data/raw_cache/'+n+'.html').write_bytes(raw)
            time.sleep(.5)
        except Exception: out[n]='FETCH_FAILED'
    Path('data/raw_cache/guide_text.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    for k,v in out.items(): print(k+'\n'+v[:3200]+'\n')

if __name__=='__main__': main()
