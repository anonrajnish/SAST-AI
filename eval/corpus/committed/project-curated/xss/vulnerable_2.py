"""XSS via Markup marking untrusted data as safe (CWE-79)."""
from flask import request
from markupsafe import Markup


def render_comment() -> Markup:
    comment = request.args.get("comment", "")
    return Markup("<p>" + comment + "</p>")  # sast:vuln
