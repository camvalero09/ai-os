"""The session table an agent is shown at startup must fit on a screen.

A hook prints this into every session before the agent reads anything else.
The first version printed every heartbeat of the last fourteen days: 477
words, 30 rows, of which 18 were sessions that started, did nothing and
ended. The one line that decides whether it is safe to edit sat at the
bottom. Two behavioural tests skipped coordination entirely, and the cause
was volume rather than absence.
"""
from __future__ import annotations

import importlib.util
import io
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "sessions.py"

# A startup injection larger than this competes with the request itself.
MAX_STARTUP_WORDS = 140


def load():
    spec = importlib.util.spec_from_file_location("sessions_brief_test", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def beat(mod, ident, state, efforts=(), age_min=0):
    now = time.time()
    return {
        "id": ident,
        "agent": "Claude Code",
        "model": "unknown",
        "started": now - age_min * 60,
        "last_beat": now - age_min * 60,
        "state": state,
        "efforts": list(efforts),
        "file": Path("/nonexistent"),
    }


def render(mod, beats):
    buf = io.StringIO()
    with redirect_stdout(buf):
        mod.print_table(beats)
    return buf.getvalue()


class StartupTableStaysSmallTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        self.mod.commits_by_session = lambda limit=60: {}

    def crowded(self):
        live = [beat(self.mod, "aaaa1111", "idle", ["Startup Ideas"]),
                beat(self.mod, "bbbb2222", "ACTIVE", ["AI OS Development"])]
        dead = [beat(self.mod, "dead%04d" % i, "ended", (), age_min=600 + i)
                for i in range(28)]
        return live + dead

    def test_startup_table_fits_on_a_screen(self):
        out = render(self.mod, self.crowded())
        words = len(out.split())
        self.assertLessEqual(
            words, MAX_STARTUP_WORDS,
            f"startup table is {words} words; an agent reads this before the request",
        )

    def test_every_live_session_is_listed(self):
        out = render(self.mod, self.crowded())
        self.assertIn("aaaa1111", out)
        self.assertIn("bbbb2222", out)
        self.assertIn("Startup Ideas", out)

    def test_ended_sessions_are_counted_not_listed(self):
        out = render(self.mod, self.crowded())
        self.assertNotIn("dead0000", out)
        self.assertIn("28", out)

    def test_model_column_is_gone_while_it_reports_unknown(self):
        out = render(self.mod, self.crowded())
        self.assertNotIn("Model", out)
        self.assertNotIn("unknown", out)

    def test_no_heartbeats_still_warns_it_is_not_proof(self):
        out = render(self.mod, [])
        self.assertIn("not proof", out)


if __name__ == "__main__":
    unittest.main()
