"""Update helper (update/starstack-update.py): when the health check undoes an update, and what undo
touches. No printer needed: Moonraker, systemd and the clock are faked. Run: python -m pytest tests"""
import importlib.util
import os
import subprocess
import time as real_time
import types

import pytest

HERE = os.path.dirname(__file__)
SPEC = importlib.util.spec_from_file_location("ssu", os.path.join(HERE, "..", "update", "starstack-update.py"))

GOOD = {"klipper": "a" * 40, "moonraker": "b" * 40}
NEW = {"klipper": "c" * 40, "moonraker": "b" * 40}


@pytest.fixture
def h(monkeypatch, tmp_path):
    """The helper with a fake clock and printer; h.calls records undo/record_good calls."""
    m = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(m)
    clock = [1000.0]
    m.time = types.SimpleNamespace(time=lambda: clock[0], sleep=lambda s: None,
                                   strftime=real_time.strftime, localtime=real_time.localtime)
    m.clock = clock
    m.calls = []
    m.printer = {"printing": False, "updating": False, "klippy": "ready", "healthy": (True, ""), "versions": NEW}
    monkeypatch.setattr(m, "STATE", str(tmp_path / "state.json"))
    monkeypatch.setattr(m, "HEALTH", str(tmp_path / "health"))
    monkeypatch.setattr(m, "UNDO_REQUEST", str(tmp_path / "undo-request"))
    monkeypatch.setattr(m, "LOG", str(tmp_path / "helper.log"))
    monkeypatch.setattr(m, "pins_hash", lambda: "pins1")
    monkeypatch.setattr(m, "current_versions", lambda: dict(m.printer["versions"]))
    monkeypatch.setattr(m, "healthy", lambda: m.printer["healthy"])
    monkeypatch.setattr(m, "busy_printing", lambda: m.printer["printing"])

    def api(path, method="GET", timeout=10):
        if path == "/machine/update/status":
            return {"busy": m.printer["updating"]}
        if path == "/printer/info":
            return {"state": m.printer["klippy"]}
        return {}
    monkeypatch.setattr(m, "api", api)

    def undo(st, target, reason, auto):  # like the real one: the old versions are running again
        m.calls.append(("undo", target, auto))
        m.printer.update(versions=dict(target["versions"]), healthy=(True, ""))
        return "undone"

    def record_good(st, cur):
        m.calls.append(("record_good", cur))
        st["good"] = {"versions": dict(cur), "time": m.clock[0]}
    monkeypatch.setattr(m, "undo", undo)
    monkeypatch.setattr(m, "record_good", record_good)
    monkeypatch.setattr(m, "save_config", lambda st, cur: m.calls.append(("save_config", cur)))
    return m


def state(**extra):
    return dict({"pins": "pins1", "good": {"versions": GOOD, "time": 0}, "prev": None}, **extra)


def run_for(h, st, seconds):
    """Poll every 15 s like the service does; return the last status line."""
    out = None
    for _ in range(int(seconds // 15) + 1):
        out = h.health_step(st)
        h.clock[0] += 15
    return out


# ---------------------------------------------------------------- when it undoes


def test_unhealthy_update_is_undone_after_5_minutes(h):
    h.printer["healthy"] = (False, "Klipper is error")
    st = state()
    assert "checking the update" in run_for(h, st, h.HEALTH_WAIT - 30)
    assert h.calls == []  # not yet: still inside the 5 minutes
    run_for(h, st, 60)
    assert h.calls == [("undo", st["good"], True)]


def test_never_undo_while_printing(h):
    h.printer.update(healthy=(False, "the touchscreen app isn't running"), printing=True)
    st = state()
    assert "waiting for the print" in run_for(h, st, h.HEALTH_WAIT + 120)
    assert h.calls == []


def test_klipper_shutdown_is_not_blamed_on_the_update(h):
    h.printer.update(healthy=(False, "Klipper is shutdown"), klippy="shutdown")
    st = state()
    assert "unrelated" in run_for(h, st, h.HEALTH_WAIT + 120)
    assert h.calls == []


def test_healthy_update_must_stay_up_a_minute_before_it_counts(h):
    st = state()
    run_for(h, st, h.HEALTH_STEADY - 15)
    assert h.calls == []
    run_for(h, st, 30)
    assert h.calls == [("record_good", NEW)]
    assert "changed_at" not in st


def test_a_blip_restarts_the_steady_minute(h):
    st = state()
    run_for(h, st, 45)
    h.printer["healthy"] = (False, "Moonraker isn't answering")
    h.health_step(st)
    h.printer["healthy"] = (True, "")
    run_for(h, st, 30)
    assert h.calls == []  # 45 s healthy before the blip doesn't count


def test_the_5_minutes_start_when_moonraker_finishes_updating(h):
    h.printer.update(healthy=(False, "Klipper is startup"), updating=True)
    st = state()
    run_for(h, st, 600)  # a long update
    assert h.calls == []
    h.printer["updating"] = False
    run_for(h, st, h.HEALTH_WAIT - 30)
    assert h.calls == []


def test_new_tested_versions_installing_is_not_judged(h):
    h.printer["healthy"] = (False, "Klipper is error")
    h.pins_hash = lambda: "pins2"
    st = state()
    assert run_for(h, st, h.HEALTH_WAIT + 120) is None
    assert h.calls == []


def test_first_healthy_run_records_good(h):
    st = {"pins": "pins1"}
    h.health_step(st)
    assert h.calls == [("save_config", NEW)]


# ---------------------------------------------------------------- the Undo button


def press_undo(h):
    open(h.UNDO_REQUEST, "w").close()


def test_undo_button_ignored_while_printing(h):
    h.printer["printing"] = True
    press_undo(h)
    st = state(prev={"versions": GOOD, "time": 0})
    assert "ignored" in h.health_step(st)
    assert h.calls == [] and not os.path.exists(h.UNDO_REQUEST)


def test_undo_button_with_nothing_to_go_back_to(h):
    press_undo(h)
    assert "nothing to go back to" in h.health_step(state())
    assert h.calls == []


def test_undo_button_goes_back_one_step(h):
    press_undo(h)
    prev = {"versions": GOOD, "time": 0}
    h.health_step(state(prev=prev))
    assert h.calls == [("undo", prev, False)]


# ---------------------------------------------------------------- what undo touches


def git(path, *args):
    return subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, check=True).stdout.strip()


def make_repo(path):
    path.mkdir()
    git(path, "init", "-q")
    git(path, "config", "user.email", "t@t")
    git(path, "config", "user.name", "t")
    shas = []
    for n in ("1", "2"):
        (path / "f.txt").write_text(n)
        git(path, "add", ".")
        git(path, "commit", "-q", "-m", n)
        shas.append(git(path, "rev-parse", "HEAD"))
    return shas


@pytest.fixture
def real_undo(monkeypatch, tmp_path):
    """The real undo() against two git repos and a config folder; services and Moonraker faked."""
    m = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(m)
    m.time = types.SimpleNamespace(time=real_time.time, sleep=lambda s: None,
                                   strftime=real_time.strftime, localtime=real_time.localtime)
    repos = {n: tmp_path / n for n in ("klipper", "KlipperScreen")}
    m.shas = {n: make_repo(p) for n, p in repos.items()}
    m.restarted = []
    cfg, good = tmp_path / "config", tmp_path / "good"
    cfg.mkdir()
    good.mkdir()
    for name, d in (("STATE", "state.json"), ("HEALTH", "health"), ("LOG", "helper.log")):
        monkeypatch.setattr(m, name, str(tmp_path / d))
    monkeypatch.setattr(m, "GIT_REPOS", {n: str(p) for n, p in repos.items()})
    monkeypatch.setattr(m, "CONFIG_DIR", str(cfg))
    monkeypatch.setattr(m, "GOOD_DIR", str(good))
    monkeypatch.setattr(m, "api", lambda *a, **k: {})
    monkeypatch.setattr(m, "restart", lambda unit: m.restarted.append(unit))
    monkeypatch.setattr(m, "wait_klipper", lambda *a, **k: True)
    monkeypatch.setattr(m, "pins_hash", lambda: "pins1")
    m.repos, m.cfg, m.good = repos, cfg, good
    return m


def test_undo_resets_repos_but_never_wipes_local_changes(real_undo):
    m = real_undo
    (m.repos["KlipperScreen"] / "f.txt").write_text("someone's work")
    target = {"versions": {n: s[0] for n, s in m.shas.items()}, "config": {}, "config_dir": str(m.good)}
    m.undo({}, target, "Klipper is error", auto=True)
    assert git(m.repos["klipper"], "rev-parse", "HEAD") == m.shas["klipper"][0]
    assert git(m.repos["KlipperScreen"], "rev-parse", "HEAD") == m.shas["KlipperScreen"][1]
    assert (m.repos["KlipperScreen"] / "f.txt").read_text() == "someone's work"
    assert "klipper" in m.restarted


def test_auto_undo_restores_only_config_changed_during_the_update(real_undo):
    m = real_undo
    good_text, old_edit, new_text = "[good]\n", "[user edit last week]\n", "[changed by the update]\n"
    for name in ("printer.cfg", "moonraker.conf"):
        (m.good / name).write_text(good_text)
    (m.cfg / "printer.cfg").write_text(new_text)
    (m.cfg / "moonraker.conf").write_text(old_edit)
    week_ago = real_time.time() - 7 * 86400
    os.utime(m.cfg / "moonraker.conf", (week_ago, week_ago))
    target = {"versions": {n: s[1] for n, s in m.shas.items()}, "config_dir": str(m.good),
              "config": {n: m.file_hash(str(m.good / n)) for n in ("printer.cfg", "moonraker.conf")}}
    m.undo({"changed_at": real_time.time() - 300}, target, "Klipper is error", auto=True)
    assert (m.cfg / "printer.cfg").read_text() == good_text
    assert (m.cfg / "printer.cfg.pre-undo").read_text() == new_text  # the changed copy is kept
    assert (m.cfg / "moonraker.conf").read_text() == old_edit  # the user's own older edit stays
    assert "moonraker" in m.restarted and "klipper" in m.restarted


def test_manual_undo_leaves_config_alone(real_undo):
    m = real_undo
    (m.good / "printer.cfg").write_text("[good]\n")
    (m.cfg / "printer.cfg").write_text("[now]\n")
    target = {"versions": {n: s[0] for n, s in m.shas.items()}, "config_dir": str(m.good), "time": 0,
              "config": {"printer.cfg": m.file_hash(str(m.good / "printer.cfg"))}}
    st = {"prev": target}
    m.undo(st, target, "Undo button", auto=False)
    assert (m.cfg / "printer.cfg").read_text() == "[now]\n"
    assert st["prev"] is None  # one step of undo only


# ---------------------------------------------------------------- board firmware check


@pytest.mark.parametrize("state,msg,host,mcu,want", [
    ("ready", "", "v0.13.0-501", "v0.13.0-501", False),
    ("ready", "", "v0.13.0-501", "v0.12.0-100", True),
    ("ready", "", "v0.13.0-501", None, False),  # board version unknown: don't flash
    ("error", "MCU Protocol error", "v0.13.0-501", None, True),
    ("error", "Unable to open serial port", "v0.13.0-501", None, False),
    ("ready", "", "", "v0.12.0", False),
])
def test_mismatch(h, state, msg, host, mcu, want):
    assert h.mismatch(state, msg, host, mcu) is want
