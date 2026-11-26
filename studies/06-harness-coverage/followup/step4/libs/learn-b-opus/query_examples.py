"""Worked query helpers on top of facts.py (the conditions of the three training queries).

    python -m gram parse doc.md --lib lib --manual doc.manual.jsonl --out out
    python lib/query_examples.py out/parsed.jsonl

Reuse the helpers below for new queries; see NOTES.md for what each relation and qualifier means.
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facts import Facts  # noqa: E402

# World knowledge the documents do not state (needed to read the queries).
COASTAL = {"Halifax", "Vancouver", "Victoria", "Lunenburg", "St. John's"}   # not: Edmonton Calgary Regina Winnipeg Ottawa
PUBLIC_TRANSPORT = {"bus", "tram", "subway", "train", "metro", "streetcar", "ferry", "light rail"}
FRUIT = {"apple", "banana", "mango", "orange", "peach", "pear", "plum", "watermelon"}   # not: bread rice lentils
DAIRY = {"milk", "cheese", "yogurt", "butter", "dairy products"}


def people(F, relation, obj=None, has=(), lacks=("past",)):
    """Person IDs with a current (not past) fact of this relation."""
    return {f["pid"] for f in F.find(relation, obj, has, lacks) if f["pid"]}


def works_in_city(F, cities):
    orgs = F.orgs_in()
    return {f["pid"] for f in F.find("works_for", lacks=("past",)) if f["pid"] and orgs.get(f["object"]) in cities}


def ordinarily_public_transport(F):
    # "routinely travels by X" and not "... but no longer does" (past); "used the bus once" and
    # "plans to use the bus in the future" do not count
    return people(F, "travels_by", lambda o: o in PUBLIC_TRANSPORT, has=("routinely",))


def night_shift_now(F):
    return people(F, "works_shift", "night")


def events_this_year(F, n):
    ev = collections.defaultdict(set)
    for f in F.find("volunteered_at", has=("during this-year",)):
        if f["pid"]:
            ev[f["pid"]].add(f["object"])
    return {p for p, e in ev.items() if len(e) >= n}


def avoids_dairy_now(F):
    # "currently chooses to avoid dairy products"; "is temporarily skipping cheese" is temporarily_skipping, and
    # "dislikes eating milk" / "buys milk for other people" are other relations: none of them count
    return people(F, "avoids", "dairy products")


def guardian_of_evening_course(F):
    yc = F.youth_courses()
    evening = {y for y, fs in yc.items()
               if any("during the evening" in f["qualifiers"] and "past" not in f["qualifiers"] for f in fs)}
    # emergency_contact_for is NOT guardianship
    return {f["pid"] for f in F.find("guardian_of", lacks=("past",)) if f["pid"] and f["object"] in evening}


def genuinely_prefers_train(F):
    # not chose_train_over_plane ("only because of a disruption"), not likes_train_and_plane_equally
    return people(F, "prefers_train_to_plane")


def enjoys_fruit_now(F):
    return people(F, "enjoys_eating", lambda o: o in FRUIT)


if __name__ == "__main__":
    F = Facts(sys.argv[1])
    for name, s in [("coastal employer", works_in_city(F, COASTAL)),
                    ("public transport", ordinarily_public_transport(F)),
                    ("night shift now", night_shift_now(F)),
                    ("3+ events this year", events_this_year(F, 3)),
                    ("avoids dairy", avoids_dairy_now(F)),
                    ("guardian of evening-course youth", guardian_of_evening_course(F)),
                    ("genuinely prefers train", genuinely_prefers_train(F)),
                    ("enjoys a fruit", enjoys_fruit_now(F))]:
        print("%-34s %3d  %s" % (name, len(s), " ".join(sorted(s)[:12])))
