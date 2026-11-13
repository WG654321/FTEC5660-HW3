import asyncio
import json
import unittest
from types import SimpleNamespace
import hw3


class Tool:
    def __init__(self, name, broken=False):
        self.name, self.broken, self.calls = name, broken, 0

    async def ainvoke(self, args):
        self.calls += 1
        if self.broken:
            raise RuntimeError('tool unavailable')
        if self.name == 'sql_query':
            return 'margin | benchmark | verdict\n15.00 | 10.00 | PASS'
        return 'Expert advice and fair treatment.'


class Model:
    def __init__(self):
        self.calls = 0

    async def ainvoke(self, messages):
        self.calls += 1
        if self.calls == 1:
            return SimpleNamespace(content='invalid JSON')
        return SimpleNamespace(content=json.dumps({p: {
            'verdict': 'PASS', 'quote': 'Expert advice', 'reason': 'Supported.'
        } for p in ('4', '7')}))


class WorkflowTests(unittest.TestCase):
    def test_retries_do_not_repeat_interviews(self):
        interview = Tool('interview')
        model = Model()
        result = asyncio.run(hw3.analyze_companies(model, {
            'sample': [Tool('sql_query'), interview]}))
        self.assertEqual(interview.calls, 2)
        self.assertEqual(model.calls, 2)
        self.assertEqual(result['sample']['points'], {4: 'PASS', 5: 'PASS', 7: 'PASS'})

    def test_failure_isolated_and_no_key_preserves_sql(self):
        result = asyncio.run(hw3.analyze_companies(None, {
            'broken': [Tool('sql_query', True)], 'healthy': [Tool('sql_query')]}))
        self.assertEqual(result['broken']['points'], {})
        self.assertEqual(result['healthy']['points'], {5: 'PASS'})

    def test_unverified_quote_rejected(self):
        content = json.dumps({p: {'verdict': 'PASS', 'quote': 'invented',
                                  'reason': 'reason'} for p in ('4', '7')})
        with self.assertRaises(ValueError):
            hw3.parse_interviews(content, {'4': 'source', '7': 'source'})

    def test_incomplete_financial_evidence_rejected(self):
        with self.assertRaises(ValueError):
            hw3.parse_margin('margin | benchmark | verdict\nNone | 10 | MISSING')


if __name__ == '__main__':
    unittest.main()
