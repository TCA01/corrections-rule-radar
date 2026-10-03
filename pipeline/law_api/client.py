"""Small sequential HTTPS client; exceptions never retain request URLs or secrets."""
import hashlib
import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


class ApiError(Exception):
    def __init__(self, code, status=None):
        self.code, self.status = code, status
        super().__init__(code + (f" HTTP {status}" if status else ""))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ApiError("REDIRECT_REJECTED", code)


def xml_object(node):
    if not list(node):
        return node.text or ""
    result = {}
    for child in node:
        value = xml_object(child)
        if child.tag in result:
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(value)
        else:
            result[child.tag] = value
    return result


def parse_payload(raw, kind):
    if not raw.strip():
        raise ApiError("EMPTY_RESPONSE")
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = raw.decode("cp949")
    try:
        if kind == "JSON":
            obj = json.loads(decoded)
        else:
            root = ET.fromstring(decoded)
            obj = {root.tag: xml_object(root)}
    except (ValueError, ET.ParseError):
        if any(s in decoded for s in ("사용자 인증", "인증값이", "인증키가", "등록되지 않은", "승인되지", "사용자 정보가")):
            raise ApiError("AUTHENTICATION_ERROR") from None
        raise ApiError("MALFORMED_" + kind) from None
    if not isinstance(obj, dict) or not obj:
        raise ApiError("INVALID_PAYLOAD")
    if any(k.lower() in ("error", "errormessage", "errorcode") for k in obj):
        raise ApiError("API_ERROR_PAYLOAD")
    for root in obj.values():
        if isinstance(root,dict) and root.get('resultCode','00')!='00':
            message=str(root.get('resultMsg',''))
            raise ApiError('AUTHENTICATION_ERROR' if any(s in message for s in ('인증','사용자','권한','등록')) else 'API_RESULT_ERROR')
    return obj


class LawClient:
    def __init__(self, *, timeout=30, interval=1.1, retries=2, cache="data/raw_cache", opener=None, metrics=None):
        self._oc = os.environ.get("LAW_API_OC", "").strip()
        if not self._oc:
            raise ApiError("WAITING_FOR_LAW_API_OC")
        self.timeout, self.interval, self.retries = timeout, interval, retries
        self.cache = Path(cache)
        self.opener = opener or urllib.request.build_opener(NoRedirect())
        self._last = 0.0
        self.metrics = metrics

    def __repr__(self):
        return "LawClient(credential=REDACTED)"

    def _request(self, endpoint, params):
        wait = self.interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        url = "https://www.law.go.kr/DRF/" + endpoint + "?" + urllib.parse.urlencode({**params, "OC": self._oc})
        req = urllib.request.Request(url, headers={"User-Agent": "CorrectionsRuleRadar/0.0.1 (official-api-feasibility)", "Accept": "application/json, application/xml"})
        error = None
        for attempt in range(self.retries + 1):
            if attempt and self.metrics: self.metrics.retry_count+=1
            self._last = time.monotonic()
            attempt_started=self._last; error_code=None
            try:
                with self.opener.open(req, timeout=self.timeout) as response:
                    raw = response.read(30_000_000)
                return raw
            except urllib.error.HTTPError as exc:
                error = ApiError("AUTHENTICATION_ERROR" if exc.code in (401, 403) else "HTTP_ERROR", exc.code)
                error_code=error.code
                if exc.code not in (429, 500, 502, 503, 504):
                    break
            except (socket.timeout, TimeoutError):
                error = ApiError("TIMEOUT")
                error_code=error.code
            except urllib.error.URLError:
                error = ApiError("NETWORK_ERROR")
                error_code=error.code
            finally:
                if self.metrics: self.metrics.record('api',time.monotonic()-attempt_started,error_code)
            if attempt < self.retries:
                time.sleep(2 ** attempt)
        raise error from None

    def fetch(self, endpoint="lawSearch.do", **params):
        if endpoint not in ("lawSearch.do", "lawService.do") or "OC" in params:
            raise ApiError("INVALID_REQUEST")
        last = None
        for kind in ("JSON", "XML"):
            request = {**params, "type": kind}
            raw = self._request(endpoint, request)
            raw_hash = hashlib.sha256(raw).hexdigest()
            # Official detail links echo OC. Security takes precedence over
            # byte-exact evidence storage; redact ONLY credential occurrences.
            tokens={self._oc,urllib.parse.quote(self._oc,safe=''),urllib.parse.quote_plus(self._oc)}
            redacted = any(t.encode() in raw for t in tokens)
            for token in sorted(tokens,key=len,reverse=True):
                raw = raw.replace(token.encode(), b"REDACTED")
            try:
                result = parse_payload(raw, kind)
            except ApiError as exc:
                last = exc
                if exc.code.startswith("MALFORMED_"):
                    continue
                raise
            key = hashlib.sha256(json.dumps({'endpoint':endpoint,'params':request,'stored_sha256':hashlib.sha256(raw).hexdigest()}, sort_keys=True).encode()).hexdigest()
            self.cache.mkdir(parents=True, exist_ok=True)
            (self.cache / (key + "." + kind.lower())).write_bytes(raw)
            return result, {"request": request, "raw_sha256": raw_hash, "credential_redacted": redacted, "stored_sha256": hashlib.sha256(raw).hexdigest(), "cache_key": key}
        raise last
