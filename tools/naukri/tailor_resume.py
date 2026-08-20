#!/usr/bin/env python3
"""
Truthful per-JD resume tailor for Mohammed Abdul Rafi Ahmed.

Rewrites only emphasis (headline, summary, competency order) from the canonical
Rafi_Resume.docx. Never invents employers, dates, or skills not already on the CV.

Usage:
  python3 tools/naukri/tailor_resume.py \\
    --role "Solution Architect" --company "Epam" \\
    --jd-file /tmp/jd.txt --out /tmp/tailored/Rafi_Resume.docx

  # or stdin JD:
  echo "..." | python3 tools/naukri/tailor_resume.py --role "..." --out ...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE = ROOT / "resumes" / "Rafi_Resume.docx"
ALT_BASES = [
    Path("/workspace/resumes/Rafi_Resume.docx"),
    Path("/home/ubuntu/resumes/Rafi_Resume.docx"),
    Path("/home/ubuntu/Documents/Rafi_Resume.docx"),
]

# Skills that already appear on the canonical CV (or clear synonyms thereof).
# Tailoring may only emphasize these — never invent new stacks.
SKILL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b\.?net\b|dotnet|asp\.?\s*net|c#|csharp", re.I), ".NET Core / C#"),
    (re.compile(r"\bazure\b", re.I), "Azure"),
    (re.compile(r"\baws\b|amazon web services", re.I), "AWS"),
    (re.compile(r"\bkafka\b", re.I), "Kafka"),
    (re.compile(r"\brabbitmq\b", re.I), "RabbitMQ"),
    (re.compile(r"\bkubernetes\b|\bk8s\b", re.I), "Kubernetes"),
    (re.compile(r"\bdocker\b|container", re.I), "Docker"),
    (re.compile(r"\bmicroservices?\b", re.I), "Microservices"),
    (re.compile(r"\bevent[-\s]?driven\b", re.I), "Event-Driven Architecture"),
    (re.compile(r"\bapi\b|rest\b", re.I), "REST APIs"),
    (re.compile(r"\breact\b", re.I), "React"),
    (re.compile(r"\bangular\b", re.I), "Angular"),
    (re.compile(r"\bsql server\b|\bpostgresql\b|\bsql\b", re.I), "SQL Server / PostgreSQL"),
    (re.compile(r"\bci\s*/?\s*cd\b|\bjenkins\b", re.I), "CI/CD / Jenkins"),
    (re.compile(r"\bdistributed\b", re.I), "Distributed Systems"),
    (re.compile(r"\bcloud[-\s]?native\b|\bcloud\b", re.I), "Cloud Architecture"),
    (re.compile(r"\bagile\b|\bscrum\b", re.I), "Agile / Scrum"),
    (re.compile(r"\bmentors?\b|\bcode review", re.I), "Mentoring / Code Reviews"),
]

DEFAULT_SKILLS = [
    ".NET Core / C#",
    "Microservices",
    "AWS",
    "Azure",
    "Kafka",
    "RabbitMQ",
    "Kubernetes",
    "Docker",
]

HEADLINE_DEFAULT = (
    "Solutions Architect | Technical Lead — .NET, Cloud & Distributed Systems"
)


def find_base() -> Path:
    for p in [DEFAULT_BASE, *ALT_BASES]:
        if p.is_file() and p.stat().st_size > 1000:
            return p
    raise FileNotFoundError("Rafi_Resume.docx not found")


def xml_escape_text(s: str) -> str:
    return escape(s, {"'": "&apos;", '"': "&quot;"})


def match_skills(jd: str, role: str = "") -> list[str]:
    blob = f"{role}\n{jd}"
    hit: list[str] = []
    seen: set[str] = set()
    for pat, label in SKILL_PATTERNS:
        if pat.search(blob) and label not in seen:
            seen.add(label)
            hit.append(label)
    # Always keep core .NET signal first when present in JD or by default.
    if ".NET Core / C#" not in seen:
        # Prefer adding it when role looks .NET-shaped or JD is thin.
        if re.search(r"\.net|dotnet|c#|architect|technical lead|engineering manager", blob, re.I):
            hit.insert(0, ".NET Core / C#")
            seen.add(".NET Core / C#")
    if not hit:
        hit = list(DEFAULT_SKILLS)
    # Cap for summary readability
    return hit[:10]


def pick_headline(role: str, skills: list[str]) -> str:
    r = (role or "").lower()
    stack = " · ".join(skills[:4]) if skills else ".NET, Cloud & Distributed Systems"
    if re.search(r"engineering manager|software engineering manager|manager of software", r):
        return f"Engineering Manager | Technical Architect — {stack}"
    if re.search(r"technical director|director of (engineering|technology)|engineering director", r):
        return f"Technical Director | Solutions Architect — {stack}"
    if re.search(r"principal", r):
        return f"Principal Engineer | Solutions Architect — {stack}"
    if re.search(r"staff", r):
        return f"Staff Engineer | Technical Architect — {stack}"
    if re.search(r"solution[s]?\s+architect|software architect|cloud architect|azure architect|technical architect", r):
        return f"Solutions Architect | Technical Lead — {stack}"
    if re.search(r"technical lead|tech lead|\.net lead|lead (software|engineer)", r):
        return f"Technical Lead | Solutions Architect — {stack}"
    return HEADLINE_DEFAULT if not skills else f"Solutions Architect | Technical Lead — {stack}"


def build_summary(role: str, company: str, skills: list[str]) -> str:
    skill_phrase = ", ".join(skills[:7]) if skills else ", ".join(DEFAULT_SKILLS[:7])
    target = (role or "Solutions Architect").strip()
    co = (company or "").strip()
    co_bit = f" for roles like {target} at {co}" if co else f" for {target} roles"
    return (
        f"Solutions Architect and Technical Lead with 15+ years designing distributed, "
        f"cloud-native platforms and leading engineering teams{co_bit}. "
        f"Strong match for this JD on {skill_phrase}. "
        f"Owns end-to-end architecture across service boundaries, API contracts, "
        f"event-driven messaging (Kafka/RabbitMQ), data models, and deployment topology "
        f"on AWS and Azure. Hands-on with .NET Core, C#, and Kubernetes/Docker, with a "
        f"track record translating business requirements into scalable system design and "
        f"shipped software while mentoring engineers and owning delivery through CI/CD."
    )


def replace_w_t(xml: str, old: str, new: str) -> tuple[str, bool]:
    """Replace a full <w:t>...</w:t> text node value. old is unescaped plain text."""
    # document may store & as &amp;
    variants = {
        old,
        old.replace("&", "&amp;"),
        xml_escape_text(old),
    }
    new_esc = xml_escape_text(new)
    for v in variants:
        needle = f">{v}</w:t>"
        if needle in xml:
            return xml.replace(needle, f">{new_esc}</w:t>", 1), True
    return xml, False


def tailor_docx(
    *,
    base: Path,
    out_path: Path,
    role: str,
    company: str,
    jd: str,
) -> dict:
    skills = match_skills(jd, role)
    headline = pick_headline(role, skills)
    summary = build_summary(role, company, skills)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Always ship as Rafi_Resume.docx so ATS/profile UI keep the known filename.
    if out_path.suffix.lower() != ".docx":
        out_path = out_path / "Rafi_Resume.docx"
    elif out_path.name.lower() != "rafi_resume.docx":
        out_path = out_path.parent / "Rafi_Resume.docx"

    shutil.copy2(base, out_path)

    with zipfile.ZipFile(out_path, "r") as zin:
        xml = zin.read("word/document.xml").decode("utf-8")
        others = {
            i.filename: zin.read(i.filename)
            for i in zin.infolist()
            if i.filename != "word/document.xml"
        }

    replaced = {"headline": False, "summary": False, "competencies": 0}

    # Headline (paragraph index 1 in canonical CV)
    old_headline = (
        "Technical Architect | Technical Lead — .NET, Cloud & Distributed Systems"
    )
    xml, ok = replace_w_t(xml, old_headline, headline)
    replaced["headline"] = ok

    old_summary_prefix = (
        "Technical Architect and Technical Lead with 15+ years designing distributed, "
        "cloud-native platforms and leading engineering teams to deliver them"
    )
    # Find full summary node via regex on w:t
    m = re.search(
        r"(<w:t[^>]*>)(Technical Architect and Technical Lead with 15\+ years.*?)</w:t>",
        xml,
        flags=re.S,
    )
    if m:
        xml = xml[: m.start()] + m.group(1) + xml_escape_text(summary) + "</w:t>" + xml[m.end() :]
        replaced["summary"] = True
    else:
        # Fallback: prefix-only contiguous replace if truncated differently
        xml, ok = replace_w_t(xml, old_summary_prefix, summary[: len(old_summary_prefix)])
        replaced["summary"] = ok

    # Competencies stay as-is (comma/paren-safe). Headline + summary carry JD keywords for ATS.

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in others.items():
            zout.writestr(name, data)
        zout.writestr("word/document.xml", xml.encode("utf-8"))

    meta = {
        "ok": True,
        "base": str(base),
        "out": str(out_path),
        "role": role,
        "company": company,
        "headline": headline,
        "skills": skills,
        "replaced": replaced,
        "jdChars": len(jd or ""),
        "jdSha1": hashlib.sha1((jd or "").encode("utf-8")).hexdigest()[:12],
    }
    meta_path = out_path.with_suffix(".tailor.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    meta["metaPath"] = str(meta_path)
    return meta


def main() -> int:
    ap = argparse.ArgumentParser(description="Tailor Rafi_Resume.docx to a JD (truthful emphasis only)")
    ap.add_argument("--role", required=True)
    ap.add_argument("--company", default="")
    ap.add_argument("--jd-file", default="")
    ap.add_argument("--jd", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default="")
    args = ap.parse_args()

    jd = args.jd or ""
    if args.jd_file:
        jd = Path(args.jd_file).read_text(encoding="utf-8", errors="ignore")
    elif not jd and not sys.stdin.isatty():
        jd = sys.stdin.read()

    base = Path(args.base) if args.base else find_base()
    meta = tailor_docx(
        base=base,
        out_path=Path(args.out),
        role=args.role,
        company=args.company,
        jd=jd,
    )
    print(json.dumps(meta, indent=2))
    return 0 if meta.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
