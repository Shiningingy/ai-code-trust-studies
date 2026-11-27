#!/bin/sh
for i in 1 2 3 4; do python -m gram parse train/doc$i.md --lib lib --manual train/doc$i.manual.jsonl --out out/doc$i | tail -2; done
