"""Parse only published official tables, including department rowspans."""
import re
from collections import Counter
from bs4 import BeautifulSoup

URLS = {'law':'https://www.corrections.go.kr/corrections/2534/subview.do', 'admrul':'https://www.corrections.go.kr/corrections/2535/subview.do'}

def parse_seed(html, kind, crawled_at):
    soup=BeautifulSoup(html,'html.parser'); entries=[]; declared={}
    for table in soup.find_all('table'):
        caption=table.find('caption')
        if not caption or '교정본부 관련' not in caption.get_text(): continue
        heading=table.find_previous('h3').get_text(' ',strip=True)
        category=re.sub(r'\s*\(.*','',heading).strip()
        match=re.search(r'(\d+)개',heading)
        if match: declared[category]=int(match.group(1))
        department=None; remaining=0
        for row in table.select('tbody tr'):
            cells=row.find_all('td',recursive=False)
            if not cells: continue
            link=row.find('a',href=re.compile(r'law\.go\.kr'))
            if not link: continue
            if kind=='admrul':
                if remaining<=0: department=None
                if len(cells)>=3:
                    department=cells[1].get_text(' ',strip=True)
                    remaining=int(cells[1].get('rowspan',1))
                remaining-=1
            entries.append({'seed_name':cells[0].get_text(' ',strip=True),'category':category,'department':department,'corrections_source_url':URLS[kind],'outgoing_url':link['href'].replace('http:','https:',1),'source_kind':kind,'crawled_at':crawled_at})
    if not entries: raise ValueError('SEED_EMPTY')
    counts=dict(Counter(e['category'] for e in entries))
    if declared!=counts: raise ValueError('SEED_DECLARED_COUNT_MISMATCH')
    if len({e['outgoing_url'] for e in entries})!=len(entries): raise ValueError('SEED_DUPLICATE')
    return entries,counts
