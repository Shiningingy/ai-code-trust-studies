import re
from gram import Splitter, Normalizer, PatternRule

class SentCommaAnd(Splitter):
    name = "sent_comma_and"; solves = "sentences, then ', and' / ', ' joins"; added_by = "test"
    droppable = [r",?\s*and", r","]
    examples = [("A owns a camera, and B owns a guitar.", ["A owns a camera", "B owns a guitar."])]
    def split(self, line):
        out = []
        for s in re.split(r"(?<=[.!?])(?<!\b[A-Z]\.)\s+", line.strip()):
            out += [p for p in re.split(r",\s*and\s+|,\s+(?=[A-Z])", s) if p]
        return out

class Curly(Normalizer):
    name = "curly"; solves = "curly quotes to straight"; added_by = "test"
    examples = [("\u201chi\u201d", '"hi"')]
    def apply(self, c): return c.replace("\u201c", '"').replace("\u201d", '"')

class BadDrop(Normalizer):
    name = "bad_drop"; solves = "deliberately bad: deletes 'in the past'"; added_by = "test"
    examples = [("x in the past", "x")]
    def apply(self, c): return c.replace(" in the past", "")

class Owns(PatternRule):
    name = "owns"; solves = "X owns a Y"; added_by = "test"
    pattern = r"(?P<s>.+?) owns an? (?P<o>[a-z ]+)\.?"
    examples = [("Ben Mensah owns a guitar.", [{"subject": "Ben Mensah", "relation": "owns", "object": "guitar", "qualifiers": []}])]
    def build(self, g): return [{"subject": g["s"], "relation": "owns", "object": g["o"], "qualifiers": []}]

class Owns2(PatternRule):
    name = "owns_dup"; solves = "deliberate duplicate with different facts, to test ambiguity"; added_by = "test"
    pattern = r"(?P<s>.+?) owns a camera\.?"
    examples = [("A owns a camera", [{"subject": "A", "relation": "has", "object": "camera", "qualifiers": []}])]
    def build(self, g): return [{"subject": g["s"], "relation": "has", "object": "camera", "qualifiers": []}]
