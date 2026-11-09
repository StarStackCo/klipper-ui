"""USB stick import: what gets copied, skipped or renamed (audit #6). Run: python -m pytest tests"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import usb_import  # noqa: E402


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def run(monkeypatch, stick, gcodes):
    monkeypatch.setattr(sys, "argv", ["usb_import.py", str(stick), "--gcodes", str(gcodes)])
    usb_import.main()
    with open(gcodes / ".starstack" / "usb_import.json") as f:
        return json.load(f)


def test_copy_skip_and_rename(tmp_path, monkeypatch):
    stick, gcodes = tmp_path / "stick", tmp_path / "printer_data" / "gcodes"
    write(str(stick / "cube.gcode"), "G1 X1\n")
    write(str(stick / "parts" / "arm.gcode"), "G1 X2\n")
    write(str(stick / "config.g"), "not a print file\n")
    write(str(stick / ".hidden.gcode"), "skip me\n")
    gcodes.mkdir(parents=True)

    first = run(monkeypatch, stick, gcodes)
    assert sorted(first["copied"]) == ["cube.gcode", "parts/arm.gcode"]
    assert not (gcodes / "config.g").exists() and not (gcodes / ".hidden.gcode").exists()

    # same stick again: everything is already there
    again = run(monkeypatch, stick, gcodes)
    assert again["copied"] == [] and again["skipped"] == 2

    # same name, new content: kept as "cube (2)"; plugging in once more skips it
    write(str(stick / "cube.gcode"), "G1 X9\n")
    third = run(monkeypatch, stick, gcodes)
    assert third["copied"] == ["cube (2).gcode"]
    assert run(monkeypatch, stick, gcodes)["copied"] == []
    assert not list((tmp_path / "printer_data" / ".starstack_usb_tmp").iterdir())  # no temp left


def test_symlink_is_not_followed(tmp_path, monkeypatch):
    secret = tmp_path / "secret_key"
    secret.write_text("private")
    stick, gcodes = tmp_path / "stick", tmp_path / "gcodes"
    stick.mkdir()
    gcodes.mkdir()
    try:
        os.symlink(secret, stick / "cube.gcode")
    except (OSError, NotImplementedError):
        pytest.skip("this system can't make symlinks")
    report = run(monkeypatch, stick, gcodes)
    assert report["copied"] == [] and not (gcodes / "cube.gcode").exists()
