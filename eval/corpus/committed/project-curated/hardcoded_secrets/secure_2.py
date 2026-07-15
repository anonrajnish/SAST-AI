"""Safe: API token read from the environment (CWE-798)."""
import os

import requests

API_TOKEN = os.environ["API_TOKEN"]  # sast:safe


def fetch(url: str) -> requests.Response:
    return requests.get(url, headers={"Authorization": f"Bearer {API_TOKEN}"})
