#!/usr/bin/env bash
# Fails unless every convention in CLAUDE.md sections 2 to 5 has an audit decision
# in skills/audit-project/SKILL.md: a row in the catalog's "Convention coverage"
# table that names the checks auditing it, or an entry in its "Deliberately not
# audited" list.
#
# A convention is one top-level bullet. Its title is the bold lead ("**CDI-first.**"
# gives "CDI-first"); a bullet without one is titled by its opening words, up to the
# first " (", ";" or end of sentence. Titles match after whitespace is collapsed.
#
# Also fails when a coverage row names a check that no catalog table defines, when a
# row or list entry names a convention that no longer exists or sits in another
# section, or when a convention is both covered and listed as not audited. Together
# these keep the conventions and the audit from drifting apart again (#117).
#
# Usage: ci/check-audit-coverage.sh [conventions-file] [audit-skill-file]
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

conventions="${1:-CLAUDE.md}"
skill="${2:-skills/audit-project/SKILL.md}"

python3 -I - "$conventions" "$skill" <<'PY'
import re
import sys

conventions_path, skill_path = sys.argv[1], sys.argv[2]


def squash(text):
    return re.sub(r"\s+", " ", text).strip()


def convention_titles(path):
    """(section, title) for every top-level bullet in sections 2 to 5."""
    titles, section, bullet = [], None, None

    def flush():
        if bullet is not None and section in {2, 3, 4, 5}:
            titles.append((section, title_of(squash(bullet))))

    for line in open(path, encoding="utf-8").read().splitlines():
        heading = re.match(r"^## (\d+)\.", line)
        if heading or line.startswith(("#", "---")) or not line.strip():
            flush()
            bullet = None
            if heading:
                section = int(heading.group(1))
            continue
        if line.startswith("- "):
            flush()
            bullet = line[2:]
        elif bullet is not None:
            bullet += " " + line.strip()
    flush()
    return titles


def title_of(text):
    if text.startswith("**"):
        title = text[2:text.index("**", 2)]
    else:
        title = re.split(r" \(|;|\. |\.$", text, maxsplit=1)[0]
    return title.rstrip(".").strip()


def table_rows(lines):
    rows = []
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = [squash(c) for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        rows.append(cells)
    return rows


skill_lines = open(skill_path, encoding="utf-8").read().splitlines()
errors = []


def block(start_pattern, stop_pattern, lines):
    out, inside = [], False
    for line in lines:
        if inside and re.match(stop_pattern, line):
            break
        if inside:
            out.append(line)
        elif re.match(start_pattern, line):
            inside = True
    return out


catalog = block(r"^## 5\. ", r"^## ", skill_lines)
coverage = block(r"^#{3,4} .*Convention coverage", r"^#{3,4} ", catalog)
not_audited = block(r"^#{3,4} .*Deliberately not audited", r"^#{2,4} ", catalog)
if not coverage:
    errors.append('no "Convention coverage" table under "## 5." in ' + skill_path)
if not not_audited:
    errors.append('no "Deliberately not audited" list under "## 5." in ' + skill_path)

checks = set()
inside_coverage = False
for line in catalog:
    if re.match(r"^#{3,4} ", line):
        inside_coverage = "Convention coverage" in line
    if not inside_coverage:
        for cells in table_rows([line]):
            if cells[0] != "Check":
                checks.add(cells[0])

expected = {title: section for section, title in convention_titles(conventions_path)}
decided = {}

for cells in table_rows(coverage)[1:]:
    if len(cells) != 3:
        errors.append(f"coverage row needs 3 cells (section | convention | checks): {cells}")
        continue
    section, title, names = cells[0].lstrip("§"), cells[1], cells[2]
    decided.setdefault(title, []).append((section, "coverage table"))
    for name in (n.strip() for n in names.split(";")):
        if name not in checks:
            errors.append(f'coverage row "{title}" names check "{name}", which no catalog table defines')

for line in not_audited:
    entry = re.match(r"^- §(\d+) \*\*(.+?)\*\*", line)
    if entry:
        decided.setdefault(squash(entry.group(2)), []).append((entry.group(1), "not-audited list"))

for title, section in expected.items():
    places = decided.get(title, [])
    if not places:
        errors.append(f'§{section} "{title}" is neither in the coverage table nor in the not-audited list')
    elif len(places) > 1:
        errors.append(f'§{section} "{title}" appears more than once: ' + ", ".join(p for _, p in places))
    elif places[0][0] != str(section):
        errors.append(f'"{title}" is listed under §{places[0][0]}, but the conventions put it in §{section}')

for title in decided:
    if title not in expected:
        errors.append(f'"{title}" is in the audit catalog but is not a convention in §2-§5 of {conventions_path}')

if errors:
    print(f"FAIL: {skill_path} is out of step with the conventions in {conventions_path}.", file=sys.stderr)
    print("      Give every convention in §2-§5 a coverage row or a not-audited entry:", file=sys.stderr)
    for error in errors:
        print("  - " + error, file=sys.stderr)
    sys.exit(1)
print(f"OK: every convention in §2-§5 of {conventions_path} has an audit decision ({len(expected)} conventions)")
PY
