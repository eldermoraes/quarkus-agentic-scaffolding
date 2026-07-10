#!/usr/bin/env bash
#
# build-from-templates.sh — static template validation (VALIDATING-TEMPLATES.md fallback,
# scripted). Generates a throwaway Quarkus project via the quarkus-maven-plugin (the same
# codestart generator behind quarkus_create / code.quarkus.io), materializes EVERY template
# by convention, injects the non-extension deps from pom.xml.template, removes easy-rag
# (compile-only run needs no embedding model), and runs `mvn test-compile`.
#
# Usage: ci/build-from-templates.sh [PLATFORM_VERSION]
#   No argument: resolves the latest io.quarkus.platform version from Maven Central.
# Env: WORKDIR (optional) — where the throwaway project is generated.
# Requires: python3 (materializes the templates and injects the pom deps), Maven,
#   a JDK 25+, and curl (only when PLATFORM_VERSION is resolved from Maven Central).
#
# Template conventions this script relies on (keep new templates compliant):
#   - *.java.template containing '/* ===== File: <rel/path>.java ===== */' markers is split
#     into one file per marker; the destination package dir comes from each section's own
#     `package` declaration.
#   - any other *.java.template is a single file named after its public type; types whose
#     name ends in "Test" land in src/test/java, everything else in src/main/java.
#   - application.properties.template -> src/main/resources/application.properties.
#   - pom.xml.template is a dependency reference: every <dependency> in it (comments
#     stripped) is injected into the generated pom before </dependencies>.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATES="$REPO_ROOT/skills/quarkus-langchain4j-scaffolding/templates"
EXTENSIONS="rest,rest-jackson,smallrye-openapi,websockets-next,langchain4j-ollama,langchain4j-agentic,langchain4j-easy-rag"

PLATFORM_VERSION="${1:-}"
if [[ -z "$PLATFORM_VERSION" ]]; then
  PLATFORM_VERSION="$(curl -fsSL https://repo1.maven.org/maven2/io/quarkus/platform/quarkus-bom/maven-metadata.xml \
    | sed -n 's:.*<latest>\(.*\)</latest>.*:\1:p')"
fi
[[ -n "$PLATFORM_VERSION" ]] || { echo "ERROR: could not resolve latest platform version" >&2; exit 1; }
echo "==> Validating templates against Quarkus platform $PLATFORM_VERSION"

WORKDIR="${WORKDIR:-$(mktemp -d)}"
mkdir -p "$WORKDIR"
cd "$WORKDIR"
rm -rf ql4j-validate

mvn -B -ntp "io.quarkus.platform:quarkus-maven-plugin:${PLATFORM_VERSION}:create" \
  -DprojectGroupId=org.acme -DprojectArtifactId=ql4j-validate \
  -DplatformGroupId=io.quarkus.platform -DplatformVersion="$PLATFORM_VERSION" \
  -Dextensions="$EXTENSIONS" -DnoCode
cd ql4j-validate

python3 - "$TEMPLATES" <<'PY'
import pathlib, re, sys

templates = pathlib.Path(sys.argv[1])
proj = pathlib.Path(".")
MARKER = re.compile(r"/\*\s*=+\s*File:\s*(\S+)\s*=+\s*\*/")
PKG = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.M)
TYPE = re.compile(r"(?:class|interface|enum|record)\s+(\w+)")

def write(root, pkg, filename, body):
    d = proj / root / pkg.replace(".", "/")
    d.mkdir(parents=True, exist_ok=True)
    (d / filename).write_text(body.strip() + "\n")
    print(f"materialized {root}/{pkg.replace('.', '/')}/{filename}")

for tpl in sorted(templates.glob("*.java.template")):
    text = tpl.read_text()
    parts = MARKER.split(text)
    if len(parts) > 1:  # multi-file template; parts[0] is the header comment, dropped
        for relpath, body in zip(parts[1::2], parts[2::2]):
            pkg = PKG.search(body)
            if not pkg:
                sys.exit(f"ERROR: no package declaration in section {relpath} of {tpl.name}")
            name = pathlib.PurePosixPath(relpath).name
            root = "src/test/java" if name.endswith("Test.java") else "src/main/java"
            write(root, pkg.group(1), name, body)
    else:
        pkg, typ = PKG.search(text), TYPE.search(text)
        if not (pkg and typ):
            sys.exit(f"ERROR: cannot derive package/type from {tpl.name}")
        root = "src/test/java" if typ.group(1).endswith("Test") else "src/main/java"
        write(root, pkg.group(1), typ.group(1) + ".java", text)

props = templates / "application.properties.template"
res = proj / "src/main/resources"
res.mkdir(parents=True, exist_ok=True)
(res / "application.properties").write_text(props.read_text())
print("materialized src/main/resources/application.properties")

# Inject non-extension deps from pom.xml.template (comments stripped first),
# then drop easy-rag from the generated pom (needs no embedding model to compile).
ref = re.sub(r"<!--.*?-->", "", (templates / "pom.xml.template").read_text(), flags=re.S)
deps = re.findall(r"<dependency>.*?</dependency>", ref, flags=re.S)
dep_ids = re.findall(r"<artifactId>\s*([\w.\-]+)\s*</artifactId>", "\n".join(deps))
pom_path = proj / "pom.xml"
pom = pom_path.read_text()

# Drop easy-rag from the generated pom; report it only if the regex matched.
pom, n_removed = re.subn(
    r"\s*<dependency>(?:(?!</dependency>).)*quarkus-langchain4j-easy-rag(?:(?!</dependency>).)*</dependency>",
    "", pom, flags=re.S)

# Inject into the RUNTIME <dependencies>, NOT <dependencyManagement>'s BOM block.
# The FIRST </dependencies> in a Quarkus pom closes <dependencyManagement><dependencies>
# (the BOM imports), so anchoring there makes the version-less deps inert. Anchor to the
# LAST </dependencies> (the runtime block) instead.
cut = pom.rfind("</dependencies>")
if cut == -1:
    sys.exit("ERROR: no </dependencies> found in generated pom.xml")
pom = pom[:cut] + "    " + "\n    ".join(deps) + "\n    " + pom[cut:]
pom_path.write_text(pom)

# Verify each injected artifactId actually landed in the runtime block, i.e. AFTER
# </dependencyManagement> — a real check, not presence-only. Fail loudly otherwise.
written = pom_path.read_text()
dm_end = written.rfind("</dependencyManagement>")
runtime = written[dm_end:] if dm_end != -1 else written
missing = [a for a in dep_ids if a not in runtime]
if missing:
    sys.exit("ERROR: injected deps did not land in the runtime <dependencies> block "
             f"(after </dependencyManagement>): {', '.join(missing)}")

if n_removed:
    print("removed easy-rag")
print(f"injected {len(deps)} non-extension dependencies")
PY

mvn -B -ntp -DskipTests test-compile
echo "==> OK: templates compile against platform $PLATFORM_VERSION"
