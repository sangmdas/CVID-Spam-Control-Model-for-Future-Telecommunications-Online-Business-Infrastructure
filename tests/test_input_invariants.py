import sys
import unittest
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from fixtures import request, setup


class InputInvariantTests(unittest.TestCase): pass

GRANT_FIELDS=("grant_id","sender","recipient","purpose","channel","audience","nonce","handle_id","direction","effect")
REQUEST_FIELDS=("transaction_id","authenticated_sender","recipient","purpose","channel","audience","grant_id","nonce","handle_id","direction","effect")

def grant_case(field):
    def test(self):
        *_,grant=setup()
        with self.assertRaisesRegex(ValueError,"non-empty"): replace(grant,**{field:"  "})
    return test

def request_case(field):
    def test(self):
        with self.assertRaisesRegex(ValueError,"non-empty"): replace(request(),**{field:""})
    return test

for field in GRANT_FIELDS: setattr(InputInvariantTests,f"test_grant_rejects_empty_{field}",grant_case(field))
for field in REQUEST_FIELDS: setattr(InputInvariantTests,f"test_request_rejects_empty_{field}",request_case(field))

if __name__=="__main__": unittest.main()
