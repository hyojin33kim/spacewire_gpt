import unittest

from tools.semantic_lint import ID_PATTERNS


class TestSemanticLintDecisionRegex(unittest.TestCase):
    def test_project_local_prefixed_decision_ids_are_not_misread(self):
        pat = ID_PATTERNS["decision"]
        self.assertEqual(pat.findall("NR-DEC-01"), [])
        self.assertEqual(pat.findall("NR-DEC-02"), [])
        self.assertEqual(pat.findall("NR-DEC-03"), [])

    def test_canonical_decision_ids_are_still_detected(self):
        pat = ID_PATTERNS["decision"]
        self.assertEqual(pat.findall("DEC-ENC-001"), ["DEC-ENC-001"])
        self.assertEqual(pat.findall("DEC-DL-003"), ["DEC-DL-003"])
        self.assertEqual(pat.findall("(DEC-RTL-005)"), ["DEC-RTL-005"])


if __name__ == "__main__":
    unittest.main()
