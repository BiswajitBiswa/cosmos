---
type: Handoff
kind: handoff
branch: "main"
by: "Biswajit Tripathy"
at: "2026-09-29T10:28:05Z"
how: auto
---

That search came up empty because `cosmos-dev` isn't on PyPI yet; I just checked and it's still not there. The upload was left to you, since I won't sign in with a token. Once it's up, Google can take days or weeks to list it, but `pip install cosmos-dev` works within about a minute. The package is already built from the pushed code. In a terminal, from the cosmos folder: ```bash cd ~/Desktop/shyftlabs/ideator/cosmos ``` ```bash TWINE_USERNAME=__token__ python3.11 -m twine upload dist/* ``` When it asks for a password, paste your PyPI token, the one starting with `pypi-`. Then revoke that token on PyPI, since it's in this chat. To check it worked: ```bash python3 -m pip index versions cosmos …
