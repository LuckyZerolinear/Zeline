"""Contract tests for mid-turn steer classification.

`classify_steer` decides whether a message the user sends *while a task is
still running* interrupts that task (it is cancelled and held) or is merely
absorbed as guidance. Getting it wrong in the interrupt direction is the
expensive failure: the running task is killed for a message that only added
detail.

These tests pin the awkward cases that a bare keyword list got wrong:

- "buatin tombol skip di modal" -- "skip" is a *button name*, not an order,
  so it must not interrupt.
- "jangan lupa tambahin test" -- polite filler, not a stop command.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))


def _store():
    os.environ["ZELINE_HOME"] = tempfile.mkdtemp()
    import importlib

    import zeline.sessions as sessions

    importlib.reload(sessions)
    return sessions.SessionStore()


class ClassifySteerTests(unittest.TestCase):
    def setUp(self):
        self.store = _store()

    def assertSteer(self, text):
        self.assertFalse(
            self.store.classify_steer(text),
            f"expected steer (do NOT interrupt the running task): {text!r}",
        )

    def assertUrgent(self, text):
        self.assertTrue(
            self.store.classify_steer(text),
            f"expected urgent (interrupt the running task): {text!r}",
        )

    # --- words that are always commands -------------------------------------

    def test_unambiguous_stop_words_are_urgent(self):
        for text in ("stop", "berhenti dulu", "batal", "tunggu dulu", "urgent"):
            with self.subTest(text=text):
                self.assertUrgent(text)

    # --- "skip" as a button/feature name must not interrupt ----------------

    def test_skip_as_noun_does_not_interrupt(self):
        for text in (
            "buatin tombol skip di modal",
            "buatin fitur skip login",
            "tambahin tombol skip di form",
        ):
            with self.subTest(text=text):
                self.assertSteer(text)

    def test_skip_as_command_interrupts(self):
        for text in (
            "skip bagian login",
            "tolong skip yang tadi",
            "gak usah, skip aja bagian itu",
            "oke langsung skip bagian itu",
        ):
            with self.subTest(text=text):
                self.assertUrgent(text)

    # --- polite filler containing a stop-looking word -----------------------

    def test_politeness_filler_does_not_interrupt(self):
        for text in (
            "jangan lupa tambahin test",
            "jangan sampai lupa update changelog",
        ):
            with self.subTest(text=text):
                self.assertSteer(text)

    # --- ordinary refinements stay steer -----------------------------------

    def test_refinements_stay_steer(self):
        for text in (
            "tambahin border merah",
            "btw harga eth berapa",
        ):
            with self.subTest(text=text):
                self.assertSteer(text)

    # --- real redirects still interrupt ------------------------------------

    def test_redirects_interrupt(self):
        for text in ("jangan lanjutin, salah arah", "koreksi dikit, bagian footer"):
            with self.subTest(text=text):
                self.assertUrgent(text)


if __name__ == "__main__":
    unittest.main()
