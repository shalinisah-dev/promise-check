import json, os, shutil, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import promise_lint as pl

EXAMPLE = os.path.join(os.path.dirname(HERE), "examples", "helpbot")


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.repo = os.path.join(self.d, "helpbot")
        shutil.copytree(EXAMPLE, self.repo)

    def tearDown(self):
        shutil.rmtree(self.d)

    def run_lint(self, *args):
        return pl.main([self.repo] + list(args))

    def test_clean_example_passes_strict(self):
        res = pl.lint(self.repo, os.path.join(self.repo, "promises.json"))
        self.assertEqual(len(res["promises"]), 5)
        self.assertEqual(res["drift"], [])
        self.assertEqual(res["stale"], [])
        self.assertEqual(res["unledgered"], [])
        self.assertEqual(self.run_lint("--strict"), 0)

    def test_deleted_enforcer_is_drift(self):
        os.remove(os.path.join(self.repo, "payments", "refund_gate.py"))
        res = pl.lint(self.repo, os.path.join(self.repo, "promises.json"))
        self.assertEqual([e["id"] for e in res["drift"]], ["refund-cap"])
        self.assertEqual(self.run_lint(), 1)

    def test_weakened_enforcer_is_drift(self):
        p = os.path.join(self.repo, "payments", "refund_gate.py")
        with open(p, "w") as f:
            f.write("def authorize(amount, approval_token=None):\n    return True\n")
        res = pl.lint(self.repo, os.path.join(self.repo, "promises.json"))
        self.assertIn("no longer contains", res["drift"][0]["error"])

    def test_new_promise_unledgered_fails_only_in_strict(self):
        with open(os.path.join(self.repo, "README.md"), "a") as f:
            f.write("Deleted chats are permanently erased within 30 days.\n")
        self.assertEqual(self.run_lint(), 0)
        self.assertEqual(self.run_lint("--strict"), 1)

    def test_ignore_marker_and_code_fences(self):
        with open(os.path.join(self.repo, "README.md"), "a") as f:
            f.write("We never sell data. <!-- promise-lint: ignore -->\n```\nnever = True  # always\n```\n")
        self.assertEqual(self.run_lint("--strict"), 0)

    def test_stale_entry_reported(self):
        led = os.path.join(self.repo, "promises.json")
        data = json.load(open(led))
        data["promises"].append({"id": "gone", "match": "a promise nobody makes", "rung": 1})
        json.dump(data, open(led, "w"))
        res = pl.lint(self.repo, led)
        self.assertEqual([e["id"] for e in res["stale"]], ["gone"])

    def test_rung3_without_enforcer_is_drift(self):
        led = os.path.join(self.repo, "promises.json")
        data = json.load(open(led))
        data["promises"][1]["rung"] = 3
        json.dump(data, open(led, "w"))
        res = pl.lint(self.repo, led)
        self.assertIn("names no enforced_by", res["drift"][0]["error"])

    def test_bad_ledger_exit_2(self):
        with open(os.path.join(self.repo, "promises.json"), "w") as f:
            f.write('{"promises":[{"match":"x","rung":9}]}')
        self.assertEqual(self.run_lint(), 2)

    def test_init_generates_ledger(self):
        os.remove(os.path.join(self.repo, "promises.json"))
        res = pl.lint(self.repo, os.path.join(self.repo, "promises.json"))
        led = pl.init_ledger(res)
        self.assertEqual(len(led["promises"]), 5)
        self.assertTrue(all(p["rung"] == 1 for p in led["promises"]))


if __name__ == "__main__":
    unittest.main()
