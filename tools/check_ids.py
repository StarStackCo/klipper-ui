"""Decision (D-), question (Q-) and backlog (B-) numbers must be unique across the logs.
   python tools/check_ids.py           fail if any number is used by two rows (CI runs this)
   python tools/check_ids.py --next D  print the next free number, e.g. D-128
"""
import collections
import glob
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ROW = re.compile(r"^\|\s*([DQB])-(\d+)\s*\|", re.M)


def find_ids(files):
    """{(letter, number): [file, ...]} for every table row that starts with an ID."""
    seen = collections.defaultdict(list)
    for path in files:
        with open(path, encoding="utf-8") as f:
            for letter, num in ROW.findall(f.read()):
                seen[(letter, int(num))].append(os.path.basename(path))
    return seen


def log_files():
    docs = os.path.join(ROOT, "docs")
    return [os.path.join(docs, "DECISIONS.md"), os.path.join(docs, "BACKLOG.md")] + \
        sorted(glob.glob(os.path.join(docs, "archive", "*.md")))


def main(argv):
    seen = find_ids(log_files())
    if argv[:1] == ["--next"]:
        letter = argv[1].upper()
        nums = [n for (lt, n) in seen if lt == letter]
        width = 2 if letter == "B" else 3
        print(f"{letter}-{max(nums, default=0) + 1:0{width}d}")
        return 0
    dups = {k: v for k, v in seen.items() if len(v) > 1}
    for (letter, num), where in sorted(dups.items()):
        print(f"{letter}-{num:03d} used {len(where)} times: {', '.join(where)}")
    if not dups:
        print(f"ok: {len(seen)} IDs, no duplicates")
    return 1 if dups else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
