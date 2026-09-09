"""Probe documentation tools before spending the agent execution budget."""
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time


class PreflightError(RuntimeError):
    pass


def probe(command, tool, arguments, env, timeout=90):
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, env=env, start_new_session=True)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    pending = b''
    deadline = time.monotonic() + timeout

    def send(message):
        process.stdin.write(json.dumps(message) + '\n')
        process.stdin.flush()

    def receive(identifier):
        nonlocal pending
        while time.monotonic() < deadline:
            if b'\n' not in pending:
                if not selector.select(max(0, deadline-time.monotonic())):
                    break
                chunk = os.read(process.stdout.fileno(), 4096)
                if not chunk:
                    raise PreflightError(f'{tool}: MCP process closed')
                pending += chunk
                if len(pending) > 1024 * 1024:
                    raise PreflightError(f'{tool}: oversized MCP response')
                continue
            line, pending = pending.split(b'\n', 1)
            try:
                message = json.loads(line)
            except ValueError:
                continue
            if message.get('id') == identifier:
                if 'error' in message:
                    raise PreflightError(f'{tool}: JSON-RPC error')
                return message.get('result', {})
        raise PreflightError(f'{tool}: documentation probe timed out')

    try:
        send({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
            'protocolVersion': '2024-11-05', 'capabilities': {},
            'clientInfo': {'name': 'skill-pilot-preflight', 'version': '1'}}})
        receive(1)
        send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        send({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
              'params': {'name': tool, 'arguments': arguments}})
        result = receive(2)
        content = '\n'.join(item.get('text', '') for item in result.get('content', []))
        lower = content.lower()
        if 'docker' in lower and ('unavailable' in lower or 'neither' in lower):
            raise PreflightError('Quarkus documentation requires an available Docker/Podman runtime')
        if 'quota exceeded' in lower or 'rate limit' in lower:
            raise PreflightError('Documentation quota/rate limit reached; restore access before collecting')
        if result.get('isError') or not content.strip():
            raise PreflightError(f'{tool}: documentation probe returned an error or empty response')
    finally:
        process.poll()
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        process.stdin.close()
        selector.close()
        process.stdout.close()


def check(project, env):
    probe(['jbang', '--java', '21+', 'io.quarkus:quarkus-agent-mcp:1.2.6:runner'],
          'quarkus_searchDocs', {'projectDir': str(Path(project).resolve()),
                                'query': 'REST', 'maxResults': 1}, env)
    probe(['npx', '-y', '@upstash/context7-mcp@4.0.6'], 'query-docs',
          {'libraryId': '/langchain4j/langchain4j', 'query': 'RegisterAiService interface'}, env)
