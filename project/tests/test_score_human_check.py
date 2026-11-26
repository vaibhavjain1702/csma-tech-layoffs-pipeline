import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import score_human_check as S  # noqa: E402

ORDER = S.COMMENT_LABELS + S.REPLY_LABELS


def make_reference():
    rows = []
    for li, lab in enumerate(ORDER):
        for j in range(20):
            rows.append({"unit": "comment" if li < 8 else "reply", "machine_label": lab,
                         "id": f"id{li}_{j}", "text": f"fake text {li} {j}",
                         "human_label_correct_yes_no": ""})
    return pd.DataFrame(rows)


def write_coder(directory, name, ref, lc=None, bt=None, mutate=None):
    lc, bt = lc or {}, bt or {}
    rows = []
    for i, r in ref.iterrows():
        rid = i + 1
        rows.append({"row_id": rid, "unit": r["unit"], "machine_label": r["machine_label"],
                     "label_meaning": "", "text": r["text"], "label_correct": lc.get(rid, ""),
                     "blamed_target": bt.get(rid, ""), "notes": "", "id": r["id"]})
    df = pd.DataFrame(rows)
    if mutate:
        df = mutate(df)
    p = Path(directory) / f"check_sheet_coder_{name}.csv"
    df.to_csv(p, index=False, encoding="utf-8-sig")
    return p


class KappaTests(unittest.TestCase):
    def test_perfect(self):
        k, po, _ = S.cohen_kappa(["yes", "no"] * 5, ["yes", "no"] * 5)
        self.assertAlmostEqual(k, 1.0)
        self.assertAlmostEqual(po, 1.0)

    def test_chance(self):
        k, _, _ = S.cohen_kappa(["yes", "yes", "no", "no"] * 5, ["yes", "no", "yes", "no"] * 5)
        self.assertAlmostEqual(k, 0.0, places=6)

    def test_worked_example(self):
        a = ["yes"] * 25 + ["no"] * 25
        b = ["yes"] * 20 + ["no"] * 5 + ["yes"] * 10 + ["no"] * 15
        k, po, _ = S.cohen_kappa(a, b)
        self.assertAlmostEqual(k, 0.40, places=6)
        self.assertAlmostEqual(po, 0.70, places=6)

    def test_degenerate(self):
        k, po, why = S.cohen_kappa(["yes"] * 10, ["yes"] * 10)
        self.assertIsNone(k)
        self.assertEqual(po, 1.0)
        self.assertIn("same answer", why)

    def test_empty(self):
        k, po, why = S.cohen_kappa([], [])
        self.assertIsNone(k)
        self.assertIsNone(po)
        self.assertTrue(why)


class WilsonTests(unittest.TestCase):
    def test_all(self):
        lo, hi = S.wilson(20, 20)
        self.assertAlmostEqual(lo, 0.8389, places=3)
        self.assertAlmostEqual(hi, 1.0, places=6)

    def test_none(self):
        lo, hi = S.wilson(0, 20)
        self.assertAlmostEqual(lo, 0.0, places=6)
        self.assertAlmostEqual(hi, 0.1611, places=3)

    def test_half(self):
        lo, hi = S.wilson(10, 20)
        self.assertAlmostEqual(lo, 0.2993, places=3)
        self.assertAlmostEqual(hi, 0.7007, places=3)

    def test_zero_n(self):
        self.assertEqual(S.wilson(0, 0), (None, None))


class LoadTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.d = Path(self._t.name)
        self.ref = make_reference()

    def tearDown(self):
        self._t.cleanup()

    def test_unsure_and_blank(self):
        lc = {}
        for j in range(20):  # experience block = rows 1..20
            lc[j + 1] = ["yes"] * 10 + ["no"] * 5 + ["unsure"] * 3 + [""] * 2
            lc[j + 1] = lc[j + 1][j]
        p = write_coder(self.d, "A", self.ref, lc=lc)
        df = S.load_coder_file(p, self.ref)
        rows = S.stat_row("label_correct", "coder_A", "experience",
                          [v for v, m in zip(S.effective(df, "label_correct"), df["machine_label"])
                           if m == "experience"])
        self.assertEqual(rows["n_coded"], 18)
        self.assertEqual(rows["unsure"], 3)
        self.assertEqual((rows["yes"], rows["no"]), (10, 5))
        self.assertAlmostEqual(rows["precision"], 10 / 15)

    def test_normalisation(self):
        p = write_coder(self.d, "A", self.ref, lc={1: " Y ", 2: "N"}, bt={41: "N/A", 61: "NA"})
        df = S.load_coder_file(p, self.ref)
        self.assertEqual(df["label_correct"][:2].tolist(), ["yes", "no"])
        self.assertEqual(df["blamed_target"][40], "na")

    def test_239_rows(self):
        p = write_coder(self.d, "A", self.ref, mutate=lambda d: d.iloc[:239])
        with self.assertRaises(ValueError):
            S.load_coder_file(p, self.ref)

    def test_duplicate_row_id(self):
        def mut(d):
            d.loc[5, "row_id"] = 1
            return d
        p = write_coder(self.d, "A", self.ref, mutate=mut)
        with self.assertRaises(ValueError):
            S.load_coder_file(p, self.ref)

    def test_bad_value(self):
        p = write_coder(self.d, "A", self.ref, lc={7: "maybe"})
        with self.assertRaises(ValueError) as cm:
            S.load_coder_file(p, self.ref)
        msg = str(cm.exception)
        self.assertIn("row_id 7", msg)
        self.assertIn("maybe", msg)
        self.assertIn("label_correct", msg)

    def test_id_mismatch(self):
        def mut(d):
            d.loc[3, "id"] = "WRONG"
            return d
        p = write_coder(self.d, "A", self.ref, mutate=mut)
        with self.assertRaises(ValueError) as cm:
            S.load_coder_file(p, self.ref)
        self.assertIn("row_id 4", str(cm.exception))

    def test_missing_column(self):
        p = write_coder(self.d, "A", self.ref, mutate=lambda d: d.drop(columns=["label_correct"]))
        with self.assertRaises(ValueError):
            S.load_coder_file(p, self.ref)


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.root = Path(self._t.name)
        self.d = self.root / "coders"
        self.d.mkdir()
        self.ref = make_reference()
        self.ref_path = self.root / "check_sheet.csv"
        self.ref.to_csv(self.ref_path, index=False, encoding="utf-8")
        self.out = self.root / "out"

    def tearDown(self):
        self._t.cleanup()

    def run_main(self):
        return S.main(["--dir", str(self.d), "--out", str(self.out),
                       "--reference", str(self.ref_path)])

    def test_full_run(self):
        a = {i: ("yes" if i % 3 else "no") for i in range(1, 241)}
        b = dict(a)
        b[2] = "no" if a[2] == "yes" else "yes"
        b[3] = "unsure"
        bt = {i: "yes" for i in range(41, 121)}
        write_coder(self.d, "A", self.ref, lc=a, bt=bt)
        write_coder(self.d, "B", self.ref, lc=b, bt=bt)
        write_coder(self.d, "C", self.ref)
        (self.d / "~$check_sheet_coder_Z.xlsx").write_bytes(b"lock")
        pd.DataFrame({"row_id": [2], "final_label_correct": ["yes"]}).to_csv(
            self.d / "adjudicated.csv", index=False)
        self.assertEqual(self.run_main(), 0)
        for f in ("precision_by_label.csv", "agreement_by_label.csv", "disagreements.csv",
                  "SUMMARY.md"):
            self.assertTrue((self.out / f).is_file(), f)
        prec = pd.read_csv(self.out / "precision_by_label.csv")
        self.assertEqual(set(prec["source"]) >= {"coder_A", "coder_B", "consensus", "final"}, True)
        self.assertNotIn("coder_C", set(prec["source"]))
        dis = pd.read_csv(self.out / "disagreements.csv")
        self.assertNotIn("text", dis.columns)
        self.assertEqual(dis.loc[dis.row_id == 2, "adjudicated"].iloc[0], "yes")
        self.assertIn("Cohen", (self.out / "SUMMARY.md").read_text(encoding="utf-8"))

    def test_nothing_coded(self):
        write_coder(self.d, "A", self.ref)
        self.assertEqual(self.run_main(), 0)
        self.assertFalse(self.out.exists())

    def test_validation_error(self):
        write_coder(self.d, "A", self.ref, lc={1: "maybe"})
        self.assertEqual(self.run_main(), 2)
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
