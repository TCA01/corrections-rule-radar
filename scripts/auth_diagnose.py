"""Allowlisted diagnostics only: never output response text, credential or URL."""
import json
import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

def main():
    oc = os.environ.get('LAW_API_OC', '').strip()
    if not oc:
        print('WAITING_FOR_LAW_API_OC')
        return
    for target in ('law', 'admrul'):
        for kind in ('JSON', 'XML'):
            try:
                url = 'https://www.law.go.kr/DRF/lawSearch.do?' + urllib.parse.urlencode({'OC': oc, 'target': target, 'type': kind, 'query': '교도작업', 'display': 1})
                with urllib.request.urlopen(url, timeout=30) as r:
                    raw = r.read()
                    status = r.status
                    content_type = r.headers.get_content_type()
                s = raw.decode('utf-8', errors='replace')
                markers = {
                    'auth': any(t in s for t in ('인증', 'authentication', 'unauthorized')),
                    'registration': any(t in s for t in ('등록', '사용자')),
                    'login': any(t in s for t in ('로그인', 'login')),
                    'approval': any(t in s for t in ('승인', '신청')),
                    'ip': any(t in s for t in ('IP', '아이피')),
                    'html': '<html' in s.lower(),
                    'secret_echo': oc in s,
                }
                structure = 'UNSTRUCTURED'
                try:
                    obj = json.loads(s)
                    structure = 'JSON_OBJECT' if isinstance(obj, dict) else 'JSON_OTHER'
                    def paths(value, path=''):
                        if isinstance(value, dict):
                            return [p for k,v in value.items() for p in paths(v, path + '/' + str(k))]
                        if isinstance(value, list):
                            return [p for v in value for p in paths(v, path + '/item')]
                        return [path] if oc in str(value) else []
                    # Paths only; never serialize authenticated values.
                    print(json.dumps({'target': target, 'credential_echo_fields': paths(obj)}, ensure_ascii=False))
                except ValueError:
                    try:
                        root = ET.fromstring(raw)
                        structure = 'XML_' + (root.tag if root.tag in ('LawSearch', 'AdmrulSearch', 'Error', 'html') else 'OTHER')
                    except ET.ParseError:
                        pass
                print(json.dumps({'target': target, 'format': kind, 'http': status, 'content_type': content_type, 'structure': structure, 'markers': markers}))
            except Exception:
                print(json.dumps({'target': target, 'format': kind, 'error': 'REQUEST_FAILED'}))

if __name__ == '__main__':
    main()
