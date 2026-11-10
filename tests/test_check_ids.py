"""check_ids.py: duplicate D/Q/B numbers are caught, the next number skips used ones."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import check_ids  # noqa: E402


def test_duplicates_and_next(tmp_path, monkeypatch, capsys):
    a, b = tmp_path / "DECISIONS.md", tmp_path / "old.md"
    a.write_text("| D-119 | x |\n| D-120 | x |\n| Q-005 | x |\nsee D-200 in text\n", encoding="utf-8")
    b.write_text("| D-119 | x |\n", encoding="utf-8")
    monkeypatch.setattr(check_ids, "log_files", lambda: [str(a), str(b)])

    assert check_ids.main([]) == 1
    assert "D-119 used 2 times" in capsys.readouterr().out
    assert check_ids.main(["--next", "D"]) == 0
    assert capsys.readouterr().out.strip() == "D-121"  # D-200 is prose, not a row

    b.write_text("| D-118 | x |\n", encoding="utf-8")
    assert check_ids.main([]) == 0
