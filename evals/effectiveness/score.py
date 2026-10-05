"""Mechanical convention checks for a project produced by an evaluated agent.

Every check is a source-presence (or absence) predicate derived from the conventions in
CLAUDE.md / AGENTS.md. A check passing is not proof of semantic correctness; it only says the
convention's observable marker is present. All checks have equal weight.
"""
import re
from pathlib import Path

SKIP_DIRS = {'target', '.git', 'node_modules', '.mvn', '.quarkus', '.idea'}

# Strings (text blocks first) are kept; comments are removed, so commented-out code earns nothing.
_JAVA_TOKENS = re.compile(r'"""[\s\S]*?"""|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|//[^\n]*|/\*[\s\S]*?\*/')
_PROP_COMMENT = re.compile(r'(?m)^\s*[#!].*$')
_XML_COMMENT = re.compile(r'<!--[\s\S]*?-->')

GLUE = re.compile(r'\bExecutorService\b|\bCompletableFuture\b|\bExecutors\s*\.|\bStructuredTaskScope\b|'
                  r'\.parallelStream\s*\(|\bparallelBuilder\s*\(')
AI_SERVICE_ARGS = r'@RegisterAiService\s*\((?:[^()]|\([^()]*\))*'


def strip_java(text):
    return _JAVA_TOKENS.sub(lambda m: '' if m[0].startswith(('//', '/*')) else m[0], text)


def _files(root, pattern):
    return sorted(p for p in root.glob(pattern)
                  if p.is_file() and not SKIP_DIRS.intersection(p.relative_to(root).parts))


def find_project(workdir):
    """The project the agent produced: ./app if it has a POM, else the shallowest POM."""
    workdir = Path(workdir)
    if (workdir / 'app' / 'pom.xml').is_file():
        return workdir / 'app'
    poms = [p for p in _files(workdir, '**/pom.xml') if len(p.relative_to(workdir).parts) <= 4]
    poms.sort(key=lambda p: (len(p.parts), str(p)))
    return poms[0].parent if poms else None


class Project:
    def __init__(self, root):
        self.root = Path(root)
        read = lambda p: p.read_text(encoding='utf-8', errors='replace')
        self.java = '\n'.join(strip_java(read(p)) for p in _files(self.root, 'src/main/java/**/*.java'))
        self.test_java = '\n'.join(strip_java(read(p)) for p in _files(self.root, 'src/test/java/**/*.java'))
        props = self.root / 'src/main/resources/application.properties'
        self.props = _PROP_COMMENT.sub('', read(props)) if props.is_file() else ''
        prompt_files = [p for p in _files(self.root, 'src/main/resources/**/*')
                        if p.suffix in ('.txt', '.st', '.prompt', '.md') and 'rag' not in p.parts]
        self.prompt_text = self.java + '\n' + '\n'.join(read(p) for p in prompt_files)
        pom = self.root / 'pom.xml'
        self.pom = _XML_COMMENT.sub('', read(pom)) if pom.is_file() else ''

    def dependencies(self):
        """<dependency> blocks outside <dependencyManagement> and <plugins>."""
        pom = re.sub(r'<dependencyManagement>[\s\S]*?</dependencyManagement>', '', self.pom)
        pom = re.sub(r'<plugins>[\s\S]*?</plugins>', '', pom)
        return re.findall(r'<dependency>[\s\S]*?</dependency>', pom)

    def has_artifact(self, pattern):
        return bool(re.search(r'<artifactId>\s*' + pattern + r'\s*</artifactId>', self.pom))

    def rag_documents(self):
        match = re.search(r'(?m)^\s*(?:%[\w-]+\.)?quarkus\.langchain4j\.easy-rag\.path\s*=\s*(\S+)', self.props)
        candidates = []
        if match:
            value = match.group(1).strip()
            value = re.sub(r'^(?:classpath:|file:)', '', value)
            candidates = [self.root / value, self.root / 'src/main/resources' / value]
            directories = [c for c in candidates if c.is_dir()]
            return any(p.is_file() and p.stat().st_size > 0 for d in directories for p in d.rglob('*'))
        # No Easy RAG path: accept a non-empty Markdown/text document under src/main/resources or
        # under a top-level folder other than src/ (a project-root README does not count).
        for p in _files(self.root, '**/*'):
            parts = p.relative_to(self.root).parts
            if p.suffix not in ('.md', '.txt') or len(parts) < 2 or p.stat().st_size == 0:
                continue
            if parts[0] != 'src' or parts[:3] == ('src', 'main', 'resources'):
                return True
        return False


def _pins(project):
    for block in project.dependencies():
        group = re.search(r'<groupId>\s*([^<\s]+)\s*</groupId>', block)
        if group and re.match(r'(io\.quarkus|io\.quarkiverse|dev\.langchain4j)', group.group(1)) \
                and '<version>' in block:
            return True
    return False


def _release(project):
    values = [int(v) for v in re.findall(r'<(?:maven\.compiler\.release|release)>\s*(\d+)\s*<', project.pom)]
    return bool(values) and min(values) >= 25


CHECKS = {
    # Band D: decided by the agent.
    'ai_service': lambda p: bool(re.search(r'@RegisterAiService\b', p.java)),
    'named_model': lambda p: bool(re.search(AI_SERVICE_ARGS + r'\bmodelName\s*=', p.java)
                                  or re.search(r'@ModelName\s*\(', p.java)),
    'record_dto': lambda p: bool(re.search(r'\brecord\s+\w+\s*[(<]', p.java)),
    'input_guardrail': lambda p: bool(re.search(r'@InputGuardrails\b', p.java)),
    'delimited_input': lambda p: bool(re.search(r'<([A-Za-z][\w-]*)>[\s\S]{0,4000}?</\1>', p.prompt_text)),
    'no_manual_wiring': lambda p: bool(re.search(r'@RegisterAiService\b', p.java))
                                  and not re.search(r'\bAiServices\s*\.\s*(?:builder|create)\s*\(', p.java)
                                  and not re.search(r'\b(?:ChatModel|ChatLanguageModel)\s+\w+\s*[;=,)]', p.java),
    'smoke_test': lambda p: bool(re.search(r'@QuarkusTest\b', p.test_java)),
    'dev_logging': lambda p: bool(re.search(r'(?m)^\s*%dev\.quarkus\.langchain4j\.(?:[\w-]+\.)*log-requests\s*=\s*true\s*$', p.props)),
    'devservices_off': lambda p: bool(re.search(r'(?m)^\s*(?:%[\w-]+\.)?quarkus\.langchain4j\.(?:[\w-]+\.)?devservices\.enabled\s*=\s*false\s*$', p.props)),
    'enum_result': lambda p: bool(re.search(r'\benum\s+\w+', p.java)),
    'zero_temperature': lambda p: bool(re.search(r'(?m)^\s*(?:%[\w-]+\.)?quarkus\.langchain4j\.[\w.-]*temperature\s*=\s*0(?:\.0+)?\s*$', p.props)),
    'virtual_threads': lambda p: bool(re.search(r'@RunOnVirtualThread\b|startVirtualThread\s*\(|'
                                                r'newVirtualThreadPerTaskExecutor\s*\(|Thread\s*\.\s*ofVirtual\s*\(', p.java)),
    'fault_tolerance': lambda p: bool(re.search(r'@Timeout\b', p.java) and re.search(r'@Fallback\b', p.java)),
    'agentic_extension': lambda p: p.has_artifact(r'quarkus-langchain4j-agentic'),
    'agent_annotation': lambda p: bool(re.search(r'@Agent\b', p.java)),
    'parallel_agent': lambda p: bool(re.search(r'@Parallel(?:Mapper)?Agent\b', p.java)),
    'no_executor_glue': lambda p: bool(re.search(r'@Agent\b', p.java)) and not GLUE.search(p.java),
    'easy_rag_extension': lambda p: p.has_artifact(r'quarkus-langchain4j-easy-rag'),
    'easy_rag_path': lambda p: bool(re.search(r'(?m)^\s*(?:%[\w-]+\.)?quarkus\.langchain4j\.easy-rag\.path\s*=\s*\S+', p.props)),
    'embedding_dependency': lambda p: p.has_artifact(r'langchain4j-embeddings-[\w.-]+'),
    'sample_document': lambda p: p.rag_documents(),
    'mcp_server_extension': lambda p: p.has_artifact(r'quarkus-mcp-server-(?:http|sse|stdio)'),
    'mcp_tool': lambda p: bool(re.search(r'import\s+io\.quarkiverse\.mcp\.server\.(?:Tool|\*)\s*;', p.java)
                               and re.search(r'@Tool\b', p.java)
                               or re.search(r'@io\.quarkiverse\.mcp\.server\.Tool\b', p.java)),
    'mcp_tool_arg': lambda p: bool(re.search(r'@(?:io\.quarkiverse\.mcp\.server\.)?ToolArg\b', p.java)),
    'llm_tool': lambda p: bool(re.search(r'import\s+dev\.langchain4j\.agent\.tool\.(?:Tool|\*)\s*;', p.java)
                               and re.search(r'@Tool\b', p.java)
                               or re.search(r'@dev\.langchain4j\.agent\.tool\.Tool\b', p.java)),
    'llm_tools_wired': lambda p: bool(re.search(AI_SERVICE_ARGS + r'\btools\s*=', p.java)
                                      or re.search(r'@ToolBox\s*\(', p.java)),
    'memory_id': lambda p: bool(re.search(r'@MemoryId\b', p.java)),
    # Band G: normally supplied by the project generator (quarkus_create).
    'dual_bom': lambda p: p.has_artifact(r'quarkus-bom') and p.has_artifact(r'quarkus-langchain4j-bom'),
    'no_extension_version_pins': lambda p: bool(p.pom) and not _pins(p),
    'java_release_25': _release,
    'parameters_flag': lambda p: bool(re.search(r'<parameters>\s*true\s*</parameters>|-parameters\b', p.pom)),
    'native_profile': lambda p: bool(re.search(r'<id>\s*native\s*</id>', p.pom)),
}


def score(project_root, names):
    if project_root is None:
        return {name: False for name in names}
    project = Project(project_root)
    return {name: bool(CHECKS[name](project)) for name in names}


def java_file_count(project_root):
    if project_root is None:
        return 0
    return len(_files(Path(project_root), 'src/main/java/**/*.java'))
