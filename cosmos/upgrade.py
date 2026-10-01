"""Updates that reach every project by themselves: a newer release, and the repairs a release brings.

Nobody pushes cosmos into each repository. Once a day (cached per machine) a background process asks PyPI for the
latest release. When it is newer than the repository's committed copy (.cosmos/vendor), it downloads the wheel, checks
its sha256 against PyPI's, makes sure the new copy imports, swaps it in and commits .cosmos, so every teammate gets it
on their next pull, with or without a pip install. A pip install on this machine is upgraded too when pip allows it.

A new version then runs `repair` once per machine and repository: each step rewrites what an older version wrote
wrongly or does not write at all (hook commands, slash commands, the Codex plugin listing, a Claude Desktop MCP entry
that sends every session's facts to one repository). Steps are idempotent and only touch files cosmos wrote, or add
cosmos's own entry next to the team's. `update.auto: false` in .cosmos/config.json turns all of it off.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from . import __version__
from .config import Config

PYPI_JSON = "https://pypi.org/pypi/cosmos-dev/json"
PLUGIN_GIT = "https://github.com/BiswajitBiswa/cosmos.git"     # where the Codex plugin listing points (plugin/ on main)
CHECK_EVERY = 24 * 3600


def _home() -> Path:
    return Path(os.environ.get("COSMOS_HOME") or (Path.home() / ".config" / "cosmos"))


def vtuple(v: str) -> Tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v or "")[:4])


def vendored_version(cfg: Config) -> str:
    init = cfg.paths.cosmos / "vendor" / "cosmos" / "__init__.py"
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)', init.read_text()) if init.exists() else None
    return m.group(1) if m else ""


# ---------------------------------------------------------------- the latest release
CA_BUNDLES = ["/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt",
              "/opt/homebrew/etc/openssl@3/cert.pem", "/usr/local/etc/openssl@3/cert.pem"]


def _contexts():
    """Verified TLS, always: Python's own trust store first, then certifi, then the system bundle (python.org's macOS
    Python ships without one until "Install Certificates" is run)."""
    import ssl
    yield ssl.create_default_context()
    try:
        import certifi
        yield ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    for ca in CA_BUNDLES:
        if os.path.exists(ca):
            yield ssl.create_default_context(cafile=ca)


def _get(url: str, timeout: int) -> bytes:
    if not url.startswith("https://"):
        with urllib.request.urlopen(url, timeout=timeout) as r:   # a local file in tests
            return r.read()
    err: Exception = OSError("no TLS trust store")
    for ctx in _contexts():
        try:
            with urllib.request.urlopen(url, timeout=timeout, context=ctx) as r:
                return r.read()
        except urllib.error.URLError as e:
            err = e
            if "CERTIFICATE_VERIFY_FAILED" not in str(e):
                raise
    raise err

def latest(max_age: int = CHECK_EVERY) -> Optional[Dict[str, str]]:
    """{version, url, sha256} of the newest wheel on PyPI; asked at most once a day per machine."""
    cache = _home() / "release.json"
    try:
        rec = json.loads(cache.read_text())
        if time.time() - float(rec.get("at", 0)) < max_age:
            return rec.get("release")
    except (OSError, ValueError):
        pass
    try:
        data = json.loads(_get(os.environ.get("COSMOS_PYPI_JSON", PYPI_JSON), 8).decode())
        version = data["info"]["version"]
        wheel = next(f for f in data["urls"] if f.get("packagetype") == "bdist_wheel")
        release = {"version": version, "url": wheel["url"], "sha256": wheel["digests"]["sha256"]}
    except (OSError, ValueError, KeyError, StopIteration):
        return None
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"at": time.time(), "release": release}))
    except OSError:
        pass
    return release


def _fetch_wheel(release: Dict[str, str], into: Path) -> Path:
    """Download the wheel and refuse it unless its sha256 is the one PyPI published."""
    wheel = into / "cosmos.whl"
    wheel.write_bytes(_get(release["url"], 60))
    if hashlib.sha256(wheel.read_bytes()).hexdigest() != release["sha256"]:
        raise ValueError("the downloaded release does not match PyPI's checksum")
    return wheel


def _unpack(wheel: Path, into: Path, version: str) -> Path:
    """The wheel's cosmos/ package, checked: it is the version PyPI named and it imports."""
    out = into / "pkg"
    with zipfile.ZipFile(wheel) as z:
        for name in z.namelist():
            if name.startswith("cosmos/") and ".." not in name and not name.endswith("/"):
                z.extract(name, out)
    init = out / "cosmos" / "__init__.py"
    if not init.exists() or vtuple(re.search(r'__version__\s*=\s*["\']([^"\']+)', init.read_text()).group(1)) != vtuple(version):
        raise ValueError("the release's package is not the version PyPI named")
    probe = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); import cosmos.cli, cosmos.hooks", str(out)],
                           capture_output=True, text=True, timeout=60)
    if probe.returncode != 0:
        raise ValueError("the release does not import here: " + probe.stderr.strip()[-300:])
    return out / "cosmos"


def _swap(new: Path, dst: Path) -> None:
    """Replace the vendored copy in one move, keeping the old one until the new one is in place."""
    old = dst.with_name("cosmos.old")
    if old.exists():
        shutil.rmtree(old)
    if dst.exists():
        dst.rename(old)
    shutil.move(str(new), str(dst))
    shutil.rmtree(old, ignore_errors=True)


def upgrade_vendor(cfg: Config, release: Dict[str, str]) -> str:
    """Bring .cosmos/vendor up to `release`. Returns the version now vendored ("" when nothing changed)."""
    dst = cfg.paths.cosmos / "vendor" / "cosmos"
    if not dst.parent.exists() or vtuple(release["version"]) <= vtuple(vendored_version(cfg)):
        return ""
    with tempfile.TemporaryDirectory() as d:
        pkg = _unpack(_fetch_wheel(release, Path(d)), Path(d), release["version"])
        _swap(pkg, dst)
    return release["version"]


def upgrade_install(release: Dict[str, str]) -> bool:
    """A pip install of cosmos older than the release is upgraded in place when pip allows it (a system Python that
    refuses outside installs is left alone; the repository's copy is what the hooks run anyway)."""
    here = Path(__file__).resolve().parent
    if ".cosmos" in here.parts or vtuple(release["version"]) <= vtuple(__version__) or "site-packages" not in str(here):
        return False
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "--quiet", "--disable-pip-version-check",
                        f"cosmos-dev=={release['version']}"], capture_output=True, text=True, timeout=300)
    return r.returncode == 0


def run(cfg: Config, force: bool = False) -> List[str]:
    """Check, upgrade, repair, commit. Returns what happened, one line each."""
    if not force and not auto_enabled(cfg):
        return []
    lock = cfg.paths.state / "upgrade.lock"
    try:
        cfg.paths.state.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        if time.time() - lock.stat().st_mtime < 900:
            return []                                  # another upgrade is running here
        lock.unlink()
        return run(cfg, force)
    done: List[str] = []
    try:
        release = latest(0 if force else CHECK_EVERY)
        if release:
            got = upgrade_vendor(cfg, release)
            if got:
                done.append(f"vendored cosmos {got}")
            if bool(cfg.get("update.pip", True)) and upgrade_install(release):
                done.append(f"pip install upgraded to {release['version']}")
        wrapper = cfg.paths.cosmos / "cosmosw"
        if done and wrapper.exists():                 # the repairs of the new version, run by the new version
            subprocess.run([sys.executable, str(wrapper), "repair"], cwd=str(cfg.paths.root), capture_output=True, text=True, timeout=300)
        elif _repair_due(cfg):
            done += repair(cfg)
        if done:
            from .sync import commit_inline
            commit_inline(cfg.paths.root, "cosmos: " + "; ".join(done)[:120], extra=_committed_extras(cfg))
    finally:
        lock.unlink(missing_ok=True)
    return done


def auto_enabled(cfg: Config) -> bool:
    return bool(cfg.get("update.auto", True)) and not os.environ.get("COSMOS_NO_UPDATE")


def maybe_background(cfg: Config) -> bool:
    """From a session start: start `cosmos upgrade --auto` in the background when the daily check is due, or when this
    version has not repaired this repository on this machine yet. Never waits for it."""
    if not auto_enabled(cfg) or os.environ.get("COSMOS_NO_BACKGROUND"):
        return False
    due = _repair_due(cfg)
    try:
        due = due or time.time() - float(json.loads((_home() / "release.json").read_text()).get("at", 0)) > CHECK_EVERY
    except (OSError, ValueError):
        due = True
    wrapper = cfg.paths.cosmos / "cosmosw"
    if not due or not wrapper.exists():
        return False
    try:
        log = (cfg.paths.state / "upgrade.log").open("a")
        subprocess.Popen([sys.executable, str(wrapper), "upgrade", "--auto"], cwd=str(cfg.paths.root), stdin=subprocess.DEVNULL,
                         stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        return True
    except OSError:
        return False


# ---------------------------------------------------------------- repairs a new version brings
def _repair_due(cfg: Config) -> bool:
    from .store import State
    return (State(cfg.paths).data.get("repaired") or "") != __version__


def _committed_extras(cfg: Config) -> List[str]:
    root = cfg.paths.root
    extras = [".agents/plugins/marketplace.json", ".claude/settings.json", ".claude/commands", ".gemini/commands", ".cursor/commands",
              ".github/prompts", ".windsurf/workflows"]
    return [e for e in extras if (root / e).exists()]


def _step_wrapper(cfg: Config) -> str:
    from .wrapper import WRAPPER, write_wrapper
    p = cfg.paths.cosmos / "cosmosw"
    if p.exists() and p.read_text() == WRAPPER:
        return ""
    write_wrapper(cfg.paths.cosmos)
    return "wrapper rewritten"


def _step_repo_hooks(cfg: Config) -> str:
    from .hooks import install_hooks
    s = cfg.paths.claude_settings
    return "repository hooks rewritten" if s.exists() and "cosmos" in s.read_text() and install_hooks(s) else ""


def _step_user_hooks(cfg: Config) -> str:
    from .hooks import install_hooks
    s = Path(os.environ.get("COSMOS_USER_SETTINGS") or (Path.home() / ".claude" / "settings.json"))
    return "user hooks rewritten" if s.exists() and "cosmosw" in s.read_text() and install_hooks(s) else ""


def _step_commands(cfg: Config) -> str:
    from .commands import refresh
    n = len(refresh(cfg))
    return f"{n} slash command file(s) rewritten" if n else ""


def codex_listing(existing: Optional[Dict] = None) -> Dict:
    """The repository's own Codex plugin listing: Codex shows it in the Plugins screen of any thread opened here, so
    a teammate installs cosmos with one click, no terminal. The team's other entries are kept."""
    entry = {"name": "cosmos", "source": {"source": "git-subdir", "url": PLUGIN_GIT, "path": "./plugin", "ref": "main"},
             "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "category": "Coding"}
    data = dict(existing or {"name": "repo", "interface": {"displayName": "This repository"}, "plugins": []})
    data["plugins"] = [p for p in data.get("plugins") or [] if p.get("name") != "cosmos"] + [entry]
    return data


def _step_codex_listing(cfg: Config) -> str:
    if not cfg.get("codex.listing", True) or (cfg.paths.root / "plugin" / ".codex-plugin").exists():
        return ""                                      # turned off, or this is cosmos's own repository (its listing is the source)
    p = cfg.paths.root / ".agents" / "plugins" / "marketplace.json"
    try:
        cur = json.loads(p.read_text()) if p.exists() else None
    except ValueError:
        return ""                                      # the team's own file, unreadable: never overwrite it
    new = codex_listing(cur)
    if cur == new:
        return ""
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(new, indent=2) + "\n")
    return "Codex plugin listing written (.agents/plugins/marketplace.json)"


def _step_desktop_pin(cfg: Config) -> str:
    """A Claude Desktop MCP entry named `cosmos` that runs one repository's cosmosw takes the name of every project's
    own server in Desktop sessions. Renamed to cosmos-<repo> (it keeps working), with a backup of the file."""
    from .connect import DESKTOP_CONFIG
    p = Path(os.environ.get("COSMOS_DESKTOP_CONFIG") or DESKTOP_CONFIG)
    try:
        data = json.loads(p.read_text()) if p.exists() else {}
    except (OSError, ValueError):
        return ""
    servers = data.get("mcpServers") or {}
    entry = servers.get("cosmos") or {}
    target = next((a for a in entry.get("args", []) if str(a).endswith(".cosmos/cosmosw")), "")
    if not target:
        return ""
    name = "cosmos-" + Path(target).parent.parent.name
    if name in servers:
        return ""
    data["mcpServers"] = {(name if k == "cosmos" else k): v for k, v in servers.items()}
    shutil.copy2(p, p.with_name(p.name + f".bak-cosmos-{time.strftime('%Y-%m-%d')}"))
    p.write_text(json.dumps(data, indent=2) + "\n")
    return f"Claude Desktop MCP entry `cosmos` renamed to `{name}` (restart Claude Desktop)"


REPAIRS: List[Callable[[Config], str]] = [_step_wrapper, _step_repo_hooks, _step_user_hooks, _step_commands, _step_codex_listing,
                                          _step_desktop_pin]


def repair(cfg: Config) -> List[str]:
    """Every repair step once; records that this version repaired this repository on this machine."""
    from .store import State
    done = []
    for step in REPAIRS:
        try:
            msg = step(cfg)
        except Exception as e:                         # one broken step never stops the others
            msg = f"{step.__name__[6:]} failed: {e}"
        if msg:
            done.append(msg)
    st = State(cfg.paths)
    st.data["repaired"] = __version__
    st.save()
    return done
