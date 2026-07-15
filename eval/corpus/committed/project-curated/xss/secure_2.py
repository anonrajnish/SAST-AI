"""Safe HTML output via an autoescaping template engine (CWE-79)."""
from flask import render_template_string, request


def greet() -> str:
    name = request.args.get("name", "")
    return render_template_string("<h1>Hello, {{ name }}</h1>", name=name)  # sast:safe
