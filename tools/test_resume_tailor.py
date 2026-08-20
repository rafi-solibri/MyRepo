#!/usr/bin/env python3
"""Unit tests for JD-aware resume tailoring."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.resume_paths import (  # noqa: E402
    clear_active_resume,
    resume_upload_path,
    set_active_resume,
)
from tools.resume_tailor import (  # noqa: E402
    extract_jd_skills,
    preferred_headline,
    preferred_summary,
    tailor_document,
    tailor_resume_for_job,
)


CANON = _ROOT / "resumes" / "Rafi_Resume.docx"


@pytest.fixture(autouse=True)
def _clear_active():
    clear_active_resume()
    yield
    clear_active_resume()


def test_extract_jd_skills_prefers_owned_stack():
    jd = """
    We need a Solution Architect with strong Azure, .NET Core, Kafka, and Kubernetes.
    Nice to have Salesforce and Java (not required for this role description dump).
    """
    skills = extract_jd_skills(jd, title="Solution Architect - Azure")
    assert ".NET Core" in skills
    assert "Azure" in skills
    assert "Kafka" in skills
    assert "Kubernetes" in skills
    # Must not invent non-owned stacks as matched owned skills
    assert "Salesforce" not in skills
    assert "Java" not in skills


def test_headline_and_summary_truthful():
    matched = [".NET Core", "Azure", "Kafka", "Kubernetes"]
    h = preferred_headline("Senior Solution Architect", matched)
    assert "Architect" in h
    assert "Azure" in h or ".NET" in h
    s = preferred_summary("Solution Architect", "Acme Corp", matched)
    assert "15+" in s
    assert "Azure" in s
    assert "Acme" in s
    # No fabricated employer history
    assert "Google" not in s
    assert "FAANG" not in s


def test_tailor_document_rewrites_and_keeps_employers(tmp_path: Path):
    pytest.importorskip("docx")
    if not CANON.is_file():
        pytest.skip("canonical resume missing")
    dest = tmp_path / "Rafi_Resume.docx"
    jd = "Azure Solution Architect .NET Core microservices Kafka Kubernetes CI/CD"
    meta = tailor_document(
        CANON,
        dest,
        title="Azure Solution Architect",
        company="Contoso",
        jd=jd,
    )
    assert dest.is_file() and dest.stat().st_size > 1000
    assert "Azure" in meta["matched_skills"] or ".NET Core" in meta["matched_skills"]

    from docx import Document

    doc = Document(str(dest))
    texts = [p.text for p in doc.paragraphs if p.text.strip()]
    blob = "\n".join(texts)
    assert "MOHAMMED ABDUL RAFI AHMED" in blob
    assert "Nemetschek" in blob
    assert "UnitedHealth" in blob
    assert "Acharya Nagarjuna" in blob or "Nagarjuna" in blob
    # Tailored bits present
    assert "Architect" in texts[1]
    assert "15+" in texts[3] or "15+" in texts[4]


def test_active_resume_override(tmp_path: Path):
    pytest.importorskip("docx")
    if not CANON.is_file():
        pytest.skip("canonical resume missing")
    dest = tmp_path / "Rafi_Resume.docx"
    tailor_document(CANON, dest, title="Technical Lead", company="X", jd=".NET Azure")
    set_active_resume(dest)
    assert Path(resume_upload_path()).resolve() == dest.resolve()
    clear_active_resume()
    assert Path(resume_upload_path()).name == "Rafi_Resume.docx"


def test_tailor_disabled_returns_canonical(monkeypatch, tmp_path: Path):
    if not CANON.is_file():
        pytest.skip("canonical resume missing")
    monkeypatch.setenv("RESUME_TAILOR", "0")
    monkeypatch.setenv("LINKEDIN_ARTIFACTS", str(tmp_path))
    p = tailor_resume_for_job(job_id="1", title="Architect", company="Y", jd="Azure .NET")
    assert p.name == "Rafi_Resume.docx"
    # Disabled path should not create tailored-resumes children for this call
    assert not list(tmp_path.glob("tailored-resumes/**/*.docx"))


def test_tailor_resume_for_job_writes_labeled_docx(tmp_path: Path, monkeypatch):
    pytest.importorskip("docx")
    if not CANON.is_file():
        pytest.skip("canonical resume missing")
    monkeypatch.delenv("RESUME_TAILOR", raising=False)
    monkeypatch.setenv("LINKEDIN_ARTIFACTS", str(tmp_path))
    p = tailor_resume_for_job(
        job_id="4450898539",
        title="Technical Architect",
        company="Example",
        jd="Looking for .NET Core, Azure, microservices, Kafka experience",
    )
    assert p.name == "Rafi_Resume.docx"
    assert p.is_file()
    assert "tailored-resumes" in str(p)
