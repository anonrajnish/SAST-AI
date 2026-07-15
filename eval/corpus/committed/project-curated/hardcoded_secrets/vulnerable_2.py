"""Hardcoded API token in source (CWE-798)."""
import requests

API_TOKEN = "example-token-0123456789-do-not-use"  # sast:vuln


def fetch(url: str) -> requests.Response:
    return requests.get(url, headers={"Authorization": f"Bearer {API_TOKEN}"})
