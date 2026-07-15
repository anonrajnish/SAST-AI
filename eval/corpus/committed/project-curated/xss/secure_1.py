"""Safe HTML output using explicit escaping (CWE-79)."""
from flask import request
from markupsafe import escape


def greet() -> str:
    name = request.args.get("name", "")
    return "<h1>Hello, " + str(escape(name)) + "</h1>"  # sast:safe
