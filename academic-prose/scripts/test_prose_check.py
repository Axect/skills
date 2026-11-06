#!/usr/bin/env python3
"""Regression tests for prose_check.py (standard library only).

Run: python3 test_prose_check.py

Most cases come from adversarial review rounds: each pins a path where prose was once lost
silently, a flag was missed, or a protected-token change went unreported.
"""
import json
import random
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # keep the repository free of .pyc files
sys.path.insert(0, str(HERE))
import prose_check as pc  # noqa: E402


def analyse(text, suffix=".md"):
    prose, notices, incomplete = pc.strip_markup(text, suffix)
    sents = [s for p in pc.paragraphs(prose) for s in pc.check_paragraph(p, 30, pc.TECH_TERMS)["sentences"]]
    return sents, incomplete


def joined(text, suffix=".md"):
    sents, incomplete = analyse(text, suffix)
    return " ".join(s["text"] for s in sents), incomplete


def kinds(text, suffix=".md"):
    return [k for s in analyse(text, suffix)[0] for k, _ in s["flags"]]


def changed(old, new, suffix=".md"):
    diff, unassessed, _, _ = pc.fidelity(old, suffix, new, suffix)
    out = {k for k, v in diff.items() if v["only_in_old"] or v["only_in_new"]}
    if unassessed["old_only"] or unassessed["new_only"]:
        out.add("unassessed")
    return out


def cli(args, stdin=""):
    return subprocess.run([sys.executable, str(HERE / "prose_check.py"), *args], input=stdin,
                          capture_output=True, text=True)


class Flags(unittest.TestCase):
    def test_flags_found(self):
        for text, kind in [
            ("Results are novel — and wrong.", "dash"),
            ("The estimator, a linear map, preserves the observed mean.", "comma-enclosed-phrase"),
            ("The model, which is linear, preserves the observed mean.", "comma-enclosed-phrase"),
            ("We established a bound, set by the sample size, for consistent estimation.", "comma-enclosed-phrase"),
            ("The data set these limits, with the prior of each model fixing the scale.", "with-ing"),
            ("The method reduces variance, preserving the mean across all trials.", "trailing-ing"),
            ("We located the noise level above which it cannot.", "stranded-auxiliary"),
            ("The solver failed. This is expected.", "bare-opener"),
            ("We face one problem: the data are sparse.", "colon"),
            ("Our method locates the limits that the data set.", "spatial-wording"),
            ("The bound clearly holds for every graph.", "presumptive"),
            ("We showed that the prior controls whether the parameter can be identified, and located the "
             "noise level above which the inference fails for small samples.", "propositions"),
        ]:
            with self.subTest(kind=kind):
                self.assertIn(kind, kinds(text))

    def test_false_positives_absent(self):
        for text, kind in [
            ("We tested running, jumping, swimming, walking, and resting protocols.", "comma-enclosed-phrase"),
            ("We compare the baseline with sampling from the reference distribution.", "with-ing"),
            ("Perfect sampling of the Ising model gives independent draws.", "hype"),
            ("The run started at 10:30 and ended at noon.", "colon"),
            ("A well-known two-point function was computed.", "dash"),
        ]:
            with self.subTest(text=text):
                self.assertNotIn(kind, kinds(text))

    def test_colon_exemption_covers_only_its_span(self):
        self.assertEqual(kinds("The ratio is 1:2: the estimates differ.").count("colon"), 1)

    def test_demonstrative_counts_occurrences_not_referents(self):
        sents, _ = analyse("A baseline model and a revised model were compared. This model converged.")
        notes = [d for s in sents for k, d in s["flags"] if k == "demonstrative"]
        self.assertTrue(any("2 earlier occurrences" in n and "not necessarily distinct" in n for n in notes))


class Splitting(unittest.TestCase):
    def test_sentence_boundaries(self):
        for text, counts in [
            ("Dr. Smith measured the loss. The estimate remained stable.", [5, 4]),
            ("The first trial failed. eBay supplied the second dataset.", [4, 5]),
            ("As shown by J. Smith in Fig. 2, the gap is 3.5 eV wide. It closes at high field.", [14, 5]),
        ]:
            with self.subTest(text=text):
                self.assertEqual([s["words"] for s in analyse(text)[0]], counts)

    def test_closing_quote_kept(self):
        self.assertTrue(analyse('We called it "stable." The second trial failed.')[0][0]["text"].endswith('"stable."'))

    def test_repeats_group_irregular_plurals(self):
        prose, _, _ = pc.strip_markup("The basis is fixed. Each of the bases spans it. The analysis and the analyses agree.", ".md")
        reps = {k for k, _, _ in pc.check_paragraph(pc.paragraphs(prose)[0], 30, [])["repeats"]}
        self.assertTrue({"bas", "analys"} <= reps)


class TypstNoSilentLoss(unittest.TestCase):
    def test_prose_survives_code_strings_raw_math(self):
        for src in [
            'The analysis follows.\n#let label = "["\nResults are novel — and wrong.\n',
            'The analysis follows.\n#let opener = "/*"\nResults are novel — and wrong.\n#let closer = "*/"\nThe end.\n',
            'The analysis follows.\n#text("/*")\nResults are novel — and wrong.\n#text("*/")\nThe end.\n',
            "The analysis follows.\n#let x = 1; Results are novel — and wrong.\nThe end.\n",
            'The analysis follows.\n#"/*"\nResults are novel — and wrong.\n#"*/"\nThe end.\n',
            'The analysis follows.\n#{ "/*" }\nResults are novel — and wrong.\n#{ "*/" }\nThe end.\n',
            "The analysis follows.\n#text[An opening parenthesis ( is printed.]\nResults are novel — and wrong.\n",
            '#let let-value = "M"\nThe analysis follows.\n#let-value Results are novel — and wrong.\nThe end.\n',
            "The delimiter is `/*`.\nResults are novel — and wrong.\nThe closing delimiter is `*/`.\n",
            "The analysis follows.\n```text\n/*\n```\nResults are novel — and wrong.\n```text\n*/\n```\nThe end.\n",
            'The set $"/*"$ is shown.\nResults are novel — and wrong.\nThe set $"*/"$ again.\n',
            "The delimiter is `$`.\nResults are novel — and wrong.\nThe closing delimiter is `$`.\n",
            'The analysis follows.\n#text("$")\nResults are novel — and wrong.\n#text("$")\nThe end.\n',
            "Intro text here.\n#box[#set text(size: 9pt); Inner words here.] Results are novel — and wrong.\n",
        ]:
            with self.subTest(src=src):
                text, incomplete = joined(src, ".typ")
                self.assertIn("novel", text)
                self.assertFalse(incomplete)

    def test_unsupported_or_unclosed_stops(self):
        for src in [
            'The analysis follows.\n#if true { "/*" }\nResults are novel.\n',
            "The analysis follows.\n#let f(x) = [\n  body\nResults are novel.\n",
            "Intro text here.\n/* unclosed comment\nResults are novel.\n",
            "Intro text here.\n```text\nnever closed\nResults are novel.\n",
        ]:
            with self.subTest(src=src):
                self.assertTrue(joined(src, ".typ")[1])

    def test_random_code_mixes_keep_every_prose_line(self):
        snippets = [
            '#let a = "/*"', '#let b = "*/"', '#let c = "//"', '#let d = "["', '#text("/*")', '#text(")")',
            '#let g = 1; ', '#let h(x) = [#x "quoted" text]', '#show heading: it => [#it.body]',
            '#let k = (a: "/*", b: "*/")', "// a line comment", "/* a block /* nested */ comment */", '#"/*"',
            '#{ let z = "*/"; z }', '#("//", 1)', '#text[An opening ( and a quote " in content]',
            '#box[#text("/*") inside]', "#let-value", "Inline `/*` raw.", "```text\n/*\n```", 'Math $"*/"$ here.',
            "Price \\$5 escaped.", '#emph[a `$` b]', "Cite @key and <lab>.",
        ]
        rng = random.Random(7)
        for trial in range(150):
            parts, markers = [], []
            for k in range(6):
                if rng.random() < 0.5:
                    parts.append(rng.choice(snippets))
                markers.append(f"Marker{trial}x{k}")
                parts.append(f"{markers[-1]} sentence is here.")
            text, incomplete = joined("\n".join(parts) + "\n", ".typ")
            self.assertFalse(incomplete, parts)
            self.assertEqual([m for m in markers if m not in text], [], parts)


class MarkdownNoSilentLoss(unittest.TestCase):
    def test_prose_survives_block_and_inline_boundaries(self):
        for src in [
            "The delimiter is \\`. Results are novel — and wrong. The closing delimiter is \\`.\n",
            "The delimiter is `.\n# Results\nResults are novel — and wrong. The closing delimiter is `.\n",
            "The delimiter is `.\n- Results are novel — and wrong.\n- The closing delimiter is `.\n",
            "The delimiter is `.\n--\nResults are novel — and wrong. The closing delimiter is `.\n",
            "Intro.\n```text\nx\n````\nResults are novel — and wrong.\n```text\ny\n```\nEnd.\n",
            "Intro.\n\n- ```text\n  x\n  ```\n\nResults are novel — and wrong.\n",
            "Intro.\n\n- <div></div>\nResults are novel — and wrong.\n\nEnd.\n",
            "Intro.\n\n- Item\n  <div>\nResults are novel — and wrong.\n\nEnd.\n",
            "- Item\nResults are novel — and wrong.\n",
            "Costs $5 and $6 here. Results are novel — and wrong.\n",
            "The delimiter is `$`.\nResults are novel — and wrong.\nThe closing delimiter is `$`.\n",
        ]:
            with self.subTest(src=src):
                self.assertIn("novel", joined(src)[0])

    def test_code_spans_still_recognised(self):
        self.assertEqual(joined("Code `a $ b` here and ``x ` y`` there. Unclosed ` tick and words remain.\n")[0].count("CODE"), 2)
        text = joined("The code is `alpha\nbeta`. Results are novel.\n")[0]
        self.assertIn("CODE", text)
        self.assertNotIn("alpha", text)


class LatexNoSilentLoss(unittest.TestCase):
    def test_literals_and_escaped_dollars(self):
        text, _ = joined("It costs \\$5 and \\$6. Use \\verb|50%| here. Results are novel. "
                         "See \\url{http://a.b/c%20d} now. Final words.\n", ".tex")
        for word in ("costs", "novel", "Final words"):
            self.assertIn(word, text)


class Compare(unittest.TestCase):
    def test_reported_differences(self):
        for name, old, new, key, suffix in [
            ("math", "We obtain $x=2$ here.", "We obtain $x=3$ here.", "math spans (verbatim)", ".md"),
            ("score swap", "Method A scored 90 and method B scored 80.", "Method A scored 80 and method B scored 90.",
             "numbers with units: same token, new context (review)", ".md"),
            ("negation moved", "A is not stable. B is stable.", "A is stable. B is not stable.",
             "negations: same token, new context (review)", ".md"),
            ("all dropped", "All tested cases converge.", "Tested cases converge.", "scope words and bounds", ".md"),
            ("bound flipped", "The error is at most 5 percent.", "The error is at least 5 percent.", "scope words and bounds", ".md"),
            ("contraction", "The chain doesn't converge.", "The chain converges.", "negations", ".md"),
            ("unit", "Each step takes 10 ms.", "Each step takes 10 s.", "numbers with units", ".md"),
            ("cite optional arg", "See \\cite[p. 4]{Alpha2025}.", "See \\cite[p. 4]{Beta2025}.", "citation keys", ".tex"),
            ("cite starred", "See \\cite*{Alpha}.", "See \\cite*{Beta}.", "citation keys", ".tex"),
            ("textcite", "As \\textcite{Alpha} showed.", "As \\textcite{Beta} showed.", "citation keys", ".tex"),
            ("equation env", "We use \\begin{equation}x=2\\end{equation} here.", "We use \\begin{equation}x=3\\end{equation} here.",
             "math spans (verbatim)", ".tex"),
            ("siunitx", "Takes \\SI[round-precision=2]{10}{\\milli\\second}.", "Takes \\SI[round-precision=2]{10}{\\second}.",
             "quantity macros (verbatim)", ".tex"),
            ("custom macro", "We use \\customA here.", "We use \\customB here.", "unassessed", ".tex"),
            ("percent in verb", "A \\verb|50%| b \\cite{Alpha}.", "A \\verb|50%| b \\cite{Beta}.", "citation keys", ".tex"),
        ]:
            with self.subTest(name=name):
                self.assertIn(key, changed(old, new, suffix))

    def test_identical_text_has_no_difference(self):
        self.assertEqual(changed("We showed that the spectrum sets a boundary [3].",
                                 "We showed that the spectrum sets a boundary [3]."), set())


class ExitCodes(unittest.TestCase):
    def test_strict_and_empty(self):
        self.assertEqual(cli(["--strict", "-"], "Results are novel — and wrong.").returncode, 1)
        self.assertEqual(cli(["--strict", "-"], "Perfect sampling is exact here and the model is novel.").returncode, 0)
        self.assertEqual(cli(["-"], "   \n\n").returncode, 2)

    def test_markdown_table_is_skipped_not_failed(self):
        r = cli(["--strict", "-"], "The scores are below.\n\n| Method | Score |\n|:---|---:|\n| A | 3 |\n")
        self.assertEqual(r.returncode, 0)
        self.assertIn("table", r.stderr)

    def test_unreadable_compare_input(self):
        r = cli(["--compare", str(HERE / "no-such-file.md"), str(HERE / "no-such-file-2.md")])
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_json_output_parses(self):
        data = json.loads(cli(["--json", "-"], "One sentence here. Another one follows.").stdout)
        self.assertEqual(data["paragraphs"][0]["word_counts"], [3, 3])


if __name__ == "__main__":
    unittest.main(verbosity=1)
