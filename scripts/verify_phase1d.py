"""Run audit-only tests and save a credential-free verification summary."""
import sys
import unittest
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json

def main():
    start=time.monotonic()
    suite=unittest.defaultTestLoader.discover('tests',pattern='test_phase1d.py')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    write_json('data/reports/phase1d_verification.json',{'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'duration_seconds':round(time.monotonic()-start,3),'result':'PASS' if result.wasSuccessful() else 'FAIL'})
    if not result.wasSuccessful(): sys.exit(1)

if __name__=='__main__': main()
