"""Print only approved response fields. Never print raw errors or credential."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import LawClient, ApiError

def main():
    client = LawClient()
    for target, query in (("law", "형의 집행 및 수용자의 처우에 관한 법률"), ("admrul", "교도작업운영지침")):
        try:
            result, evidence = client.fetch(target=target, query=query, display=10)
            # Client rejects any credential echo; preview contains no authenticated URL.
            print(json.dumps({"target": target, "response": result}, ensure_ascii=False)[:18000])
        except ApiError as exc:
            print(json.dumps({"target": target, "error": exc.code, "status": exc.status}))
        except Exception:
            print(json.dumps({"target": target, "error": "INTERNAL_ERROR"}))

if __name__ == "__main__":
    main()
