"""Step 4: a variant of one test instance with known changes of four kinds, to check how sessions triage outliers.

Every change keeps the facts the same, so the original answer key still holds:
  1 form   : the data's form is broken (typo in a non-name word, case flips, spacing)   -> expected: a Normalizer
  2 grammar: a fact rewritten in a construction the generator never uses, 4 times each -> expected: a Rule
  3 free   : a fact rewritten once as free text                                        -> expected: manual.jsonl
  4 noise  : inserted garbled passages that carry no fact                              -> expected: ignored
Decisive facts of answer people are included in kinds 1-3, so a wrong triage can cost the answer.

Usage: python -I make_variants.py <context.md> <answers.json> <out_context.md> <out_manifest.jsonl> [seed]
"""
import json
import random
import re
import sys

NAME = r"(?<![\w.])(?P<n>(?:[A-Z]\. )?[A-Z][a-z]+(?: [A-Z][a-z]+)?)"
YID = r"(?P<y>Y\d{3}|Youth \d{3})"
FACTS = {  # relation: (pattern of the generator's clause, kind-2 rewrite, kind-3 free-text rewrite)
    "volunteered": (NAME + r" volunteered at (?P<e>event-P-\d+-\d+) during this-year",
                    "During this-year, {n} volunteered at {e}",
                    "{n} showed up to help at {e} this year, as a volunteer"),
    "night_shift": (NAME + r" works the night shift",
                    "The night shift is the shift {n} works",
                    "If you call {n} at noon you will wake them up, because {n} works nights"),
    "taught": (NAME + r" took part in (?P<x>[a-z]+(?: [a-z]+)?) class as the teacher this year",
               "This year {n} was the teacher of the {x} class",
               "The {x} class this year was run by {n}, who stood at the front as its teacher"),
    "fruit": (NAME + r" enjoys eating (?P<f>[a-z]+)(?=[.,;]|$)",
              "Eating {f} is something {n} enjoys",
              "{n} never says no to {f}; it is a favourite food"),
    "guardian": (NAME + r" is the legal guardian of " + YID,
                 "{y} has {n} as legal guardian",
                 "{n} signs the school forms for {y}, as {y}'s legal guardian"),
    "course": (YID + r" currently attends (?P<c>evening_[a-z]+) during the evening",
               "{y} is currently enrolled in {c} in the evening",
               "These days {y} spends evenings at {c}"),
}
TYPO_WORDS = ["volunteered", "currently", "guardian", "evening", "attends", "teacher", "enjoys", "recommended",
              "discussed", "registration"]
NOISE = ["xq lorm vlntr shft ev_ng 4#1 kk", "the the of of of and P- .. -- evnt", "zzzt :: 0x1f qwe ghost-line ., ,",
         "Lorem ipsum dolor sit amet attends.", "### ###", "~~ reed reed reed ~~", "na na na. na.", "1 2 3 4 5 6 7 8 9"]


def whole_sentence(line, m):
    """True if the match is a sentence of its own (so free text can replace it without touching other facts)."""
    start = line.rfind(". ", 0, m.start())
    start = 0 if start < 0 else start + 2
    end = line.find(".", m.end())
    end = len(line) if end < 0 else end
    return line[start:end].strip() == m.group(0)


def typo(w, rng):
    i = rng.randrange(1, len(w) - 2)
    return w[:i] + w[i + 1] + w[i] + w[i + 2:]  # swap two neighbours: edit distance 2


def main():
    src, key_path, out_path, man_path = sys.argv[1:5]
    rng = random.Random(int(sys.argv[5]) if len(sys.argv) > 5 else 17)
    text = open(src, encoding="utf-8").read()
    key = json.load(open(key_path, encoding="utf-8"))["matches"]
    lines = text.split("\n")
    qline = max(i for i, l in enumerate(lines) if "Final Query" in l)
    body = [i for i in range(qline) if lines[i].strip() and not lines[i].startswith("#")]

    # answer people: names from the roster lines
    names = set()
    for i in body:
        for m in re.finditer(r"records (.+?) under identifier (p-\d+)(?: and also uses the familiar names (.+?))?\.", lines[i], re.I):
            if m.group(2).upper() in key:
                names |= {m.group(1)} | ({x.strip() for x in re.split(r",| and ", m.group(3)) if x.strip()} if m.group(3) else set())
    nums = {k[2:] for k in key}

    def about_answer(gd):
        return gd.get("n") in names or any(gd.get("y", "").endswith(n) for n in nums)

    used, changes = set(), []
    for rel, (pat, rw2, rw3) in FACTS.items():
        rx = re.compile(pat)
        hits = [(i, m) for i in body for m in rx.finditer(lines[i])]
        ans = [h for h in hits if about_answer(h[1].groupdict())]
        rest = [h for h in hits if not about_answer(h[1].groupdict())]
        rng.shuffle(ans)
        rng.shuffle(rest)
        # kind 3: one decisive fact of an answer person, a whole sentence on its own
        k3 = [h for h in ans if whole_sentence(lines[h[0]], h[1])]
        plan = [(3, k3[:1])] + [(2, ans[1:2] + rest[:3])]
        for kind, sel in plan:
            for i, m in sel:
                if i in used:
                    continue
                g = {k: v for k, v in m.groupdict().items() if v}
                new = (rw3 if kind == 3 else rw2).format(**g)
                lines[i] = lines[i][:m.start()] + new + lines[i][m.end():]
                used.add(i)
                changes.append({"kind": kind, "relation": rel, "answer_person": about_answer(m.groupdict()),
                                "before": m.group(0), "after": new, "orig_line": i + 1})
    # kind 1: typos and case flips in other lines, half of them in lines about answer people
    cand = [i for i in body if i not in used and any(w in lines[i] for w in TYPO_WORDS)]
    ans_lines = [i for i in cand if any(n in lines[i] for n in names)]
    rng.shuffle(cand)
    rng.shuffle(ans_lines)
    picked = []
    for i in ans_lines[:12] + cand:
        if i not in picked and i not in used:
            picked.append(i)
        if len(picked) >= 40:
            break
    for j, i in enumerate(picked):
        before = lines[i]
        w = next(w for w in TYPO_WORDS if w in lines[i])
        if j % 3 == 0:
            lines[i] = lines[i].replace(w, typo(w, rng), 1)
        elif j % 3 == 1:
            lines[i] = lines[i].replace(w, w.upper(), 1)
        else:
            lines[i] = lines[i].replace(" " + w, "  " + w.capitalize(), 1)
        used.add(i)
        changes.append({"kind": 1, "relation": w, "answer_person": i in ans_lines, "before": before, "after": lines[i],
                        "orig_line": i + 1})
    # kind 4: garbled passages inserted (no line removed, so no fact is lost)
    spots = sorted(rng.sample(body, len(NOISE)), reverse=True)
    for i, junk in zip(spots, NOISE):
        lines[i + 1:i + 1] = ["", "### Passage D-9%04d" % rng.randrange(10000), "", junk]
        changes.append({"kind": 4, "relation": "noise", "answer_person": False, "before": "", "after": junk,
                        "orig_line": i + 1})
    out = "\n".join(lines)
    open(out_path, "w", encoding="utf-8").write(out)
    new_lines = out.split("\n")
    with open(man_path, "w", encoding="utf-8") as f:
        for c in changes:
            c["line"] = next((n for n, l in enumerate(new_lines, 1) if c["after"] and c["after"] in l), None)
            f.write(json.dumps(c) + "\n")
    print({k: sum(c["kind"] == k for c in changes) for k in (1, 2, 3, 4)},
          "about answer people:", sum(c["answer_person"] for c in changes))


if __name__ == "__main__":
    main()
