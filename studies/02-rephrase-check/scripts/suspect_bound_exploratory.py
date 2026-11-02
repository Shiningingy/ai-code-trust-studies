"""EXPLORATORY, after labels. Bugs whose gold test shows no fail-to-pass in the scoring images
may be labelled wrong for environment reasons. Bounds what that could do to RQ1. Labels are not changed."""
import analyze as an

CRASHED = {"sphinx-doc__sphinx-8551", "sphinx-doc__sphinx-8721"}
SUSPECT = CRASHED | {"matplotlib__matplotlib-26291", "pylint-dev__pylint-6386", "pylint-dev__pylint-7080"}


def main():
    lab, _ = an.labels("baseline")
    rows = [an.row_for(b, w) for b, w in sorted(lab.items())]
    rows = [r for r in rows if r["S"] is not None]
    med = an.split(rows, "S")[0]
    for r in rows:
        if r["id"] in SUSPECT:
            print(r["id"], round(r["S"], 3), "far" if r["S"] > med else "close", "wrong" if r["wrong"] else "right")
    an.split_line("as labelled", rows, "S")
    for name, group in (("two crashed counted right", CRASHED), ("all five counted right", SUSPECT)):
        g = [{**r, "wrong": False} if r["id"] in group else r for r in rows]
        an.split_line(name, g, "S")
        print("   AUROC", round(an.stratified_auc(g, "S", an.repo)[0], 3))
    g = [r for r in rows if r["id"] not in SUSPECT]
    an.split_line("all five dropped", g, "S")
    print("   AUROC", round(an.stratified_auc(g, "S", an.repo)[0], 3), "bugs", len(g), "wrong", sum(r["wrong"] for r in g))
    print("\nEXPLORATORY: not in the frozen plan.")


if __name__ == "__main__":
    main()
