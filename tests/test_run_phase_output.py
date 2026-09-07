"""Tests for run.py's phase output handling (real-time vs buffered)."""

import sys

import run as run_module
import sotd.aggregate.run as aggregate_run
import sotd.fetch.community as community


class TestRealtimePhaseOutput:
    def test_community_stdout_is_teered_during_phase(self, monkeypatch, capsys):
        seen = {}

        def fake_main(argv):
            seen["stdout_class"] = type(sys.stdout).__name__
            print("progress: hello", flush=True)
            seen["reached_terminal_during_phase"] = capsys.readouterr().out
            return 0

        monkeypatch.setattr(community, "main", fake_main)
        code, captured = run_module.run_phase("community", ["--month", "2026-08"], debug=False)
        assert code == 0
        # output still lands in the capture buffer for the final summary...
        assert "progress: hello" in captured
        # ...and it reached the real stdout while the phase was running
        assert seen["stdout_class"] == "TeeStdout"
        assert "progress: hello" in seen["reached_terminal_during_phase"]

    def test_aggregate_stdout_stays_buffered(self, monkeypatch, capsys):
        seen = {}

        def fake_main(argv):
            print("aggregate output", flush=True)
            seen["reached_terminal_during_phase"] = capsys.readouterr().out
            return 0

        monkeypatch.setattr(aggregate_run, "main", fake_main)
        code, captured = run_module.run_phase("aggregate", ["--month", "2026-08"], debug=False)
        assert code == 0
        assert "aggregate output" in captured
        # buffered phases print nothing live; output arrives at the end
        assert seen["reached_terminal_during_phase"] == ""
