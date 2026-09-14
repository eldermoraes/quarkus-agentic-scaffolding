import errno
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, call, patch

from check_mcp_java_floor import _stop_process_group, probe, runner_coordinate


class JavaFloorTest(unittest.TestCase):
    def command(self, response, wait=False):
        program = "import sys,time; sys.stdin.readline(); "
        program += f"print({json.dumps(json.dumps(response))}, flush=True); "
        if wait:
            program += "time.sleep(30)"
        return [sys.executable, "-u", "-c", program]

    def test_valid_initialize(self):
        info = {"name": "quarkus-agent", "version": "fixture"}
        result = {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": info}
        self.assertEqual(probe(self.command({"jsonrpc": "2.0", "id": 1, "result": result}, True), 2), info)

    def test_false_positive_responses_fail(self):
        for response in ({"jsonrpc": "2.0", "id": 1, "error": {"code": -1}},
                         {"jsonrpc": "2.0", "id": 1, "result": {}},
                         {"jsonrpc": "2.0", "id": 99, "result": {}}, ["not a response"]):
            with self.subTest(response=response), self.assertRaises(RuntimeError):
                probe(self.command(response), 1)

    def test_early_exit_reports_stderr(self):
        with self.assertRaisesRegex(RuntimeError, "fixture startup failure"):
            probe([sys.executable, "-c", "import sys; print('fixture startup failure', file=sys.stderr)"], 1)

    def test_permission_denial_remains_visible(self):
        for state in ("live", "existing-group", "denied-group"):
            with self.subTest(state=state):
                process = Mock(pid=12345)
                process.poll.return_value = None if state == "live" else 0
                denied = PermissionError(errno.EPERM, "fixture permission denied")
                check = denied if state == "denied-group" else None
                with patch("check_mcp_java_floor.os.killpg", side_effect=[denied, check]) as killpg:
                    with self.assertRaises(PermissionError) as raised:
                        _stop_process_group(process)
                self.assertIs(raised.exception, denied)
                expected = [call(process.pid, signal.SIGKILL)]
                if state != "live":
                    expected.append(call(process.pid, 0))
                self.assertEqual(killpg.call_args_list, expected)
                process.wait.assert_not_called()

    def test_only_disappeared_group_allows_permission_recovery(self):
        process = Mock(pid=12345)
        process.poll.return_value = 0
        operations = Mock()
        operations.attach_mock(process, "process")
        with patch("check_mcp_java_floor.os.killpg", side_effect=[
                PermissionError(errno.EPERM, "fixture zombie"),
                ProcessLookupError(errno.ESRCH, "fixture group gone")]) as killpg:
            operations.attach_mock(killpg, "killpg")
            _stop_process_group(process)
        self.assertEqual(operations.mock_calls, [
            call.killpg(process.pid, signal.SIGKILL),
            call.process.poll(),
            call.killpg(process.pid, 0),
            call.process.wait(),
        ])

    def test_group_signal_precedes_reaping(self):
        for outcome in (None, ProcessLookupError(errno.ESRCH, "fixture group gone")):
            with self.subTest(outcome=outcome):
                process = Mock(pid=12345)
                operations = Mock()
                operations.attach_mock(process, "process")
                with patch("check_mcp_java_floor.os.killpg", side_effect=[outcome]) as killpg:
                    operations.attach_mock(killpg, "killpg")
                    _stop_process_group(process)
                self.assertEqual(operations.mock_calls, [
                    call.killpg(process.pid, signal.SIGKILL), call.process.wait(),
                ])

    def test_cleanup_denial_closes_pipes_and_preserves_startup_error(self):
        popen = subprocess.Popen
        for valid in (False, True):
            with self.subTest(valid=valid):
                processes = []

                def spawn(*args, **kwargs):
                    process = popen(*args, **kwargs)
                    processes.append(process)
                    return process

                info = {"name": "fixture", "version": "1"}
                result = {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": info}
                response = {"jsonrpc": "2.0", "id": 1, "result": result if valid else {}}
                command = self.command(response)
                command[-1] += "import select; select.select([sys.stdin],[],[],3)"
                denied = PermissionError(errno.EPERM, "fixture permission denied")
                try:
                    with patch("check_mcp_java_floor.subprocess.Popen", side_effect=spawn), \
                            patch("check_mcp_java_floor.os.killpg", side_effect=denied) as killpg:
                        with self.assertRaises(PermissionError) as raised:
                            probe(command, 1)
                    self.assertIs(raised.exception, denied)
                    if not valid:
                        self.assertIsInstance(denied.__context__, RuntimeError)
                        self.assertIn("invalid initialize response", str(denied.__context__))
                    killpg.assert_called_once_with(processes[0].pid, signal.SIGKILL)
                    self.assertTrue(processes[0].stdin.closed)
                    self.assertTrue(processes[0].stdout.closed)
                finally:
                    for process in processes:
                        process.stdin.close()
                        process.stdout.close()
                        process.wait(timeout=4)

    def test_broken_request_pipe_does_not_mask_errors_during_close(self):
        for cleanup_denied, buffering in ((False, -1), (True, -1), (False, 0), (True, 0)):
            with self.subTest(cleanup_denied=cleanup_denied, buffering=buffering):
                read_fd, write_fd = os.pipe()
                os.close(read_fd)
                with os.fdopen(write_fd, "wb", buffering=buffering) as stdin, io.BytesIO() as stdout:
                    process = Mock(pid=12345, stdin=stdin, stdout=stdout)
                    process.poll.return_value = None
                    denied = PermissionError(errno.EPERM, "fixture permission denied")
                    expected = PermissionError if cleanup_denied else RuntimeError
                    with patch("check_mcp_java_floor.subprocess.Popen", return_value=process), \
                            patch("check_mcp_java_floor.os.killpg",
                                  side_effect=denied if cleanup_denied else None):
                        with self.assertRaises(expected) as raised:
                            probe(["unused-fixture"], 1)
                    startup_error = raised.exception
                    if cleanup_denied:
                        self.assertIs(startup_error, denied)
                        startup_error = denied.__context__
                    self.assertIsInstance(startup_error, RuntimeError)
                    self.assertIsInstance(startup_error.__cause__, BrokenPipeError)
                    self.assertTrue(stdin.closed)
                    self.assertTrue(stdout.closed)

    @unittest.skipUnless(sys.platform == "darwin" and hasattr(os, "waitid"),
                         "Exercises macOS killpg on an unreaped process")
    def test_exit_between_poll_and_group_signal(self):
        popen = subprocess.Popen
        killpg = os.killpg
        processes = []
        denied = []

        def spawn(*args, **kwargs):
            process = popen(*args, **kwargs)
            processes.append(process)
            return process

        def exit_before_signal(pgid, sig):
            process = processes[0]
            self.assertEqual(pgid, process.pid)
            if sig == signal.SIGKILL:
                self.assertEqual(os.getpgid(process.pid), process.pid)
                self.assertEqual(os.getsid(process.pid), process.pid)
                self.assertIsNone(process.poll())
                process.stdin.write(b"exit\n")
                process.stdin.flush()
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    event = os.waitid(os.P_PID, process.pid,
                                      os.WEXITED | os.WNOWAIT | os.WNOHANG)
                    if event is not None:
                        self.assertEqual(event.si_status, 0)
                        break
                    time.sleep(0.001)
                else:
                    self.fail("fixture did not exit without being reaped")
            try:
                return killpg(pgid, sig)
            except PermissionError:
                denied.append(sig)
                raise

        program = ("import os,select,sys; sys.stdin.readline(); os.close(1); "
                   "select.select([sys.stdin],[],[],3)")
        try:
            with patch("check_mcp_java_floor.subprocess.Popen", side_effect=spawn), \
                    patch("check_mcp_java_floor.os.killpg", side_effect=exit_before_signal):
                with self.assertRaisesRegex(RuntimeError, "MCP exited before initialize completed"):
                    probe([sys.executable, "-u", "-c", program], 1)
            self.assertEqual(denied, [signal.SIGKILL])
            self.assertEqual(processes[0].returncode, 0)
            self.assertTrue(processes[0].stdin.closed)
            self.assertTrue(processes[0].stdout.closed)
        finally:
            for process in processes:
                process.wait(timeout=4)
                process.stdin.close()
                process.stdout.close()

    @unittest.skipUnless(hasattr(os, "waitid") and hasattr(os, "WNOWAIT"),
                         "Requires non-reaping exit observation")
    def test_exited_launcher_does_not_leave_descendant_running(self):
        killpg = os.killpg
        popen = subprocess.Popen
        processes = []

        def spawn(*args, **kwargs):
            process = popen(*args, **kwargs)
            processes.append(process)
            return process

        with tempfile.TemporaryDirectory() as directory:
            pidfile = Path(directory) / "pid"
            response = {"jsonrpc": "2.0", "id": 1, "result": {
                "protocolVersion": "2024-11-05", "capabilities": {},
                "serverInfo": {"name": "fixture", "version": "1"},
            }}
            script = (
                "import select,subprocess,sys; sys.stdin.readline(); "
                "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                f"open({str(pidfile)!r},'w').write(str(child.pid)); "
                f"print({json.dumps(json.dumps(response))},flush=True); "
                "select.select([sys.stdin],[],[],3)"
            )
            signals = []

            def signal_after_launcher_exit(pgid, sig):
                self.assertEqual(sig, signal.SIGKILL)
                process = processes[0]
                self.assertEqual(pgid, process.pid)
                self.assertIsNone(process.poll())
                self.assertEqual(os.getpgid(pgid), pgid)
                self.assertEqual(os.getsid(pgid), pgid)
                self.assertEqual(os.getpgid(int(pidfile.read_text())), pgid)
                process.stdin.write(b"exit\n")
                process.stdin.flush()
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    event = os.waitid(os.P_PID, pgid, os.WEXITED | os.WNOWAIT | os.WNOHANG)
                    if event is not None:
                        self.assertEqual(event.si_status, 0)
                        break
                    time.sleep(0.001)
                else:
                    self.fail("launcher did not exit")
                self.assertEqual(os.getpgid(int(pidfile.read_text())), pgid)
                signals.append(sig)
                return killpg(pgid, sig)

            with patch("check_mcp_java_floor.subprocess.Popen", side_effect=spawn), \
                    patch("check_mcp_java_floor.os.killpg", side_effect=signal_after_launcher_exit):
                self.assertEqual(probe([sys.executable, "-u", "-c", script], 2),
                                 response["result"]["serverInfo"])
            self.assertEqual(signals, [signal.SIGKILL])
            self.assert_process_stopped(pidfile.read_text())

    def test_timeout_cleans_up_child_process(self):
        with tempfile.TemporaryDirectory() as directory:
            pidfile = Path(directory) / "pid"
            script = ("import subprocess,sys,time; sys.stdin.readline(); "
                      "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                      f"open({str(pidfile)!r},'w').write(str(child.pid)); time.sleep(30)")
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                probe([sys.executable, "-c", script], 5)
            self.assertTrue(pidfile.exists(), "fixture did not become ready within 5 seconds")
            self.assert_process_stopped(pidfile.read_text())

    def assert_process_stopped(self, pid):
        # A killed child may briefly remain a zombie until the OS reaps it.
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            result = subprocess.run(["ps", "-o", "stat=", "-p", pid],
                                    capture_output=True, text=True)
            if not result.stdout.strip() or result.stdout.strip().startswith("Z"):
                return
            time.sleep(0.05)
        self.fail("MCP child process survived cleanup")

    def test_coordinate_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            for coordinate, valid in (("io.quarkus:quarkus-agent-mcp:1.2.6:runner", True),
                                      ("https://example.com/code.java", False)):
                manifest.write_text(json.dumps({"mcpServers": {"quarkus-agent": {"args": [coordinate]}}}))
                if valid:
                    self.assertEqual(runner_coordinate(manifest), coordinate)
                else:
                    with self.assertRaises(ValueError):
                        runner_coordinate(manifest)
