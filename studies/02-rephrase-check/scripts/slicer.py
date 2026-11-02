"""One fixed bug order, stratified by repo. Slices are consecutive runs of it."""
import random
from collections import Counter

SEED = 20261101


def bug_order(bugs, seed=SEED):
    """bugs: dicts with instance_id and repo. Returns instance ids.

    Each next place goes to the repo furthest behind its benchmark share, so any
    consecutive run of the order keeps the mix. Ties and the order inside a repo
    come from the seed.
    """
    rng = random.Random(seed)
    queues = {}
    for b in sorted(bugs, key=lambda b: b["instance_id"]):
        queues.setdefault(b["repo"], []).append(b["instance_id"])
    repos = sorted(queues)
    for r in repos:
        rng.shuffle(queues[r])
    tiebreak = {r: rng.random() for r in repos}
    total = len(bugs)
    share = {r: len(queues[r]) / total for r in repos}
    taken = Counter()
    order = []
    for place in range(1, total + 1):
        open_repos = [r for r in repos if queues[r]]
        r = max(open_repos, key=lambda x: (share[x] * place - taken[x], tiebreak[x]))
        order.append(queues[r].pop(0))
        taken[r] += 1
    return order


def slices(order, size):
    return [order[i:i + size] for i in range(0, len(order), size)]
