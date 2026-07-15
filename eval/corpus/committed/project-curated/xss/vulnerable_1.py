"""Reflected XSS: user input echoed into HTML without escaping (CWE-79)."""
from flask import request


def greet() -> str:
    name = request.args.get("name", "")
    return "<h1>Hello, " + name + "</h1>"  # sast:vuln
