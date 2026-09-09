#!/usr/bin/env python3
"""Prove the published MCP runner can initialize with an exact Java 21 request."""

import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import tempfile
import time


def runner_coordinate(manifest):
    args = json.loads(Path(manifest).read_text())["mcpServers"]["quarkus-agent"]["args"]
    matches = [arg for arg in args if re.fullmatch(
        r"io\.quarkus:quarkus-agent-mcp:\d+\.\d+\.\d+(?:[-.][\w.-]+)?:runner", arg
    )]
    if len(matches) != 1:
        raise ValueError("Expected one pinned Quarkus Agents MCP runner coordinate")
    return matches[0]


def probe(command, timeout=180, env=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05", "capabilities": {},
        "clientInfo": {"name": "java-floor-check", "version": "1"},
    }}
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=errors, start_new_session=True, env=env)
        try:
            process.stdin.write((json.dumps(request) + "\n").encode())
            process.stdin.flush()
            deadline = time.monotonic() + timeout
            pending = b""
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while time.monotonic() < deadline:
                    if not selector.select(min(0.2, max(0, deadline - time.monotonic()))):
                        continue
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise RuntimeError("MCP exited before initialize completed")
                    pending += chunk
                    if len(pending) > 1024 * 1024:
                        raise RuntimeError("MCP stdout exceeded the response size limit")
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        try:
                            response = json.loads(line)
                        except (ValueError, UnicodeDecodeError):
                            continue
                        if (not isinstance(response, dict) or type(response.get("id")) is not int
                                or response.get("id") != 1):
                            continue
                        result = response.get("result")
                        info = result.get("serverInfo") if isinstance(result, dict) else None
                        if (response.get("jsonrpc") != "2.0" or "error" in response
                                or not isinstance(result, dict)
                                or result.get("protocolVersion") != "2024-11-05"
                                or not isinstance(result.get("capabilities"), dict)
                                or not isinstance(info, dict)
                                or not isinstance(info.get("name"), str) or not info["name"]
                                or not isinstance(info.get("version"), str) or not info["version"]):
                            raise RuntimeError("MCP returned an invalid initialize response")
                        return info
            raise RuntimeError(f"MCP initialize timed out after {timeout:g}s")
        except (RuntimeError, BrokenPipeError) as exc:
            errors.seek(0, os.SEEK_END)
            errors.seek(max(0, errors.tell() - 8000))
            detail = errors.read().decode(errors="replace").strip()
            raise RuntimeError(f"{exc}\n{detail}".rstrip()) from exc
        finally:
            # JBang can spawn Java; stop its whole process group even if the launcher exited.
            process.poll()  # Reap a dead launcher before signalling its process group on macOS.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            process.stdin.close()
            process.stdout.close()


def main():
    manifest = Path(__file__).resolve().parent.parent / "gemini-extension.json"
    coordinate = runner_coordinate(manifest)
    env = {k: v for k, v in os.environ.items() if not k.startswith("JBANG_")
           and k not in {"JAVA_HOME", "JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS"}}
    info = probe(["jbang", "--java", "21", coordinate], env=env)
    print(f"OK: {coordinate} initializes with Java 21 ({info['name']} {info['version']})")


if __name__ == "__main__":
    main()
