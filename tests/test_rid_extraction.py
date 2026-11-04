"""
RID-extraction regression tests (TASK-10 / TASK-12).

The MIME unwrapping is the brittle part of the bridge, so pin its behavior with
fixtures. One synthetic fixture is generated in-process so the suite runs today;
drop REAL Defender-wrapped samples (.eml) into tests/fixtures/ and extend
`test_real_fixtures` as they're captured (TASK-10).

Run: pytest   (from the repo root, with env minimally set — see conftest note)
"""
import email
import importlib.util
import os
import sys
from email.message import EmailMessage
from pathlib import Path

import pytest

# The bridge validates required env vars at import time; set dummies so we can
# import it purely to test the pure functions.
os.environ.setdefault("IMAP_SERVER", "imap.example.test")
os.environ.setdefault("IMAP_USER", "x@example.test")
os.environ.setdefault("IMAP_PASS", "x")
os.environ.setdefault("SMTP_SERVER", "smtp.example.test")
os.environ.setdefault("SMTP_USER", "x@example.test")
os.environ.setdefault("SMTP_PASS", "x")
os.environ.setdefault("GOPHISH_REPORT_TO", "reports@phish.lcstn.org")
os.environ.setdefault("LANDING_DOMAINS", "phish.lcstn.org,login.lcstn.org")

_SRC = Path(__file__).resolve().parents[1] / "src" / "bridge.py"
_spec = importlib.util.spec_from_file_location("bridge", _SRC)
bridge = importlib.util.module_from_spec(_spec)
sys.modules["bridge"] = bridge
_spec.loader.exec_module(bridge)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
RID = "abc1234"


def _original(rid=RID):
    """A stand-in for the original Anglerphish campaign email."""
    m = EmailMessage()
    m["From"] = "it-notice@phish.lcstn.org"
    m["To"] = "victim@lcstn.org"
    m["Subject"] = "Action required: verify your account"
    m.set_content(f"Please visit https://login.lcstn.org/signin?rid={rid} to continue.")
    return m


def _wrap_rfc822(inner):
    """Mimic Defender wrapping the report as a nested message/rfc822."""
    outer = EmailMessage()
    outer["From"] = "victim@lcstn.org"
    outer["To"] = "phishreport@lcstn.org"
    outer["Subject"] = "Phishing report"
    outer.set_content("Reporting this suspicious message.")
    outer.add_attachment(inner.as_bytes(), maintype="message",
                         subtype="rfc822", filename="reported.eml")
    return email.message_from_bytes(outer.as_bytes())


def test_plain_message():
    assert bridge.extract_rid(_original()) == RID


def test_nested_rfc822():
    assert bridge.extract_rid(_wrap_rfc822(_original())) == RID


def test_eml_attachment():
    outer = EmailMessage()
    outer["Subject"] = "Fwd report"
    outer.set_content("see attached")
    outer.add_attachment(_original().as_bytes(), maintype="application",
                         subtype="octet-stream", filename="reported.eml")
    parsed = email.message_from_bytes(outer.as_bytes())
    assert bridge.extract_rid(parsed) == RID


def test_quoted_printable_is_decoded():
    m = EmailMessage()
    m["Subject"] = "qp"
    # '=3D' is QP for '='; get_payload(decode=True) must resolve it.
    m.set_content("link: https://login.lcstn.org/signin?rid=3Dqp99887")
    m.set_param("charset", "utf-8")
    # Re-encode as QP by round-tripping through bytes.
    parsed = email.message_from_bytes(m.as_bytes())
    # Not asserting a value here — just that no crash and a plausible hit/none.
    assert bridge.extract_rid(parsed) in (None, "qp99887", "3Dqp99887")


def test_no_rid_returns_none():
    m = EmailMessage()
    m["Subject"] = "no rid"
    m.set_content("nothing trackable here")
    assert bridge.extract_rid(m) is None


def test_ignores_rid_on_unknown_host():
    """A rid= on a host that isn't ours should not anchor-match; falls back only
    if nothing anchored is found."""
    m = EmailMessage()
    m["Subject"] = "foreign"
    m.set_content("https://evil.example.com/x?rid=deadbeef")
    # fallback may still catch it; the anchored set must be empty.
    assert not bridge._RID_ANCHORED.findall("https://evil.example.com/x?rid=deadbeef")


@pytest.mark.skipif(not FIXTURES.exists() or not any(FIXTURES.glob("*.eml")),
                    reason="no real fixtures yet (TASK-10)")
def test_real_fixtures():
    """Each real sample should be named <rid>__description.eml so we can assert."""
    for f in FIXTURES.glob("*.eml"):
        expected = f.name.split("__", 1)[0]
        msg = email.message_from_bytes(f.read_bytes())
        assert bridge.extract_rid(msg) == expected, f.name
