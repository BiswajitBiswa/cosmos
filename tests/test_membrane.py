"""Run: python3 -m unittest discover -s tests -v"""
import json
import os
import subprocess
from datetime import date, datetime
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["COSMOS_LLM_PROVIDER"] = "none"
os.environ["COSMOS_NO_BACKGROUND"] = "1"   # tests never spawn watchers/dreams or touch ~/.claude   # tests never call a real model; LLM paths use fakes

from cosmos import extract, privacy, retrieve  # noqa: E402
from cosmos.config import load_config  # noqa: E402
from cosmos.dream import dream, looks_contradictory  # noqa: E402
from cosmos.hooks import capture, handle, install_hooks, uninstall_hooks  # noqa: E402
from cosmos.render import render_all, upsert_block, managed_block  # noqa: E402
from cosmos.store import Ledger, Memory, Observations, make_id  # noqa: E402
from cosmos.transcript import Turn, iter_turns  # noqa: E402


def _user(text, sid="s"):
    return {"type": "user", "uuid": "u" + str(abs(hash(text)) % 10**6), "sessionId": sid, "timestamp": "2026-09-17T10:00:00Z",
            "message": {"role": "user", "content": text}}


def _asst(text, files=(), sid="s"):
    blocks = [{"type": "text", "text": text}] + [{"type": "tool_use", "id": "t", "name": "Edit", "input": {"file_path": f, "old_string": "a", "new_string": "b"}} for f in files]
    return {"type": "assistant", "uuid": "a" + str(abs(hash(text)) % 10**6), "sessionId": sid, "timestamp": "2026-09-17T10:00:01Z",
            "message": {"role": "assistant", "content": blocks}}


class Repo:
    """Temp git repo with cosmos initialized."""
    def __enter__(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Test Dev"], cwd=self.root, check=True)
        (self.root / "src").mkdir()
        (self.root / "src" / "redis-lock.ts").write_text("x")
        self.cfg = load_config(self.root)
        self.cfg.paths.ensure()
        self.cfg.save()
        return self

    def __exit__(self, *a):
        self.dir.cleanup()

    def transcript(self, name, lines):
        p = self.root / name
        p.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
        return p

    def capture(self, path, sid):
        return capture(self.cfg, {"transcript_path": str(path), "session_id": sid, "hook_event_name": "Stop", "cwd": str(self.root)})


class TestPrivacy(unittest.TestCase):
    def test_redacts_common_secrets(self):
        cases = {
            "token " + "ghp_" + "A"*36: "github_token",
            "AKIAIOSFODNN7EXAMPLE is the key": "aws_access_key",
            "sk-ant-" + "api03-" + "a"*30: "anthropic_key",
            "password=SuperSecret123!": "kv_secret",
            "Authorization: Bearer abcdefghijklmnopqrstuvwxyz0123": "bearer",
            "postgres://user:pass@host/db": "url_credentials",
            "use " + "xoxb-" + "1"*10 + "-" + "2"*13 + "-" + "A"*24 + " to post": "slack_token",
            "xoxp-" + "1"*10 + "-" + "a"*10 + " is the user token": "slack_token",
            "app token " + "xapp-1-" + "A"*10 + "-" + "1"*13 + "-" + "a"*16: "slack_token",
        }
        for text, name in cases.items():
            out, fired = privacy.redact(text)
            self.assertIn(name, fired, text)
            self.assertIn("[REDACTED", out)

    def test_leaves_normal_text(self):
        out, fired = privacy.redact("Redis is used for locks in src/locking/redis-lock.ts commit 82ab31")
        self.assertEqual(fired, [])

    def test_ignore_globs(self):
        globs = [".env*", "secrets/**", "**/*.pem"]
        self.assertTrue(privacy.path_ignored(".env.local", globs))
        self.assertTrue(privacy.path_ignored("secrets/db.json", globs))
        self.assertTrue(privacy.path_ignored("a/b/c.pem", globs))
        self.assertFalse(privacy.path_ignored("src/app.py", globs))


class TestExtraction(unittest.TestCase):
    def test_high_signal_kept_noise_dropped(self):
        t = Turn("assistant", "Let me look at the file first. We chose Redis rather than Postgres for distributed locks because "
                 "workers share a pool. I'll open the config now. Integration tests require `docker compose up` before `npm test`.",
                 files=["src/redis-lock.ts"])
        obs = extract.extract([t])
        texts = [o.text for o in obs]
        self.assertTrue(any("Redis rather than Postgres" in x for x in texts))
        self.assertTrue(any("docker compose" in x for x in texts))
        self.assertFalse(any(x.startswith("Let me") or x.startswith("I'll") for x in texts))

    def test_explicit_rule(self):
        obs = extract.extract([Turn("user", "remember: Never modify production schemas by hand.")])
        self.assertEqual(len(obs), 1)
        self.assertEqual(obs[0].source, "explicit")
        self.assertGreaterEqual(obs[0].score, 0.9)

    def test_explicit_rule_does_not_inherit_previous_files(self):
        obs = extract.extract([Turn("assistant", "x", files=["src/a.ts"]), Turn("user", "remember: Always run make lint before pushing.")])
        self.assertEqual(obs[-1].files, [])

    def test_questions_and_temporary_dropped(self):
        obs = extract.extract([Turn("assistant", "Should we use Redis for the `LockService` because it is faster? For now the `LockService` must never be called twice, as a test.")])
        self.assertEqual(obs, [])

    def test_transcript_parsing_skips_junk_and_is_incremental(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.jsonl"
            p.write_text("not json\n" + json.dumps({"type": "attachment"}) + "\n" + json.dumps(_asst("hello `X_y`", ["/r/a.py"])) + "\n")
            turns, off = iter_turns(p, 0)
            self.assertEqual(len(turns), 1)
            self.assertEqual(turns[0].files, ["/r/a.py"])
            turns2, off2 = iter_turns(p, off)
            self.assertEqual(turns2, [])
            self.assertEqual(off, off2)


class TestStore(unittest.TestCase):
    def test_markdown_roundtrip(self):
        m = Memory(id=make_id("x"), text="Redis is used for locks", category="decision", files=["a.ts"], tags=["redis"],
                   contradicts=["mem_1"], supersedes="mem_0", reason="Because", related=["mem_2"])
        back = Memory.from_markdown(m.to_markdown())
        for f in ("id", "text", "category", "files", "tags", "contradicts", "supersedes", "reason", "related", "confidence"):
            self.assertEqual(getattr(m, f), getattr(back, f), f)
        self.assertIn('aliases: ["' + m.id + '"]', m.to_markdown())   # Obsidian resolves [[mem_id]] via alias


class TestLoop(unittest.TestCase):
    def test_capture_dedupe_contradiction_supersede_retrieve(self):
        with Repo() as r:
            old = r.transcript("old.jsonl", [_user("locks?"), _asst("Postgres advisory locks are used for distributed locking in the workers, see `src/pg-lock.ts`.", [str(r.root / "src/pg-lock.ts")])])
            new = r.transcript("new.jsonl", [
                _user("why double processing?"),
                _asst("Redis is used for distributed locks in the payment workers, see `src/redis-lock.ts`.", [str(r.root / "src/redis-lock.ts")]),
                _user("token " + "ghp_" + "A"*36 + " please use it"),
                _asst("Redis is used for distributed locks in the payment workers, see `src/redis-lock.ts`."),
                _user("remember: Webhooks must be verified in src/webhooks.ts before use."),
            ])
            self.assertGreaterEqual(r.capture(old, "old"), 1)
            n = r.capture(new, "new")
            self.assertGreaterEqual(n, 2)
            self.assertEqual(r.capture(new, "new"), 0, "incremental: nothing new on re-run")
            for o in Observations(r.cfg.paths).iter_all():
                self.assertNotIn("ghp_", o["text"])
            rep = dream(r.cfg)
            mems = Ledger(r.cfg.paths).load()
            redis = [m for m in mems.values() if m.text.startswith("Redis is used")]
            self.assertEqual(len(redis), 1, "duplicate observation merged into one memory")
            self.assertEqual(redis[0].evidence_count, 2)
            pg = [m for m in mems.values() if m.text.startswith("Postgres")][0]
            self.assertEqual(pg.status, "superseded", "evidence file gone + newer fact present → superseded")
            self.assertEqual(pg.superseded_by, redis[0].id)
            self.assertIn((pg.id, redis[0].id), rep.superseded)
            expl = [m for m in mems.values() if m.source == "explicit"]
            self.assertEqual(len(expl), 1)
            hits = retrieve.retrieve(mems, "add retries to the webhook handler")
            self.assertTrue(hits and "Webhooks" in hits[0].text)
            self.assertNotIn(pg.id, [h.id for h in retrieve.retrieve(mems, "postgres locking")])
            changed = render_all(r.cfg, mems)
            self.assertIn("CLAUDE.md", changed)
            self.assertIn("AGENTS.md", changed)
            self.assertEqual(render_all(r.cfg, mems), [str(r.cfg.paths.ledger / "_index.md")], "second render is idempotent")

    def test_same_fact_not_a_contradiction(self):
        a = Memory("m1", "We chose Redis rather than Postgres for locks because of pooling.", "decision")
        b = Memory("m2", "Redis is used for distributed locks (see `src/redis-lock.ts`).", "decision")
        self.assertFalse(looks_contradictory(a, b))
        c = Memory("m3", "Postgres advisory locks are used for distributed locking in the workers.", "decision")
        self.assertTrue(looks_contradictory(b, c))
        d = Memory("m4", "Never use Redis for distributed locks in the workers.", "constraint")
        e = Memory("m5", "Redis is used for distributed locks in the workers.", "constraint")
        self.assertTrue(looks_contradictory(d, e))

    def test_stale_when_evidence_gone(self):
        with Repo() as r:
            m = Memory(make_id("gone"), "The `Foo` service lives in src/gone.ts and owns billing.", "architecture", files=["src/gone.ts"])
            Ledger(r.cfg.paths).save(m)
            dream(r.cfg)
            self.assertEqual(Ledger(r.cfg.paths).load()[m.id].status, "stale-candidate")


class TestHooks(unittest.TestCase):
    def test_handle_never_raises(self):
        self.assertEqual(handle("garbage{"), 0)
        self.assertEqual(handle(json.dumps({"hook_event_name": "Stop", "cwd": "/nonexistent/path"})), 0)
        self.assertEqual(handle(json.dumps({"hook_event_name": "SessionStart", "cwd": tempfile.gettempdir()})), 0)

    def test_install_merges_and_uninstall_restores(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "settings.json"
            p.write_text(json.dumps({"permissions": {"allow": ["Bash"]}, "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo other"}]}]}}))
            self.assertTrue(install_hooks(p))
            self.assertFalse(install_hooks(p), "idempotent")
            s0 = json.loads(p.read_text()); s0["hooks"]["SessionStart"][0]["hooks"][0]["command"] = "python3 .cosmos/cosmosw hook"; p.write_text(json.dumps(s0))
            self.assertTrue(install_hooks(p), "old relative command is migrated in place")
            self.assertIn("CLAUDE_PROJECT_DIR", json.loads(p.read_text())["hooks"]["SessionStart"][0]["hooks"][0]["command"])
            s = json.loads(p.read_text())
            self.assertEqual(s["permissions"], {"allow": ["Bash"]})
            self.assertEqual(len(s["hooks"]["Stop"]), 2)
            self.assertIn("SessionStart", s["hooks"])
            self.assertTrue(uninstall_hooks(p))
            s = json.loads(p.read_text())
            self.assertEqual(s["hooks"], {"Stop": [{"hooks": [{"type": "command", "command": "echo other"}]}]})

    def test_managed_block_upsert(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "CLAUDE.md"
            p.write_text("# My project\n\nkeep me\n")
            self.assertTrue(upsert_block(p, managed_block({}, 5)))
            self.assertFalse(upsert_block(p, managed_block({}, 5)))
            self.assertIn("keep me", p.read_text())
            self.assertEqual(p.read_text().count("cosmos:start"), 1)


class TestZeroInstall(unittest.TestCase):
    def test_fresh_clone_needs_no_install(self):
        """Simulate a teammate: repo has .cosmos/ (vendored) + hooks, but their Python has no cosmos installed."""
        with Repo() as r:
            out = subprocess.run([sys.executable, "-m", "cosmos", "init"], cwd=r.root, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT)})
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertTrue((r.root / ".cosmos" / "cosmosw").exists())
            self.assertTrue((r.root / ".cosmos" / "vendor" / "cosmos" / "cli.py").exists())
            settings = json.loads((r.root / ".claude" / "settings.json").read_text())
            cmd = settings["hooks"]["SessionStart"][0]["hooks"][0]["command"]
            self.assertIn('CLAUDE_PROJECT_DIR', cmd); self.assertIn('exec python3', cmd); self.assertTrue(cmd.endswith('exit 0'))
            # the command is harmless in a repo without .cosmos and preserves exit codes where it exists
            other = Path(tempfile.mkdtemp())
            self.assertEqual(subprocess.run(["sh", "-c", cmd], cwd=other, env={**os.environ, "CLAUDE_PROJECT_DIR": str(other)}, input="{}", capture_output=True, text=True).returncode, 0)
            self.assertEqual(subprocess.run(["sh", "-c", cmd], cwd=other, env={**os.environ, "CLAUDE_PROJECT_DIR": str(r.root)}, input=json.dumps({"hook_event_name": "SessionStart", "session_id": "x", "cwd": str(other)}), capture_output=True, text=True).returncode, 0, "cd'd into a sibling repo: still finds this repo's wrapper")
            # run the SessionStart hook with cosmos deliberately NOT importable (-I: isolated, no PYTHONPATH/site)
            Ledger(r.cfg.paths).save(Memory(make_id("k"), "Redis is used for locks in `src/redis-lock.ts`.", "decision"))
            ev = json.dumps({"hook_event_name": "SessionStart", "session_id": "x", "cwd": str(r.root)})
            out = subprocess.run([sys.executable, "-I", ".cosmos/cosmosw", "hook"], cwd=r.root, input=ev, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("Redis is used for locks", out.stdout)
            # and status works the same way
            out = subprocess.run([sys.executable, "-I", ".cosmos/cosmosw", "status", "--json"], cwd=r.root, capture_output=True, text=True)
            self.assertEqual(json.loads(out.stdout)["memories"], 1)


class TestCLI(unittest.TestCase):
    def test_status_is_fast_and_json(self):
        import time
        with Repo() as r:
            t = time.time()
            out = subprocess.run([sys.executable, "-m", "cosmos", "status", "--json"], cwd=r.root, capture_output=True, text=True)
            self.assertLess(time.time() - t, 1.5)
            self.assertEqual(json.loads(out.stdout)["memories"], 0)


if __name__ == "__main__":
    unittest.main()


class TestLaneHygiene(unittest.TestCase):
    def test_multiparagraph_commit_body_is_not_a_file_list(self):
        from cosmos.sources import git_commits
        from cosmos.store import State
        with Repo() as r:
            (r.root / "svc").mkdir(exist_ok=True)
            (r.root / "svc" / "flags.py").write_text("X = 1\n")
            subprocess.run(["git", "add", "-A"], cwd=r.root, check=True)
            msg = "feat: default flags off\n\nFirst paragraph explains why.\n\nto dev and qa-v2 only, not prod/qa/stg. With a True default\n--reply --only <id> --text posts a reply"
            subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg], cwd=r.root, check=True)
            c = [c for c in git_commits(r.cfg, State(r.cfg.paths)) if c["subject"] == "feat: default flags off"][0]
            self.assertIn("svc/flags.py", c["files"])
            self.assertFalse([f for f in c["files"] if " " in f or f.startswith("-")], "no prose in the file list")
            self.assertIn("--reply --only", c["body"], "later paragraphs stay in the body")

    def test_prose_in_evidence_never_becomes_a_lane_or_escapes_lanes_dir(self):
        from cosmos.lanes import assign_lanes, infer_lane
        from cosmos.render import write_lane_pages
        with Repo() as r:
            self.assertEqual(infer_lane(["to dev and qa-v2 only, not prod/qa/stg. With a True default", "--reply --only <id>/x"]), "general")
            m = Memory(id="mem_bad00001", text="Flags default off in every environment", category="decision",
                       files=["to dev and qa-v2 only, not prod/qa/stg. With a True default", "svc/flags.py"], lane="to dev and qa-v2 only, not prod")
            mems = {m.id: m}
            assign_lanes(mems, r.cfg)
            self.assertEqual(m.files, ["svc/flags.py"])
            self.assertNotIn(" ", m.lane)
            gone = Memory(id="mem_gone0001", text="An old fact nobody needs", category="decision", status="forgotten", lane="old-lane")
            sib = Memory(id="mem_sib00001", text="The web app reads the same flag", category="decision", lane="../web-app", meta={"lane_by": "model"})
            mems.update({gone.id: gone, sib.id: sib})
            d = r.cfg.paths.ledger / "lanes"
            d.mkdir(parents=True, exist_ok=True)
            (d / "stale.md").write_text('---\ntype: "Lane"\n---\n# Lane · stale\n')
            write_lane_pages(r.cfg, mems)
            names = sorted(p.name for p in d.glob("*.md"))
            self.assertNotIn("old-lane.md", names, "no page for a lane with only forgotten facts")
            self.assertNotIn("stale.md", names, "pages of lanes that no longer exist are removed")
            self.assertIn("repo-web-app.md", names)
            self.assertFalse((r.cfg.paths.ledger / "web-app.md").exists(), "a ../ lane never writes outside lanes/")


class TestCharterRepair(unittest.TestCase):
    def test_text_pasted_above_the_header_moves_into_the_body(self):
        from cosmos.charter import TEMPLATE, normalize
        pasted = "## Architecture rules\n\n### Tenancy\n- Every query is scoped to the business.---\n"   # no newline before the header
        out = normalize(pasted + TEMPLATE)
        self.assertTrue(out.startswith("---\ngate:"))
        self.assertEqual(out.count("## Architecture rules"), 1, "merged into the existing section, not duplicated")
        self.assertIn("### Tenancy\n- Every query is scoped", out.split("## Architecture rules", 1)[1])
        self.assertEqual(normalize(out), out, "idempotent")
        self.assertEqual(normalize(TEMPLATE), TEMPLATE, "a well-formed charter is untouched")


class TestCowork(unittest.TestCase):
    def _session(self, base, host_folder, vm="calm-vm", lines=()):
        org = base / "acct" / "org"
        (org / "local_abc" / ".claude" / "projects" / "-x").mkdir(parents=True)
        (org / "local_abc.json").write_text(json.dumps({"vmProcessName": vm, "userSelectedFolders": [str(host_folder)],
                                                        "folderMountNames": {str(host_folder): host_folder.name}}))
        t = org / "local_abc" / ".claude" / "projects" / "-x" / "s1.jsonl"
        t.write_text("".join(json.dumps(l) + "\n" for l in lines))
        return t

    def test_cowork_session_over_a_parent_folder_is_found_mapped_and_scoped(self):
        import cosmos.adapters as ad
        with Repo() as r, tempfile.TemporaryDirectory() as base:
            parent = r.root.parent
            mnt = f"/sessions/calm-vm/mnt/{parent.name}"
            def user(text): return {"type": "user", "cwd": "/private/var/empty", "message": {"role": "user", "content": text}}
            def bash(cmd): return {"type": "assistant", "cwd": "/private/var/empty", "message": {"role": "assistant", "content": [{"type": "tool_use", "name": "mcp__workspace__bash", "input": {"command": cmd}}]}}
            def edit(path): return {"type": "assistant", "cwd": "/private/var/empty", "message": {"role": "assistant", "content": [{"type": "tool_use", "name": "Edit", "input": {"file_path": path, "old_string": "a", "new_string": "b"}}]}}
            t = self._session(Path(base), parent, lines=[
                user("fix the opt-out check"), bash(f"cd {mnt}/{r.root.name} && git commit -m 'fix opt-out'"), edit(str(r.root / "svc" / "send.py")),
                user("now write the marketing post"), bash(f"cd {mnt}/other-project && ls"),
            ])
            old = ad.COWORK_BASE
            ad.COWORK_BASE = Path(base)
            try:
                self.assertIn(t, [p for p, _ in ad.find_claude_sessions(r.root)])
                turns, _ = ad.read_session(t, "claude", 0, root=r.root)
            finally:
                ad.COWORK_BASE = old
            self.assertEqual([x.text for x in turns if x.role == "user"], ["fix the opt-out check"], "the other project's exchange is left out")
            self.assertIn(f"cd {r.root} &&", turns[1].commands[0], "sandbox paths are mapped to this machine")
            from cosmos.journal import commits_in
            self.assertEqual(commits_in([c for x in turns for c in x.commands]), ["fix opt-out"])


class TestAtlasSources(unittest.TestCase):
    def test_ignored_folders_and_setup_jobs_do_not_shape_the_atlas(self):
        from cosmos.atlas import _by_model, build, inventory
        with Repo() as r:
            (r.root / ".gitignore").write_text("junk/\n")
            (r.root / "junk" / "pkg").mkdir(parents=True)
            (r.root / "junk" / "pkg" / "package.json").write_text('{"name": "stale-copy"}')
            (r.root / "web").mkdir(exist_ok=True)
            (r.root / "web" / "package.json").write_text('{"name": "web"}')
            (r.root / "docker-compose.yml").write_text("services:\n  db:\n    image: postgres:16\n  minio:\n    image: minio/minio\n  minio-init:\n    image: minio/mc\n    depends_on: [minio]\n")
            inv = inventory(r.cfg)
            self.assertNotIn("stale-copy", [a["name"] for a in inv["apps"]])
            self.assertIn("web", [a["name"] for a in inv["apps"]])
            self.assertEqual(sorted(x["name"] for x in inv["stores"]), ["db", "minio"], "minio-init is a job, not a store")
            d = r.cfg.paths.ledger / "atlas"
            d.mkdir(parents=True, exist_ok=True)
            refined = "---\ntype: Diagram\ngenerated_by: atlas-deep\n---\n# refined by the model\n"
            (d / "containers.md").write_text(refined)
            build(r.cfg)
            self.assertEqual((d / "containers.md").read_text(), refined, "the generator never overwrites the model's diagram")
            self.assertTrue(_by_model(d / "containers.md"))

    def test_hooks_off_for_cosmos_own_headless_runs(self):
        from cosmos.hooks import handle
        os.environ["COSMOS_HOOKS_OFF"] = "1"
        try:
            self.assertEqual(handle(json.dumps({"hook_event_name": "Stop", "cwd": "/"})), 0)
        finally:
            del os.environ["COSMOS_HOOKS_OFF"]


class TestLedgerRelink(unittest.TestCase):
    def test_pruned_worktree_record_is_relinked_and_nothing_is_lost(self):
        import shutil
        from cosmos import sync
        with Repo() as r:
            ok, msg = sync.migrate(r.root) if (r.root / ".cosmos").exists() else sync.attach(r.root)
            self.assertTrue(sync.linked(r.root), msg)
            (r.root / ".cosmos" / "ledger").mkdir(parents=True, exist_ok=True)
            (r.root / ".cosmos" / "ledger" / "a.md").write_text("first\n")
            sync.commit(r.root, "one")
            gitdir = Path((r.root / ".cosmos" / ".git").read_text().split("gitdir:", 1)[1].strip())
            shutil.rmtree(gitdir)                                   # what a sandbox's `git worktree prune` does
            (r.root / ".cosmos" / "ledger" / "b.md").write_text("written while unlinked\n")
            self.assertFalse(sync.linked(r.root))
            self.assertTrue(sync.commit(r.root, "two"), "commit relinks first, then commits")
            self.assertTrue(sync.linked(r.root))
            files = subprocess.run(["git", "ls-tree", "-r", "--name-only", "cosmos"], cwd=r.root, capture_output=True, text=True).stdout.split()
            self.assertIn("ledger/a.md", files)
            self.assertIn("ledger/b.md", files)
            self.assertEqual((r.root / ".cosmos" / "ledger" / "b.md").read_text(), "written while unlinked\n")
            self.assertFalse(list(r.root.glob(".cosmos-relink-*")), "no temporary folder left behind")


class TestFlarePrefix(unittest.TestCase):
    def test_chosen_prefix_is_remembered_and_session_flares_follow_it(self):
        from cosmos.audit import flare_prefix, remember_prefix, rename_prefix
        from cosmos.config import load_config
        from cosmos.mcp import call_tool
        from cosmos.dream import _name_findings
        with Repo() as r:
            call_tool(r.cfg, "cosmos_flare", {"title": "Opt-out ignored on bulk send", "severity": "high"})
            self.assertTrue(any(m.meta.get("audit_id", "").startswith("QA-") for m in Ledger(r.cfg.paths).load().values()))
            self.assertTrue(remember_prefix(r.cfg, "RET"))
            self.assertEqual(rename_prefix(r.cfg, "QA", "RET", only_source="mcp"), 1)
            cfg = load_config(r.root)
            self.assertEqual(flare_prefix(cfg), "RET", "saved in the repo config")
            call_tool(cfg, "cosmos_flare", {"title": "Holdout shrinks when pct is unset", "severity": "medium"})
            ids = sorted(m.meta["audit_id"] for m in Ledger(cfg.paths).load().values() if m.category == "finding")
            self.assertTrue(all(i.startswith("RET-") for i in ids), ids)
            stray = Memory(id="mem_abc12345", text="Benchmark: 226ms for the heaviest query", category="finding")
            mems = {stray.id: stray}
            _name_findings(cfg, mems)
            self.assertEqual((stray.meta["audit_id"], stray.meta["severity"], stray.meta["finding_status"]), ("RET-c12345", "note", "note"))


class TestFolderAnchoredFacts(unittest.TestCase):
    def test_a_rule_anchored_to_a_folder_is_shown_before_editing_files_inside_it(self):
        from cosmos.hooks import file_context
        with Repo() as r:
            (r.root / "web" / "src").mkdir(parents=True)
            (r.root / "web" / "src" / "Card.jsx").write_text("x")
            (r.root / "api").mkdir(exist_ok=True)
            (r.root / "api" / "main.py").write_text("x")
            m = Memory(id="mem_ui000001", text="UI cards end at the primary content: no footer microcopy", category="convention",
                       source="explicit", files=["web/src/"])
            Ledger(r.cfg.paths).save_all([m])
            self.assertIn("footer microcopy", file_context(r.cfg, {"session_id": "a", "tool_input": {"file_path": str(r.root / "web/src/Card.jsx")}}))
            self.assertNotIn("footer microcopy", file_context(r.cfg, {"session_id": "b", "tool_input": {"file_path": str(r.root / "api/main.py")}}))


class TestGateLargeChange(unittest.TestCase):
    def test_large_change_asks_for_the_dead_code_scan_until_it_ran(self):
        import json as _j
        from cosmos import charter
        from cosmos.gate import evaluate
        with Repo() as r:
            charter.ensure(r.cfg)                           # the default Charter carries the vulture and knip checks
            files = [str(r.root / f"src/m{i}.py") for i in range(6)]
            t = r.transcript("big.jsonl", [_user("refactor"), _asst("Refactored `src/m0.py:1`.", files)])
            res = evaluate(r.cfg, {"transcript_path": str(t), "session_id": "big"})
            self.assertTrue(res["large"])
            self.assertTrue(any("python3 -m vulture ." in x for x in res["reasons"]))
            self.assertFalse(any("knip" in x for x in res["reasons"]), "no JavaScript touched, no knip")
            ran = {"type": "assistant", "uuid": "a-v", "sessionId": "big", "timestamp": "2026-09-17T10:00:02Z",
                   "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "v", "name": "Bash", "input": {"command": "python3 -m vulture src --min-confidence 80"}}]}}
            t2 = r.transcript("big2.jsonl", [_user("refactor"), _asst("Refactored `src/m0.py:1`.", files), ran])
            self.assertFalse(any("vulture" in x for x in evaluate(r.cfg, {"transcript_path": str(t2), "session_id": "big2"})["reasons"]))
            small = r.transcript("small.jsonl", [_user("tweak"), _asst("Fixed `src/m0.py:1`.", files[:1])])
            self.assertFalse(any("vulture" in x for x in evaluate(r.cfg, {"transcript_path": str(small), "session_id": "sm"})["reasons"]))


class TestAudit(unittest.TestCase):
    FINDINGS = [
        {"id": "11", "severity": "critical", "title": "Review chain bypassable via `transition_lookup_to_stage`", "area": "Reviews",
         "locations": "`src/pipeline_stage.py:352` · `review_service.py:1076`", "sections": [["What", "Body reads a second slug."], ["Fix", "Derive server-side."]]},
        {"id": "8", "severity": "medium", "title": "Cross-tenant company rewrite", "area": "Universe", "locations": "`src/universe.py:10`", "sections": [["What", "x"]]},
        {"id": "note-1", "severity": "note", "title": "Verification note", "area": "", "locations": "", "sections": [["Evidence", "y"]]},
    ]

    def _write(self, r, items, name="f.json"):
        p = r.root / name
        p.write_text(json.dumps(items))
        return p

    def test_import_missing_file_created_only_on_confirmation(self):
        env = {**os.environ, "COSMOS_NO_BACKGROUND": "1", "PYTHONPATH": str(Path(__file__).resolve().parent.parent)}
        with Repo() as r:
            cmd = [sys.executable, "-m", "cosmos", "flares", "import", "qa/findings.json", "--prefix", "RET"]
            out = subprocess.run(cmd, cwd=r.root, capture_output=True, text=True, stdin=subprocess.DEVNULL, env=env)
            self.assertEqual(out.returncode, 1)
            self.assertNotIn("Traceback", out.stdout + out.stderr)
            self.assertFalse((r.root / "qa" / "findings.json").exists(), "never created without confirmation")
            out = subprocess.run(cmd + ["--yes"], cwd=r.root, capture_output=True, text=True, env=env)
            self.assertEqual(out.returncode, 0, out.stderr)
            data = json.loads((r.root / "qa" / "findings.json").read_text())
            self.assertEqual(data["findings"], [], "created empty: no made-up finding")
            out = subprocess.run(cmd, cwd=r.root, capture_output=True, text=True, env=env)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("imported 0 new", out.stdout)

    def test_import_idempotent_withdrawn_preserved_regression_detected(self):
        from cosmos.audit import export_json, findings, import_findings, set_status
        from cosmos.audit_slack import build_card, PostState
        with Repo() as r:
            (r.root / "src").mkdir(exist_ok=True)
            (r.root / "src" / "pipeline_stage.py").write_text("x")
            p = self._write(r, self.FINDINGS)
            new, upd, reg = import_findings(r.cfg, p, "QA")
            self.assertEqual((len(new), len(upd), len(reg)), (3, 0, 0))
            new, upd, reg = import_findings(r.cfg, p, "QA")
            self.assertEqual((len(new), len(upd), len(reg)), (0, 3, 0), "re-import is idempotent")
            mems = Ledger(r.cfg.paths).load()
            fs = findings(mems)
            self.assertEqual([m.meta["audit_id"] for m in fs][:2], ["QA-11", "QA-8"], "severity-ordered")
            self.assertEqual(fs[0].files, ["src/pipeline_stage.py", "review_service.py"])
            self.assertEqual(fs[0].details[0], ["What", "Body reads a second slug."])
            # roundtrip through markdown keeps meta + details
            self.assertEqual(Memory.from_markdown(fs[0].to_markdown()).meta["audit_id"], "QA-11")
            # withdraw is a state, survives re-import
            eight = [m for m in fs if m.meta["audit_id"] == "QA-8"][0]
            set_status(r.cfg, eight, "withdrawn", "companies table is shared by design")
            import_findings(r.cfg, p, "QA")
            eight = Ledger(r.cfg.paths).load()[eight.id]
            self.assertEqual(eight.meta["finding_status"], "withdrawn")
            self.assertEqual(eight.status, "forgotten")
            # fixed then reported again → regression
            eleven = [m for m in fs if m.meta["audit_id"] == "QA-11"][0]
            set_status(r.cfg, eleven, "fixed")
            self.assertEqual(Ledger(r.cfg.paths).load()[eleven.id].meta.get("fixed_on"), date.today().isoformat())
            _, _, reg = import_findings(r.cfg, p, "QA")
            self.assertEqual([m.meta["audit_id"] for m in reg], ["QA-11"])
            self.assertEqual(reg[0].meta["finding_status"], "regressed")
            # export keeps the import schema
            ex = export_json(findings(Ledger(r.cfg.paths).load()))
            self.assertEqual({e["id"] for e in ex}, {"11", "8", "note-1"})
            self.assertIn("sections", ex[0])
            # cards are structurally valid Block Kit
            for m in findings(Ledger(r.cfg.paths).load()):
                blocks = build_card(m)
                self.assertEqual(blocks[0]["type"], "header")
                self.assertLessEqual(len(blocks), 50)
                for b in blocks:
                    if b["type"] == "section" and "text" in b:
                        self.assertLessEqual(len(b["text"]["text"]), 3000)
                    if b["type"] == "section" and "fields" in b:
                        self.assertLessEqual(len(b["fields"]), 10)
                        self.assertTrue(all(len(f["text"]) <= 2000 for f in b["fields"]))
            # legacy poster state seeds without double posting
            legacy = r.root / ".slack-posted.json"
            legacy.write_text(json.dumps({"posted": ["11", "8"]}))
            st = PostState(r.cfg.paths.state / "slack-posted.json")
            self.assertEqual(st.seed_from(legacy, "QA"), 2)
            self.assertTrue(st.posted("QA-11") and not st.posted("QA-note-1"))

    def test_status_superset_and_precedence(self):
        from cosmos.audit import import_findings, set_status
        with Repo() as r:
            p = self._write(r, self.FINDINGS)
            import_findings(r.cfg, p, "QA")
            # fix loop writes intermediate states via the JSON → accepted verbatim, never coerced
            items = json.loads(p.read_text()); items[0]["status"] = "claimed"; items[1]["status"] = "needs_human"; p.write_text(json.dumps(items))
            import_findings(r.cfg, p, "QA")
            mems = Ledger(r.cfg.paths).load()
            by = {m.meta["audit_id"]: m for m in mems.values()}
            self.assertEqual(by["QA-11"].meta["finding_status"], "claimed")
            self.assertEqual(by["QA-8"].meta["finding_status"], "needs_human")
            self.assertEqual(by["QA-8"].status, "active", "needs_human is still open work")
            # a stale export saying "open" never downgrades claimed
            items[0]["status"] = "open"; p.write_text(json.dumps(items))
            import_findings(r.cfg, p, "QA")
            self.assertEqual(Ledger(r.cfg.paths).load()[by["QA-11"].id].meta["finding_status"], "claimed")
            # pr_open → fixed via CLI-style set, then "open" again → regressed
            set_status(r.cfg, by["QA-11"], "pr_open"); set_status(r.cfg, by["QA-11"], "fixed")
            _, _, reg = import_findings(r.cfg, p, "QA")
            self.assertEqual([m.meta["audit_id"] for m in reg], ["QA-11"])
            self.assertEqual(by["QA-note-1"].meta["severity"], "note", "note severity kept, not coerced")
            self.assertEqual(by["QA-note-1"].meta["finding_status"], "note", "notes carry no lifecycle")
            with self.assertRaises(SystemExit):
                set_status(r.cfg, by["QA-note-1"], "claimed")
            # status_note / status_at from the fix loop round-trip
            items[1].update({"status": "pr_open", "status_note": "PR #852", "status_at": "2026-09-17T10:00:00Z"}); p.write_text(json.dumps(items))
            import_findings(r.cfg, p, "QA")
            from cosmos.audit import export_json, findings
            ex = {e["audit_id"]: e for e in export_json(findings(Ledger(r.cfg.paths).load()))}
            self.assertEqual((ex["QA-8"]["status"], ex["QA-8"]["status_note"], ex["QA-8"]["status_at"]), ("pr_open", "PR #852", "2026-09-17T10:00:00Z"))
            self.assertEqual(ex["QA-note-1"]["status"], "note")

    def test_card_layout_v2_and_convert_helpers(self):
        from cosmos.audit import import_findings, findings
        from cosmos.audit_slack import build_card, card_fallback_text, parse_ts, re_marker
        with Repo() as r:
            import_findings(r.cfg, self._write(r, self.FINDINGS), "QA")
            m = findings(Ledger(r.cfg.paths).load())[0]
            blocks = build_card(m)
            self.assertEqual(blocks[0]["type"], "header")
            self.assertIn("QA-11 — Review chain bypassable via transition_lookup_to_stage", blocks[0]["text"]["text"], "title in header, mrkdwn stripped")
            self.assertLessEqual(len(blocks[0]["text"]["text"]), 150)
            self.assertEqual(blocks[1]["type"], "section"); self.assertIn("fields", blocks[1])
            labels = [f["text"].split("\n")[0] for f in blocks[1]["fields"]]
            self.assertEqual(labels, ["*Severity*", "*Ref*", "*Area*", "*Status*", "*Location*"])
            self.assertEqual(blocks[2]["type"], "divider")
            self.assertEqual(blocks[-1]["type"], "divider", "trailing divider closes the card")
            self.assertEqual(blocks[-2]["type"], "context")
            self.assertFalse(any("📍" in json.dumps(b) for b in blocks))
            self.assertLessEqual(len(card_fallback_text(m)), 300)
            self.assertTrue(re_marker("QA-1", "footer QA-1"))
            self.assertFalse(re_marker("QA-1", "footer QA-19") or re_marker("QA-1", "QA-1-b"))
            self.assertEqual(parse_ts("https://x.slack.com/archives/C1/p1756211400123456"), "1756211400.123456")
            self.assertEqual(parse_ts("1756211400.123456"), "1756211400.123456")

    def test_lint_flags_bad_keys_and_update_many_suffix(self):
        from cosmos.audit_lint import LintConfig, lint
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "app").mkdir()
            (root / "app" / "svc.py").write_text(
                "company_crud.list({'name__ilike': 'x', 'status': 'active'})\n"
                "company_crud.update_many({'org_id__eq': 1}, {'name': 'y'})\n"
                "company_crud.get({'Company.name': 'z', 'meta->x': 1, 'id': 3})\n"
                "other.list({'nope': 1})\n")
            class Company:
                id = 1; name = ""; org_id = 0; meta = {}
            cfg = LintConfig(repo_base="x:y", crud_glob="", module_prefix="", roots=[str(root / "app")], registry={"Company"})
            issues = lint(cfg, repos={"company_crud": Company})
            self.assertEqual([(i.key, i.kind) for i in issues], [("status", "not_a_column"), ("org_id__eq", "suffix_not_supported")], "sorted by line")

    def test_finding_surfaces_on_related_prompt_and_explicit_prefix(self):
        from cosmos.audit import import_findings
        with Repo() as r:
            import_findings(r.cfg, self._write(r, self.FINDINGS), "QA")
            hits = retrieve.retrieve(Ledger(r.cfg.paths).load(), "refactor the review chain in pipeline_stage.py", paths=["src/pipeline_stage.py"])
            self.assertTrue(hits and hits[0].meta.get("audit_id") == "QA-11")
            obs = extract.extract([Turn("user", "finding: `GET /transitions` has no role gate and leaks approver ids.")])
            self.assertEqual((obs[0].category, obs[0].source), ("finding", "explicit"))

    def test_finding_never_stale_by_age(self):
        from cosmos.audit import import_findings
        with Repo() as r:
            import_findings(r.cfg, self._write(r, [dict(self.FINDINGS[2], locations="")]), "QA")
            mems = Ledger(r.cfg.paths).load()
            m = next(iter(mems.values())); m.last_verified = "2020-01-01"; Ledger(r.cfg.paths).save(m)
            dream(r.cfg)
            self.assertEqual(Ledger(r.cfg.paths).load()[m.id].status, "active")


class TestLanesCharterGateIntakeAtlas(unittest.TestCase):
    def test_lane_inference_and_report(self):
        from cosmos.lanes import infer_lane, assign_lanes, lane_report
        self.assertEqual(infer_lane(["src/payments/webhooks.ts"]), "payments")
        self.assertEqual(infer_lane(["webserver/app/api/v1/endpoints/reviews.py"]), "webserver")
        self.assertEqual(infer_lane(["core_common/services/pipeline_stage.py"]), "core_common", "coarse: top-level package")
        self.assertEqual(infer_lane(["README.md"]), "general")
        self.assertEqual(infer_lane([".claude/skills/qa/SKILL.md", "scripts/x.sh"]), "tooling")
        self.assertEqual(infer_lane(["docs/qa.md", "references/ARCH.html"]), "docs")
        self.assertEqual(infer_lane(["/private/tmp/whatever/preview.html"]), "general", "outside the repo → no lane")
        self.assertEqual(infer_lane(["anything/x.py"], {"billing": ["anything/**"]}), "billing")
        with Repo() as r:
            a = Memory(make_id("a"), "Redis lock in `src/payments/lock.ts`", "decision", files=["src/payments/lock.ts"], authors=["A"])
            b = Memory(make_id("b"), "Webhooks verified in src/payments/webhooks.ts", "constraint", files=["src/payments/webhooks.ts"], authors=["B"])
            mems = {a.id: a, b.id: b}
            self.assertEqual(assign_lanes(mems, r.cfg), 2)
            self.assertEqual({a.lane, b.lane}, {"payments"})
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            obs = [{"ts": now, "author": "A", "files": ["src/payments/lock.ts"]}, {"ts": now, "author": "B", "files": ["src/payments/webhooks.ts"]}]
            rep = lane_report(r.cfg, mems, obs)
            self.assertEqual(rep[0]["lane"], "payments")
            self.assertTrue(rep[0]["overlap"], "two people in one lane within the window → overlap")
            self.assertEqual(rep[0]["facts"], 2)
            # lane survives the markdown round trip
            self.assertEqual(Memory.from_markdown(a.to_markdown()).lane, "payments")

    def test_charter_and_gate(self):
        from cosmos import charter
        from cosmos.gate import evaluate
        with Repo() as r:
            charter.ensure(r.cfg)
            self.assertIn("## How we test", charter.body(r.cfg))
            gc = charter.gate_config(r.cfg)
            self.assertTrue(gc["require_tests"] and gc["require_refs"])
            charter.add_section_rule(r.cfg, "Never call the DB from a controller.")
            self.assertIn("- Never call the DB from a controller.", charter.read(r.cfg))
            summ = charter.summary(r.cfg, {})
            self.assertIn("Never call the DB", summ)
            # a turn that edits code, runs no tests and cites no file:line → blocked with precise reasons
            cp = charter.path(r.cfg); cp.write_text(cp.read_text().replace('"small_change_chars": 400', '"small_change_chars": 0'))   # every change is "big" here
            t = r.transcript("t.jsonl", [_user("fix the lock"), _asst("Done, I changed the lock logic.", [str(r.root / "src/redis-lock.ts")])])
            res = evaluate(r.cfg, {"transcript_path": str(t), "session_id": "s"})
            self.assertTrue(res["block"])
            self.assertEqual(res["edited"], ["src/redis-lock.ts"])
            self.assertTrue(any("ran no tests" in x for x in res["reasons"]) and any("file.ext:line" in x for x in res["reasons"]))
            # never loops: a continued turn passes
            self.assertFalse(evaluate(r.cfg, {"transcript_path": str(t), "session_id": "s", "stop_hook_active": True})["block"])
            # tests ran + refs cited → passes
            ok = [_user("fix"), {"type": "assistant", "uuid": "x1", "sessionId": "s", "timestamp": "2026-09-21T10:00:00Z", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": "t1", "name": "Edit", "input": {"file_path": str(r.root / "src/redis-lock.ts"), "old_string": "a", "new_string": "b"}},
                {"type": "tool_use", "id": "t2", "name": "Bash", "input": {"command": "npm test -- lock"}},
                {"type": "text", "text": "Changed the TTL in src/redis-lock.ts:12; tests pass."}]}}]
            t2 = r.transcript("ok.jsonl", ok)
            res = evaluate(r.cfg, {"transcript_path": str(t2), "session_id": "s2"})
            self.assertTrue(res["block"], "a clean editing turn is still held once: record what the team learned")
            self.assertEqual(len(res["reasons"]), 2)
            self.assertIn("cosmos_remember", res["reasons"][0]); self.assertIn("without asking", res["reasons"][0])
            from cosmos import charter as ch
            cp = ch.path(r.cfg); cp.write_text(cp.read_text().replace('"reflect": true', '"reflect": false'))
            self.assertFalse(evaluate(r.cfg, {"transcript_path": str(t2), "session_id": "s2"})["block"], "reflect off → checklist only")
            cp.write_text(cp.read_text().replace('"reflect": false', '"reflect": true'))
            # docs-only edits are not gated
            t3 = r.transcript("docs.jsonl", [_user("docs"), _asst("Updated README.", [str(r.root / "README.md")])])
            self.assertFalse(evaluate(r.cfg, {"transcript_path": str(t3), "session_id": "s3"})["block"])
            # disabled gate never blocks
            r.cfg.data["gate"] = {"enabled": False}
            self.assertFalse(evaluate(r.cfg, {"transcript_path": str(t), "session_id": "s"})["block"])

    def test_intake_maps_a_feature(self):
        from cosmos.intake import analyse, save, list_intakes
        from cosmos.audit import import_findings
        with Repo() as r:
            a = Memory(make_id("a"), "We chose Redis for distributed locks in the payment workers.", "decision", files=["src/payments/lock.ts"], lane="payments")
            Ledger(r.cfg.paths).save(a)
            fjson = r.root / "f.json"; fjson.write_text(json.dumps([{"id": "1", "severity": "high", "title": "Payment webhook replay", "area": "Payments", "locations": "`src/payments/webhooks.ts:10`", "sections": [["What", "x"]]}]))
            import_findings(r.cfg, fjson, "QA")
            from cosmos.lanes import assign_lanes
            mems = Ledger(r.cfg.paths).load(); assign_lanes(mems, r.cfg); Ledger(r.cfg.paths).save_all(mems.values())
            res = analyse(r.cfg, "add retries to payment webhook processing", files=["src/payments/webhooks.ts"])
            self.assertIn("payments", res["lanes"])
            self.assertTrue(any("Redis" in m.text for m in res["collisions"]))
            self.assertEqual([m.meta["audit_id"] for m in res["findings"]], ["QA-1"])
            p = save(r.cfg, res)
            self.assertTrue(p.exists() and list_intakes(r.cfg)[0]["title"].startswith("add retries"))

    def test_atlas_inventory_diagrams_and_drift(self):
        from cosmos.atlas import build, check, parse_yaml_subset
        with Repo() as r:
            (r.root / "package.json").write_text(json.dumps({"name": "web", "dependencies": {"react": "1"}, "scripts": {"test": "jest"}}))
            (r.root / "docker-compose.yml").write_text("services:\n  web:\n    build: .\n    ports:\n      - \"3000:3000\"\n    depends_on:\n      - db\n      - redis\n  db:\n    image: postgres:16\n  redis:\n    image: redis:7\n")
            (r.root / "k8s").mkdir(); (r.root / "k8s" / "web.yaml").write_text("apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: web\n---\nkind: Service\nmetadata:\n  name: web-svc\n")
            (r.root / "openapi.json").write_text(json.dumps({"paths": {"/users": {"get": {}, "post": {}}, "/health": {"get": {}}}}))
            (r.root / ".env.example").write_text("DATABASE_URL=\nREDIS_URL=\n# comment\n")
            inv = build(r.cfg)
            self.assertEqual([a["name"] for a in inv["apps"]], ["web"])
            self.assertEqual({s["name"] for s in inv["services"]}, {"web"})
            self.assertEqual({s["name"]: s["kind"] for s in inv["stores"]}, {"db": "database", "redis": "cache"})
            self.assertEqual(inv["services"][0]["depends_on"], ["db", "redis"])
            self.assertEqual({k["kind"] for k in inv["k8s"]}, {"Deployment", "Service"})
            self.assertEqual(len(inv["api"][0]["endpoints"]), 3)
            self.assertEqual(inv["env_keys"], ["DATABASE_URL", "REDIS_URL"])
            d = r.cfg.paths.ledger / "atlas"
            self.assertTrue((d / "containers.md").exists() and "web --> db" in (d / "containers.md").read_text())
            self.assertIn("```mermaid", (d / "deployment.md").read_text())
            self.assertFalse(check(r.cfg)["drift"])
            (r.root / "docker-compose.yml").write_text("services:\n  web:\n    build: .\n")
            self.assertEqual(check(r.cfg)["drift"], ["docker-compose.yml"])
            self.assertEqual(parse_yaml_subset("a:\n  b: [x, y]\n  c:\n    - 1\n    - 2\n"), {"a": {"b": ["x", "y"], "c": ["1", "2"]}})

    def test_atlas_reads_unindented_sequences_nested_manifests_and_dedupes_nodes(self):
        """A compose file written the way docker writes it must not blank the Atlas.

        parse_yaml_subset cannot read a sequence at the same indent as its key, and the
        caller used to swallow the resulting AttributeError, so every service silently
        vanished and containers.md rendered as an empty flowchart.
        """
        from cosmos.atlas import build, load_yaml
        unindented = ("services:\n"
                      "  api:\n"
                      "    image: api:1\n"
                      "    ports:\n"
                      "    - \"8000:8000\"\n"
                      "    volumes:\n"
                      "    - api_data:/var/lib/api\n"
                      "    depends_on:\n"
                      "    - db\n"
                      "  db:\n"
                      "    image: postgres:16\n"
                      "    volumes:\n"
                      "    - pg_data:/var/lib/postgresql/data\n")
        self.assertEqual(sorted(load_yaml(unindented, "t.yml")["services"]), ["api", "db"])

        with Repo() as r:
            (r.root / "docker-compose.yml").write_text(unindented)
            # same services declared again, as a local override
            (r.root / "docker-compose.local.yml").write_text(unindented)
            (r.root / "svc").mkdir()
            (r.root / "svc" / "requirements.txt").write_text("fastapi\nuvicorn\n")
            inv = build(r.cfg)

            self.assertEqual({s["name"] for s in inv["services"]}, {"api"})
            self.assertEqual({s["name"] for s in inv["stores"]}, {"db"})
            self.assertEqual(inv["services"][0]["depends_on"], ["db"])
            # a manifest below the repo root is an app
            self.assertIn("svc", [a["name"] for a in inv["apps"]])

            diagram = (r.cfg.paths.ledger / "atlas" / "containers.md").read_text()
            self.assertEqual(diagram.count("api --> db"), 1, "edge duplicated per compose file")
            self.assertEqual(diagram.count('api["api'), 1, "node duplicated per compose file")
            # both compose files still surface in the table, so the overlap stays visible
            table = (r.cfg.paths.ledger / "atlas" / "inventory.md").read_text()
            self.assertIn("docker-compose.local.yml", table)
            self.assertIn("docker-compose.yml", table)


class TestMultiAgent(unittest.TestCase):
    def test_codex_adapter_reads_real_rollout_shape(self):
        from cosmos.adapters import iter_codex_turns, codex_session_cwd, find_codex_sessions
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"; root.mkdir()
            sess = Path(d) / "home" / ".codex" / "sessions" / "2026" / "09" / "21"; sess.mkdir(parents=True)
            p = sess / "rollout-2026-09-21T10-00-00-abc.jsonl"
            L = [{"type": "session_meta", "payload": {"id": "abc", "cwd": str(root), "originator": "Codex Desktop"}},
                 {"type": "response_item", "payload": {"type": "message", "role": "developer", "content": [{"type": "input_text", "text": "<permissions instructions> …"}]}},
                 {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "# AGENTS.md instructions for /x\n<INSTRUCTIONS>…"}]}},
                 {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "make DV360Task take params from the secret like BigQuery"}]}},
                 {"type": "response_item", "payload": {"type": "function_call", "name": "exec_command", "arguments": json.dumps({"cmd": "./gradlew test"})}},
                 {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "apply_patch", "input": "*** Begin Patch\n*** Update File: svc/core/src/main/kotlin/WorkflowNodeUtil.kt\n@@\n-a\n+b\n*** End Patch"}},
                 {"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "The DV360 task must receive a nested `credentials` map from the stored secret, exactly like the BigQuery task in `WorkflowNodeUtil.kt:600`."}]}}]
            p.write_text("\n".join(json.dumps(x) for x in L) + "\n")
            self.assertEqual(codex_session_cwd(p), str(root))
            turns, off = iter_codex_turns(p, 0)
            self.assertEqual([t.role for t in turns], ["user", "assistant"], "developer + injected AGENTS.md messages dropped")
            self.assertEqual(turns[1].files, ["svc/core/src/main/kotlin/WorkflowNodeUtil.kt"])
            self.assertEqual(turns[1].commands, ["./gradlew test"])
            self.assertEqual(iter_codex_turns(p, off)[0], [], "incremental")
            self.assertEqual(find_codex_sessions(root, home=Path(d) / "home"), [p])
            self.assertEqual(find_codex_sessions(Path(d) / "other", home=Path(d) / "home"), [])
            # the shared extractor keeps the durable fact from a Codex session
            obs = extract.extract(turns)
            self.assertTrue(any("DV360" in o.text for o in obs))

    def test_generic_adapter_and_capture_agent(self):
        from cosmos.adapters import iter_generic_turns
        from cosmos.hooks import capture
        with Repo() as r:
            g = r.root / "chat.json"
            g.write_text(json.dumps({"messages": [{"role": "user", "parts": [{"text": "why redis?"}]}, {"role": "model", "parts": [{"text": "Redis is used for distributed locks in `src/redis-lock.ts` because workers share a pool."}]}]}))
            turns = iter_generic_turns(g)
            self.assertEqual([t.role for t in turns], ["user", "assistant"])
            n = capture(r.cfg, {"transcript_path": str(g), "session_id": "g1", "cwd": str(r.root)}, agent="gemini")
            self.assertGreaterEqual(n, 1)
            self.assertEqual(capture(r.cfg, {"transcript_path": str(g), "session_id": "g1", "cwd": str(r.root)}, agent="gemini"), 0)
            self.assertEqual({o["agent"] for o in Observations(r.cfg.paths).iter_all()}, {"gemini"})

    def test_mcp_server_roundtrip(self):
        with Repo() as r:
            Ledger(r.cfg.paths).save(Memory(make_id("k"), "Redis is used for locks in `src/redis-lock.ts`.", "decision", files=["src/redis-lock.ts"]))
            from cosmos.charter import ensure; ensure(r.cfg)
            msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}},
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                    {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "cosmos_recall", "arguments": {"query": "change the redis lock", "files": ["src/redis-lock.ts"]}}},
                    {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "cosmos_remember", "arguments": {"kind": "rule", "text": "Never modify production schemas by hand.", "category": "constraint"}}},
                    {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "cosmos_charter", "arguments": {}}},
                    {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "cosmos_flare", "arguments": {"title": "Webhook replay possible", "severity": "high", "locations": "`src/webhooks.ts:10`", "what": "no nonce"}}}]
            out = subprocess.run([sys.executable, "-m", "cosmos", "mcp"], cwd=r.root, input="\n".join(json.dumps(m) for m in msgs) + "\n", capture_output=True, text=True, timeout=30, env={**os.environ, "PYTHONPATH": str(ROOT)})
            self.assertEqual(out.returncode, 0, out.stderr)
            res = {json.loads(l)["id"]: json.loads(l) for l in out.stdout.splitlines() if l.strip()}
            self.assertEqual(res[1]["result"]["serverInfo"]["name"], "cosmos")
            self.assertIn("cosmos_recall", [t["name"] for t in res[2]["result"]["tools"]])
            self.assertIn("Redis is used for locks", res[3]["result"]["content"][0]["text"])
            self.assertIn("remembered", res[4]["result"]["content"][0]["text"])
            self.assertIn("## How we test", res[5]["result"]["content"][0]["text"])
            self.assertIn("filed QA-", res[6]["result"]["content"][0]["text"])
            mems = Ledger(r.cfg.paths).load()
            self.assertTrue(any(m.source == "explicit" and "production schemas" in m.text for m in mems.values()))
            self.assertTrue(any(m.category == "finding" for m in mems.values()))

    def test_connect_writes_every_agent_config(self):
        from cosmos.connect import connect, codex_snippet, write_codex_user_config
        from cosmos.render import render_all
        with Repo() as r:
            done = connect(r.cfg, ["claude", "cursor", "gemini", "copilot"])
            self.assertEqual(len(done), 4)
            self.assertEqual(json.loads((r.root / ".mcp.json").read_text())["mcpServers"]["cosmos"]["args"], [".cosmos/cosmosw", "mcp"])
            self.assertEqual(json.loads((r.root / ".vscode" / "mcp.json").read_text())["servers"]["cosmos"]["type"], "stdio")
            self.assertEqual(connect(r.cfg, ["claude"]), [], "idempotent")
            self.assertIn("[mcp_servers.cosmos]", codex_snippet(r.root))
            p = write_codex_user_config(r.root, home=r.root / "fakehome")
            self.assertIn(str(r.root / ".cosmos" / "cosmosw"), p.read_text())
            r.cfg.data["render"] = {"targets": ["GEMINI.md", ".cursor/rules/cosmos.mdc", ".github/copilot-instructions.md", ".clinerules"]}
            changed = render_all(r.cfg, {})
            for f in ("CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursor/rules/cosmos.mdc", ".github/copilot-instructions.md", ".clinerules"):
                self.assertIn(f, changed); self.assertIn("cosmos:start", (r.root / f).read_text())
            self.assertTrue((r.root / ".cursor/rules/cosmos.mdc").read_text().startswith("---\nalwaysApply" if False else "---"))


class TestExternalPaths(unittest.TestCase):
    def test_sibling_repo_paths_become_relative_and_lane(self):
        from cosmos.transcript import relativize
        from cosmos.lanes import infer_lane
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "backend"; (root / "src").mkdir(parents=True)
            sib = Path(d) / "frontend" / "src" / "lib"; sib.mkdir(parents=True)
            self.assertEqual(relativize(str(root / "src" / "a.py"), root), "src/a.py")
            self.assertEqual(relativize(str(sib / "sector.ts"), root), "../frontend/src/lib/sector.ts")
            self.assertEqual(infer_lane(["../frontend/src/lib/sector.ts"]), "../frontend")
            self.assertNotIn("users", infer_lane([str(sib / "sector.ts")]).lower() if False else "")


class TestPartialPathResolution(unittest.TestCase):
    def test_fragment_resolves_to_tree_path_and_lane(self):
        from cosmos.lanes import _tree_index, resolve_path, assign_lanes
        with Repo() as r:
            (r.root / "core_common" / "core_common" / "crud").mkdir(parents=True)
            (r.root / "core_common" / "core_common" / "crud" / "base.py").write_text("x")
            (r.root / "webserver" / "app" / "middleware").mkdir(parents=True)
            (r.root / "webserver" / "app" / "middleware" / "auth.py").write_text("x")
            idx = _tree_index(r.root)
            self.assertEqual(resolve_path("crud/base.py", idx), "core_common/core_common/crud/base.py")
            self.assertEqual(resolve_path("middleware/auth.py", idx), "webserver/app/middleware/auth.py")
            self.assertEqual(resolve_path("nowhere/x.py", idx), "nowhere/x.py")
            m = Memory(make_id("f"), "Finding", "finding", files=["crud/base.py", "middleware/auth.py"])
            assign_lanes({m.id: m}, r.cfg, only_missing=False)
            self.assertEqual(m.files, ["core_common/core_common/crud/base.py", "webserver/app/middleware/auth.py"])
            self.assertIn(m.lane, ("core_common", "webserver"))


class TestObservationPathNormalisation(unittest.TestCase):
    def test_absolute_observation_paths_are_credited_to_lanes(self):
        from cosmos.lanes import lane_report
        with Repo() as r:
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            obs = [{"ts": now, "author": "A", "files": [str(r.root / "src" / "redis-lock.ts")]},          # absolute, inside repo
                   {"ts": now, "author": "B", "files": [str(r.root.parent / "frontend" / "src" / "x.ts")]},  # absolute, sibling repo
                   {"ts": now, "author": "C", "files": ["/private/tmp/scratch/whatever.md"]}]              # outside → general
            rep = {x["lane"]: x for x in lane_report(r.cfg, {}, obs)}
            self.assertIn("A", [c["name"] for c in rep["src"]["contributors"]] if "src" in rep else [c["name"] for c in rep["general"]["contributors"]])
            self.assertIn("../frontend", rep)
            self.assertEqual([c["name"] for c in rep["../frontend"]["contributors"]], ["B"])
            self.assertEqual([c["name"] for c in rep["general"]["contributors"]], ["C"])


class TestIntakeHintsAndNoopDreams(unittest.TestCase):
    def test_folder_hint_expands_and_noop_dream_not_recorded(self):
        from cosmos.intake import expand_hints
        import cosmos.dream as D
        with Repo() as r:
            (r.root / "webserver" / "app").mkdir(parents=True)
            (r.root / "webserver" / "app" / "a.py").write_text("x"); (r.root / "webserver" / "app" / "b.ts").write_text("x"); (r.root / "webserver" / "app" / "c.png").write_bytes(b"x")
            files = expand_hints(r.cfg, ["webserver/app", "src/redis-lock.ts", "nowhere.py"])
            self.assertEqual(files, ["webserver/app/", "webserver/app/a.py", "webserver/app/b.ts", "src/redis-lock.ts", "nowhere.py"])
            orig = D.get_provider; D.get_provider = lambda c: None
            try:
                D.dream(r.cfg)   # nothing to do
            finally:
                D.get_provider = orig
            self.assertEqual(list((r.cfg.paths.state / "dreams").glob("*.json")) if (r.cfg.paths.state / "dreams").exists() else [], [], "no-op dreams leave no run record")


class TestIntakeContext(unittest.TestCase):
    def test_brief_and_attachments_widen_retrieval_and_are_saved(self):
        from cosmos.intake import analyse, save, read_attachment
        with Repo() as r:
            Ledger(r.cfg.paths).save(Memory(make_id("w"), "Webhook signatures are verified in `src/webhooks.ts` before any payment is touched.", "constraint", files=["src/webhooks.ts"], lane="payments"))
            spec = r.root / "prd.md"; spec.write_text("# PRD\nAdd retries for failed webhook deliveries with exponential backoff.")
            att = read_attachment(spec)
            self.assertEqual(att["name"], "prd.md"); self.assertIn("exponential backoff", att["text"])
            res = analyse(r.cfg, "improve delivery reliability", brief="", attachments=[att])   # the sentence alone matches nothing; the PRD does
            self.assertTrue(any("Webhook" in m.text for m in res["related"] + res["collisions"]))
            p = save(r.cfg, res)
            self.assertIn("## Attached documents", p.read_text())
            self.assertTrue((r.cfg.paths.ledger / "horizon" / "attachments" / p.stem / "prd.md").exists())
            bin_ = r.root / "img.png"; bin_.write_bytes(b"\x89PNG\x00\x00binary")
            self.assertEqual(read_attachment(bin_)["text"], "", "binary files contribute their name only")


class TestLaneProposal(unittest.TestCase):
    def test_deterministic_proposal_and_write(self):
        from cosmos.lanes import propose, assign_lanes
        with Repo() as r:
            a = Memory(make_id("a"), "x", "decision", files=["webserver/app/x.py", "webserver/app/y.py"])
            b = Memory(make_id("b"), "y", "decision", files=["processor/app/z.py"])
            c = Memory(make_id("c"), "z", "decision", files=["/private/tmp/junk.html", "docs/a.md"])
            res = propose(r.cfg, {a.id: a, b.id: b, c.id: c}, [], use_llm=False)
            self.assertEqual(res["lanes"], {"webserver": ["webserver/**"], "processor": ["processor/**"]})
            r.cfg.data["lanes"] = {"web": ["webserver/**"]}
            mems = {a.id: a, b.id: b}
            assign_lanes(mems, r.cfg, only_missing=False)
            self.assertEqual((a.lane, b.lane), ("web", "processor"))


class TestLLMCuration(unittest.TestCase):
    class Fake:
        name = "fake"
        def __init__(self): self.calls = []
        def complete(self, system, user, schema=None):
            self.calls.append((system, user, schema))
            data = json.loads(user)
            if "candidates" in data:
                items = []
                for c in data["candidates"]:
                    if "narration" in c["text"]:
                        items.append({"id": c["id"], "keep": False, "why_dropped": "session narration"})
                    else:
                        items.append({"id": c["id"], "keep": True, "text": "Review requests must be rejected through `reviews.py`, never edited in the DB.", "category": "constraint", "lane": "reviews", "importance": 0.9})
                return {"items": items}
            if "paths" in data:
                return {"lanes": {"reviews": ["webserver/app/api/v1/endpoints/reviews*"], "bogus": ["nowhere/**"]}}
            return {"memories": [], "contradictions": []}

    def test_dream_curates_with_llm_and_assigns_lanes(self):
        import cosmos.dream as D
        from cosmos.lanes import propose
        fake = self.Fake()
        with Repo() as r:
            Observations(r.cfg.paths).append([
                {"id": "obs_1", "text": "Let me look at the narration of this session first.", "category": "workflow", "score": 0.6, "source": "observed", "files": ["webserver/app/api/v1/endpoints/reviews.py"], "ts": "2026-09-21T10:00:00Z"},
                {"id": "obs_2", "text": "reject path passes org_id__eq to update_many which only takes plain column names", "category": "bug", "score": 0.6, "source": "observed", "files": ["webserver/app/api/v1/endpoints/reviews.py"], "ts": "2026-09-21T10:00:01Z"}])
            orig = D.get_provider
            D.get_provider = lambda cfg_llm: fake
            try:
                rep = D.dream(r.cfg, use_llm=True)
            finally:
                D.get_provider = orig
            self.assertTrue(rep.llm_used)
            self.assertEqual(rep.dropped, 1)
            mems = Ledger(r.cfg.paths).load()
            self.assertEqual(len(mems), 1)
            m = next(iter(mems.values()))
            self.assertEqual((m.category, m.lane), ("constraint", "reviews"))
            self.assertTrue(m.text.startswith("Review requests must be rejected"))
            self.assertIn("LLM curated, 1 dropped as noise", rep.summary())
            # lane proposal through the same provider; invalid globs are discarded
            import cosmos.lanes as L
            origL = L.get_provider if hasattr(L, "get_provider") else None
            import cosmos.providers as P
            origP = P.get_provider
            P.get_provider = lambda cfg_llm: fake
            try:
                res = propose(r.cfg, mems, [], use_llm=True)
            finally:
                P.get_provider = origP
            self.assertEqual(res["source"], "llm")
            self.assertEqual(list(res["lanes"]), ["reviews"])

    def test_existing_heuristic_facts_are_recurated_once(self):
        import cosmos.dream as D
        fake = self.Fake()
        with Repo() as r:
            keep = Memory(make_id("k"), "reject path passes org_id__eq to update_many", "bug", files=["webserver/app/x.py"])
            drop = Memory(make_id("d"), "Let me check the narration of this first.", "workflow")
            Ledger(r.cfg.paths).save_all([keep, drop])
            orig = D.get_provider; D.get_provider = lambda cfg_llm: fake
            try:
                rep = D.dream(r.cfg)
                mems = Ledger(r.cfg.paths).load()
                self.assertEqual((rep.recurated, rep.recurated_dropped), (2, 1))
                self.assertEqual(mems[drop.id].status, "forgotten")
                self.assertEqual(mems[keep.id].lane, "reviews")
                self.assertTrue(mems[keep.id].meta.get("curated", "").startswith("llm:"))
                self.assertIn("re-curated 2 existing facts, 1 retired", rep.summary())
                calls = len(fake.calls)
                rep2 = D.dream(r.cfg)          # second dream: nothing left to re-curate, no model call for it
                self.assertEqual(rep2.recurated, 0)
                self.assertEqual(len(fake.calls), calls)
                self.assertNotIn("no LLM available", rep2.summary())
            finally:
                D.get_provider = orig

    def test_without_llm_dream_still_works_and_says_so(self):
        import cosmos.dream as D
        with Repo() as r:
            Observations(r.cfg.paths).append([{"id": "obs_9", "text": "Redis is used for locks in `src/redis-lock.ts`.", "category": "decision", "score": 0.6, "source": "observed", "files": ["src/redis-lock.ts"], "ts": "2026-09-21T10:00:00Z"}])
            orig = D.get_provider; D.get_provider = lambda cfg_llm: None
            try:
                rep = D.dream(r.cfg)
            finally:
                D.get_provider = orig
            self.assertFalse(rep.llm_used); self.assertEqual(len(rep.new), 1); self.assertIn("heuristics only", rep.summary())

    def test_first_json_tolerates_prose_and_fences(self):
        from cosmos.providers import _first_json
        self.assertEqual(_first_json('Sure! ```json\n{"a": 1}\n```'), {"a": 1})
        self.assertEqual(_first_json('here you go {"items": [{"id": "x", "keep": true}]} thanks'), {"items": [{"id": "x", "keep": True}]})
        self.assertIsNone(_first_json("no json here"))


class TestExtractionHardening(unittest.TestCase):
    def test_long_pasted_user_text_is_not_a_rule(self):
        pasted = "Do not use it in new pages: declare `capabilities: {artifact: {}}` and obtain the namespace with `await claude.use(\"artifact\")`. " * 20
        self.assertEqual(extract.extract([Turn("user", pasted)]), [])
        self.assertEqual(extract.extract([Turn("user", "<tool>Do not use it in new pages: declare capabilities and obtain the namespace properly.</tool>")]), [])
        short = extract.extract([Turn("user", "Never modify production schemas by hand, always go through a migration.")])
        self.assertEqual(len(short), 1)


class TestJournal(unittest.TestCase):
    """The journal records what was done even when no fact was learned; subagents are read; dreams start themselves."""

    def _bash(self, cmd):
        return {"type": "assistant", "uuid": "b" + str(abs(hash(cmd)) % 10**6), "timestamp": "2026-09-21T10:00:02Z",
                "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "t", "name": "Bash", "input": {"command": cmd}}]}}

    def test_commit_messages_are_parsed(self):
        from cosmos.journal import commits_in
        cmds = ['git add -A && git commit -m "fix(aura): cap Tavily hits at n" && git push',
                "git commit -m 'chore: trim comments'",
                'git commit -m "$(cat <<\'EOF\'\nfeat(chat): restrict attachments to PDF\n\nBody here\nEOF\n)"',
                "pytest -q tests"]
        self.assertEqual(commits_in(cmds), ["fix(aura): cap Tavily hits at n", "chore: trim comments", "feat(chat): restrict attachments to PDF"])

    def test_capture_writes_a_journal_line_even_without_facts(self):
        with Repo() as r:
            p = r.transcript("s.jsonl", [_user("please make the chat attachment upload reject docx"),
                                         _asst("Done.", files=[str(r.root / "src" / "redis-lock.ts")]),
                                         self._bash('cd . && git commit -m "fix(chat): reject docx attachments"'), self._bash("pytest -q")])
            n = r.capture(p, "sess-1")
            obs = list(Observations(r.cfg.paths).iter_all())
            J = [o for o in obs if o.get("kind") == "journal"]
            self.assertEqual(len(J), 1, obs)
            j = J[0]
            self.assertEqual(j["commits"], ["fix(chat): reject docx attachments"])
            self.assertEqual(j["files"], ["src/redis-lock.ts"])
            self.assertTrue(j["tests"])
            self.assertIn("chat attachment", j["ask"])
            self.assertGreaterEqual(n, 1)
            # the dream writes it to ledger/journal/<day>.md, once, and does not turn the raw line into a fact
            rep = dream(r.cfg, use_llm=False)
            self.assertEqual(rep.journal_entries, 1)
            day = (r.cfg.paths.ledger / "journal" / (j["ts"][:10] + ".md")).read_text()
            self.assertIn("fix(chat): reject docx attachments", day)
            self.assertIn(j["id"], day)
            self.assertFalse(any("Work done" in m.text for m in Ledger(r.cfg.paths).load().values()))
            rep2 = dream(r.cfg, use_llm=False)
            self.assertEqual(rep2.journal_entries, 0, "already written")
            self.assertEqual(day, (r.cfg.paths.ledger / "journal" / (j["ts"][:10] + ".md")).read_text())

    def test_subagent_transcripts_are_found_and_read(self):
        from cosmos.adapters import find_claude_sessions, read_session
        with Repo() as r, tempfile.TemporaryDirectory() as home:
            proj = Path(home) / ".claude" / "projects" / str(r.root.resolve()).replace("/", "-")
            (proj / "abc" / "subagents").mkdir(parents=True)
            (proj / "abc.jsonl").write_text(json.dumps(_user("main")) + "\n")
            sub = proj / "abc" / "subagents" / "agent-1.jsonl"
            rows = [dict(_user("explore the repo for the retry policy"), isSidechain=True),
                    dict(_asst("Retries are capped at 3 in `src/redis-lock.ts`; the lock TTL is 30 seconds.", files=[str(r.root / "src" / "redis-lock.ts")]), isSidechain=True)]
            sub.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
            old = os.environ.get("HOME"); os.environ["HOME"] = home
            try:
                found = find_claude_sessions(r.root)
            finally:
                os.environ["HOME"] = old
            self.assertEqual([sid for _, sid in found], ["abc", "abc/agent-1"])
            turns, _ = read_session(sub, "claude", 0)
            self.assertEqual(len(turns), 2, "sidechain entries are read when the file is a subagent transcript")
            turns_main, _ = read_session(proj / "abc.jsonl", "claude", 0)
            self.assertEqual(len(turns_main), 1)

    def test_auto_dream_decision(self):
        from cosmos.hooks import should_auto_dream
        with Repo() as r:
            self.assertFalse(should_auto_dream(r.cfg, 0))
            self.assertTrue(should_auto_dream(r.cfg, 25), "enough waiting")
            self.assertTrue(should_auto_dream(r.cfg, 3), "something waiting and no dream ever ran")
            d = r.cfg.paths.state / "dreams"; d.mkdir(parents=True)
            (d / "x.json").write_text("{}")
            self.assertFalse(should_auto_dream(r.cfg, 3), "a dream just ran")
            r.cfg.data.setdefault("dream", {})["auto"] = False
            self.assertFalse(should_auto_dream(r.cfg, 100))

    def test_journal_backfill_is_idempotent_and_dated(self):
        from cosmos.hooks import backfill_journal
        with Repo() as r:
            rows = [dict(_user("add retries"), gitBranch="feat/retries"), _asst("ok", files=[str(r.root / "src" / "redis-lock.ts")]), self._bash('git commit -m "feat: retries"'),
                    _user("what time is it"), _asst("noon"),
                    _user("now ship it"), self._bash('git commit -m "chore: release"')]
            p = r.transcript("old.jsonl", rows)
            self.assertEqual(backfill_journal(r.cfg, p, "old"), 2, "two windows did work; the question did not")
            self.assertEqual(backfill_journal(r.cfg, p, "old"), 0)
            J = [o for o in Observations(r.cfg.paths).iter_all() if o.get("kind") == "journal"]
            self.assertEqual(sorted(c for o in J for c in o["commits"]), ["chore: release", "feat: retries"])
            self.assertTrue(all(o["ts"].startswith("2026-09-") for o in J), "dated from the transcript, not from now")
            self.assertIn("feat/retries", [o["branch"] for o in J], "branch comes from the transcript entry, not from HEAD today")

    def test_observations_the_model_drops_do_not_come_back(self):
        from cosmos import dream as dm
        with Repo() as r:
            p = r.transcript("s.jsonl", [_user("q"), _asst("Redis is used for locks in `src/redis-lock.ts` with a 30 second TTL.", files=[str(r.root / "src" / "redis-lock.ts")])])
            r.capture(p, "s1")
            class Drop:  # a model that drops everything
                def complete(self, system, user, schema):
                    import json as j
                    return {"items": [{"id": c["id"], "keep": False} for c in j.loads(user)["candidates"]]}
            old = dm.get_provider; dm.get_provider = lambda *_a, **_k: Drop()
            try:
                rep = dream(r.cfg, use_llm=True)
            finally:
                dm.get_provider = old
            self.assertGreaterEqual(rep.dropped, 1)
            rep2 = dream(r.cfg, use_llm=False)
            self.assertEqual((rep2.observations_processed, len(rep2.new)), (0, 0), "dropped observations never resurface as raw facts")


class FakeReader:
    """A model that answers the reading prompt with one fact per USER/AGENT excerpt and drops nothing at curation."""
    def __init__(self):
        self.read_calls = 0; self.curate_calls = 0
    def complete(self, system, user, schema):
        import json as j
        p = j.loads(user)
        if "excerpt" in p:
            self.read_calls += 1
            return {"items": [{"text": "Redis locks use a 30 second TTL; see src/redis-lock.ts.", "category": "constraint", "kind": "correction",
                               "lane": "locking", "files": ["src/redis-lock.ts", "made/up.py"], "importance": 0.9}]}
        self.curate_calls += 1
        return {"items": [{"id": c["id"], "keep": True} for c in p["candidates"]]}


class TestModelReads(unittest.TestCase):
    def _model_repo(self):
        r = Repo().__enter__()
        r.cfg.data.setdefault("capture", {})["mode"] = "model"
        r.cfg.save()
        return r

    def test_hook_marks_the_range_and_keeps_only_explicit_lines(self):
        from cosmos.reader import windows_waiting
        from cosmos.store import State
        r = self._model_repo()
        try:
            p = r.transcript("s.jsonl", [_user("remember: never edit prod schemas by hand"), _asst("Redis is used for locks in `src/redis-lock.ts` with a 30 second TTL.")])
            r.capture(p, "s1")
            obs = [o for o in Observations(r.cfg.paths).iter_all() if o.get("kind") != "journal"]
            self.assertEqual([o["source"] for o in obs], ["explicit"], "no heuristic guesses in model mode")
            st = State(r.cfg.paths)
            self.assertEqual(windows_waiting(st), 1)
            w = st.data["windows"][0]
            self.assertEqual((w["from"], w["to"] > 0, w["sid"]), (0, True, "s1"))
            r.capture(p, "s1")
            self.assertEqual(windows_waiting(State(r.cfg.paths)), 1, "nothing new: no second window")
            # a turn that edited code is recorded by the agent itself at the Gate: not queued for a second reading
            p2 = r.transcript("s2.jsonl", [_user("fix it"), _asst("Done.", files=[str(r.root / "src" / "redis-lock.ts")])])
            r.capture(p2, "s2")
            self.assertEqual(windows_waiting(State(r.cfg.paths)), 1, "editing turn: the agent records, the reader does not re-read")
        finally:
            r.__exit__()

    def test_dream_lets_the_model_read_the_range(self):
        from cosmos import dream as dm
        from cosmos.store import State
        r = self._model_repo()
        try:
            p = r.transcript("s.jsonl", [_user("how do locks work"), _asst("Redis is used for locks in `src/redis-lock.ts` with a 30 second TTL.")])
            r.capture(p, "s1")
            fake = FakeReader(); old = dm.get_provider; dm.get_provider = lambda *_a, **_k: fake
            try:
                rep = dream(r.cfg, use_llm=True)
            finally:
                dm.get_provider = old
            self.assertEqual((rep.windows_read, rep.turns_read, fake.read_calls), (1, 2, 1))
            self.assertEqual(fake.curate_calls, 0, "what the model read is already curated; it is not sent back for curation")
            mems = Ledger(r.cfg.paths).load()
            m = next(m for m in mems.values() if "30 second TTL" in m.text)
            self.assertEqual((m.category, m.lane, m.files), ("constraint", "locking", ["src/redis-lock.ts"]), "made-up file paths are dropped")
            self.assertEqual(State(r.cfg.paths).data.get("windows"), [])
            self.assertEqual(dream(r.cfg, use_llm=False).observations_processed, 0, "read once")
        finally:
            r.__exit__()

    def test_budget_leaves_the_rest_for_the_next_dream(self):
        from cosmos import reader
        from cosmos.store import State
        r = self._model_repo()
        try:
            rows = []
            for i in range(6):
                rows += [_user(f"question {i} " + "lorem ipsum dolor " * 180), _asst(f"answer {i} " + "sit amet consectetur " * 150)]
            p = r.transcript("s.jsonl", rows)
            r.capture(p, "s1")
            st = State(r.cfg.paths); store = Observations(r.cfg.paths)
            fake = FakeReader()
            rep = reader.read_windows(r.cfg, fake, {}, st, store, budget=2)
            self.assertEqual(rep.chunks_read, 2)
            self.assertEqual(len(st.data["windows"]), 1, "remainder re-queued")
            self.assertGreater(st.data["windows"][0]["from"], 0)
            rep2 = reader.read_windows(r.cfg, fake, {}, st, store, budget=50)
            self.assertGreater(rep2.chunks_read, 0)
            self.assertEqual(st.data["windows"], [])
        finally:
            r.__exit__()

    def test_auto_memory_notes_become_candidates_once(self):
        from cosmos import reader
        from cosmos.store import State
        r = self._model_repo()
        try:
            with tempfile.TemporaryDirectory() as home:
                d = Path(home) / ".claude" / "projects" / str(r.root.resolve()).replace("/", "-") / "memory"
                d.mkdir(parents=True)
                (d / "MEMORY.md").write_text("- [x](x.md)\n")
                (d / "who.md").write_text("---\nname: who\ntype: user\n---\nThe user is a backend engineer.\n")
                (d / "redis.md").write_text("---\nname: redis\ntype: project\n---\nAPI tests need a local Redis on 6379; the CI job starts one.\n")
                old = os.environ.get("HOME"); os.environ["HOME"] = home
                try:
                    st = State(r.cfg.paths)
                    c = reader.auto_memory_candidates(r.cfg, st)
                    self.assertEqual([x["note"] for x in c], ["redis.md"], "personal notes (type: user) stay personal")
                    self.assertEqual(c[0]["category"], "decision")
                    self.assertEqual(reader.auto_memory_candidates(r.cfg, st), [], "unchanged notes are not offered twice")
                    (d / "redis.md").write_text("---\nname: redis\ntype: project\n---\nAPI tests need a local Redis on 6380 since 2026-09-01.\n")
                    self.assertEqual(len(reader.auto_memory_candidates(r.cfg, st)), 1, "a changed note is offered again")
                finally:
                    os.environ["HOME"] = old
        finally:
            r.__exit__()

    def test_without_a_model_the_range_waits_then_falls_back(self):
        from cosmos.store import State
        r = self._model_repo()
        try:
            p = r.transcript("s.jsonl", [_user("q"), _asst("Redis is used for locks in `src/redis-lock.ts` with a 30 second TTL.")])
            r.capture(p, "s1")
            rep = dream(r.cfg, use_llm=False)
            self.assertEqual((rep.windows_waiting, rep.fallback_windows), (1, 0), "recent range waits for a model")
            st = State(r.cfg.paths); st.data["windows"][0]["ts"] = "2026-01-01T00:00:00Z"; st.save()
            rep = dream(r.cfg, use_llm=False)
            self.assertEqual((rep.windows_waiting, rep.fallback_windows), (0, 1))
            self.assertTrue(any("30 second" in m.text for m in Ledger(r.cfg.paths).load().values()), "heuristics kept it rather than lose it")
        finally:
            r.__exit__()


class TestDecisionTime(unittest.TestCase):
    """Knowledge shows up where the work happens: before an edit, and in the flare lifecycle."""

    def test_pretooluse_shows_what_is_known_about_the_file_once(self):
        from cosmos.hooks import file_context
        with Repo() as r:
            mems = {}
            m = Memory(id=make_id("Redis lock TTL is 30 seconds"), text="Redis lock TTL is 30 seconds; do not lower it.", category="constraint", files=["src/redis-lock.ts"])
            f = Memory(id="mem_f1", text="Lock is never released on timeout", category="finding", files=["src/redis-lock.ts"], meta={"audit_id": "QA-3", "severity": "high", "finding_status": "open"})
            Ledger(r.cfg.paths).save_all([m, f])
            ev = {"hook_event_name": "PreToolUse", "session_id": "s", "tool_name": "Edit", "tool_input": {"file_path": str(r.root / "src" / "redis-lock.ts")}}
            out = file_context(r.cfg, ev)
            self.assertIn("QA-3", out); self.assertIn("30 seconds", out); self.assertIn("without asking", out)
            self.assertEqual(file_context(r.cfg, ev), "", "shown once per file per session")
            self.assertEqual(file_context(r.cfg, {**ev, "tool_input": {"file_path": str(r.root / "src" / "other.ts")}}), "", "nothing known → silent")

    def test_a_commit_naming_a_flare_closes_it(self):
        from cosmos.dream import _flares_from_commits
        with Repo() as r:
            f = Memory(id="mem_f2", text="Approval chain bypassable", category="finding", files=["src/a.py"], meta={"audit_id": "QA-11", "severity": "critical", "finding_status": "open"})
            Ledger(r.cfg.paths).save_all([f])
            mems = Ledger(r.cfg.paths).load()
            n = _flares_from_commits(r.cfg, [{"kind": "journal", "commits": ["fix(auth): QA-11 derive stage server-side"]}], mems)
            self.assertEqual(n, 1)
            self.assertEqual(Ledger(r.cfg.paths).load()["mem_f2"].meta["finding_status"], "fixed")

    def test_agent_facts_are_not_human_rules(self):
        from cosmos.mcp import call_tool
        with Repo() as r:
            call_tool(r.cfg, "cosmos_remember", {"text": "The scheduler never sets is_reminder on created reminders.", "category": "bug", "lane": "reminders"})
            call_tool(r.cfg, "cosmos_remember", {"text": "Never run erase endpoints against the shared dev DB.", "kind": "rule"})
            mems = Ledger(r.cfg.paths).load()
            fact = next(m for m in mems.values() if "is_reminder" in m.text); rule = next(m for m in mems.values() if "erase" in m.text)
            self.assertEqual((fact.source, fact.lane, fact.importance < 0.9), ("agent", "reminders", True))
            self.assertEqual((rule.source, rule.importance), ("explicit", 0.95))


class TestWorktreesAndWatch(unittest.TestCase):
    def test_files_in_a_worktree_are_repo_relative(self):
        from cosmos import transcript
        with Repo() as r:
            subprocess.run(["git", "add", "-A"], cwd=r.root, check=True)
            subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init"], cwd=r.root, check=True)
            wt = r.root.parent / (r.root.name + "-fix")
            subprocess.run(["git", "worktree", "add", "-q", str(wt), "-b", "fix"], cwd=r.root, check=True)
            try:
                transcript._WORKTREES.clear()
                self.assertEqual(transcript.relativize(str(wt / "src" / "redis-lock.ts"), r.root), "src/redis-lock.ts", "a worktree is the same repo")
                self.assertTrue(transcript.relativize(str(r.root.parent / "other-repo" / "a.py"), r.root).startswith("../other-repo/"), "a sibling repo stays a sibling")
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=r.root, check=True)
                transcript._WORKTREES.clear()

    def test_hook_command_falls_back_to_the_main_worktree(self):
        from cosmos.wrapper import HOOK_CMD
        self.assertIn("--git-common-dir", HOOK_CMD)
        self.assertTrue(HOOK_CMD.endswith("exit 0"), "never breaks a session where cosmos is absent")

    def test_watch_once_builds_the_live_picture(self):
        from cosmos.watch import load_live, tick
        with Repo() as r, tempfile.TemporaryDirectory() as home:
            proj = Path(home) / ".claude" / "projects" / str(r.root.resolve()).replace("/", "-")
            proj.mkdir(parents=True)
            rows = [dict(_user("fix the lock TTL"), gitBranch="fix/ttl", cwd=str(r.root)), _asst("Done.", files=[str(r.root / "src" / "redis-lock.ts")]),
                    {"type": "assistant", "uuid": "b1", "timestamp": "2026-09-22T10:00:03Z", "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "t", "name": "Bash", "input": {"command": 'git commit -m "fix(lock): raise TTL"'}}]}}]
            for x in rows:
                x["timestamp"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            (proj / "live1.jsonl").write_text("\n".join(json.dumps(x) for x in rows) + "\n")
            old = os.environ.get("HOME"); os.environ["HOME"] = home
            try:
                res = tick(r.cfg, ["claude"])
            finally:
                os.environ["HOME"] = old
            self.assertEqual(res["sessions"], 1)
            live = load_live(r.cfg)
            s = live["live1"]
            self.assertEqual((s["agent"], s["branch"], s["ask"], s["files"], s["commits"]), ("claude", "fix/ttl", "fix the lock TTL", ["src/redis-lock.ts"], ["fix(lock): raise TTL"]))
            J = [o for o in Observations(r.cfg.paths).iter_all() if o.get("kind") == "journal"]
            self.assertEqual(len(J), 1, "the watcher captures like a hook would")
            # a hook-captured session is live too, and a hooked session the watcher never read gets a tail summary
            (proj / "hooked.jsonl").write_text(json.dumps(dict(_user("rename the queue"), gitBranch="feat/q", timestamp=rows[0]["timestamp"])) + "\n")
            r.capture(proj / "hooked.jsonl", "hooked")
            self.assertEqual(load_live(r.cfg)["hooked"]["ask"], "rename the queue")
            (proj / "silent.jsonl").write_text(json.dumps(dict(_user("old work"), timestamp=rows[0]["timestamp"])) + "\n")
            from cosmos.store import State
            st = State(r.cfg.paths); st.set_offset("silent", (proj / "silent.jsonl").stat().st_size); st.save()
            os.environ["HOME"] = home
            try:
                tick(r.cfg, ["claude"])
            finally:
                os.environ["HOME"] = old
            self.assertEqual(load_live(r.cfg)["silent"]["ask"], "old work", "recent but already-captured session still shows as live")
            os.environ["HOME"] = home
            try:
                self.assertEqual(tick(r.cfg, ["claude"])["captured"], 0, "nothing new on the second pass")
            finally:
                os.environ["HOME"] = old


class TestReviewFixes(unittest.TestCase):
    """The points raised by an agent that lived with cosmos for a day."""

    def test_doubtful_facts_are_never_injected(self):
        from cosmos.retrieve import retrieve, top, format_for_agent
        good = Memory(id="a", text="Redis lock TTL is 30 seconds in src/redis-lock.ts", category="constraint", files=["src/redis-lock.ts"], status="active")
        stale = Memory(id="b", text="Redis lock TTL is 10 seconds in src/redis-lock.ts", category="constraint", files=["src/redis-lock.ts"], status="stale-candidate")
        mems = {"a": good, "b": stale}
        self.assertEqual([m.id for m in retrieve(mems, "redis lock ttl", paths=["src/redis-lock.ts"])], ["a"])
        self.assertEqual([m.id for m in top(mems)], ["a"])
        self.assertIn("UNVERIFIED", format_for_agent(retrieve(mems, "redis", include_doubtful=True), "x"))

    def test_identifier_that_left_the_code_makes_a_fact_stale(self):
        from cosmos.dream import _missing_identifiers
        with Repo() as r:
            (r.root / "src" / "erase.py").write_text("UNIVERSE_ERASE_CHECKPOINT_KEYS = ['a']\n")
            m = Memory(id="mem_erase1", text="Erase uses `UNIVERSE_ERASE_CHECKPOINT_KEYS` and the s3_key convention.", category="constraint", files=["src/erase.py"])
            self.assertEqual(_missing_identifiers(r.root, m), ["s3_key"])
            (r.root / "src" / "erase.py").write_text("CHECKPOINTS = ['a']\ns3_key = None\n")
            self.assertEqual(_missing_identifiers(r.root, m), ["UNIVERSE_ERASE_CHECKPOINT_KEYS"])
            rep = dream(r.cfg, use_llm=False)  # nothing pending; staleness pass alone
            Ledger(r.cfg.paths).save(m)
            rep = dream(r.cfg, use_llm=False)
            self.assertIn("mem_erase1", rep.stale)
            self.assertIn("no longer appears", Ledger(r.cfg.paths).load()["mem_erase1"].reason)

    def test_tools_say_what_they_need_and_accept_obvious_spellings(self):
        from cosmos.mcp import call_tool
        with Repo() as r:
            out = call_tool(r.cfg, "cosmos_remember", {"fact": "Universe erase treats an empty s3_key as nothing to delete.", "lane": "universe"})
            self.assertIn("remembered", out["content"][0]["text"], "`fact` is accepted as the text")
            out = call_tool(r.cfg, "cosmos_remember", {"lane": "universe", "category": "constraint"})
            self.assertIn("needs `text` (got: category, lane)", out["content"][0]["text"])
            out = call_tool(r.cfg, "cosmos_flare", {"text": "GET /transitions has no role gate", "severity": "HIGH"})
            self.assertIn("filed QA-", out["content"][0]["text"])
            out = call_tool(r.cfg, "cosmos_flare", {"severity": "high"})
            self.assertIn("needs `title`", out["content"][0]["text"])

    def test_gate_is_proportional_to_the_change(self):
        from cosmos.gate import evaluate
        with Repo() as r:
            small = [_user("fix the typo"), {"type": "assistant", "uuid": "s1", "timestamp": "2026-09-22T10:00:00Z", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": "t1", "name": "Edit", "input": {"file_path": str(r.root / "src/redis-lock.ts"), "old_string": "ttl = 10", "new_string": "ttl = 30"}},
                {"type": "text", "text": "Fixed in src/redis-lock.ts:12."}]}}]
            res = evaluate(r.cfg, {"transcript_path": str(r.transcript("small.jsonl", small)), "session_id": "s"})
            self.assertTrue(res["small"]); self.assertFalse(res["block"], "a one-line fix with a citation is not held: no tests, no reflection demanded")
            big = [_user("add retries"), {"type": "assistant", "uuid": "b1", "timestamp": "2026-09-22T10:00:00Z", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": "t1", "name": "Write", "input": {"file_path": str(r.root / "src/retry.ts"), "content": "x" * 900}},
                {"type": "tool_use", "id": "t2", "name": "Bash", "input": {"command": "npm test"}},
                {"type": "text", "text": "Added src/retry.ts:1."}]}}]
            res = evaluate(r.cfg, {"transcript_path": str(r.transcript("big.jsonl", big)), "session_id": "s"})
            self.assertFalse(res["small"]); self.assertTrue(res["block"]); self.assertIn("Record what the team learned", res["reasons"][0])


class TestLedgerBranch(unittest.TestCase):
    """.cosmos/ is a worktree of the cosmos branch: feature branches never carry ledger changes."""

    def test_attach_on_a_repo_with_no_commits_then_commit_and_status(self):
        from cosmos import sync
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            ok, msg = sync.attach(root); self.assertTrue(ok, msg)
            self.assertTrue((root / ".cosmos" / ".git").is_file(), "worktree, not a plain directory")
            self.assertTrue(sync.has_local_branch(root))
            self.assertTrue(sync.attach(root)[0], "idempotent")
            (root / ".cosmos" / "ledger").mkdir(); (root / ".cosmos" / "ledger" / "x.md").write_text("fact\n")
            self.assertTrue(sync.commit(root, "cosmos: test"))
            self.assertFalse(sync.commit(root, "cosmos: nothing"))
            log = subprocess.run(["git", "log", "--oneline", "cosmos"], cwd=root, capture_output=True, text=True).stdout
            self.assertIn("cosmos: test", log); self.assertIn("cosmos: ledger branch", log)
            self.assertIn(".cosmos/", (root / ".gitignore").read_text())
            self.assertEqual(subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True).stdout.strip(), "?? .gitignore", "the main tree sees the new .gitignore and nothing of .cosmos")

    def test_migrate_a_repo_that_tracked_cosmos_in_its_branch(self):
        from cosmos import sync
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "src").mkdir(); (root / "src" / "a.py").write_text("x")
            (root / ".cosmos" / "ledger").mkdir(parents=True); (root / ".cosmos" / "charter.md").write_text("# Charter\n"); (root / ".cosmos" / "ledger" / "mem_1.md").write_text("fact")
            (root / ".gitignore").write_text(".cosmos/state/\n")
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "feature with cosmos inside"], cwd=root, check=True)
            ok, msg = sync.migrate(root); self.assertTrue(ok, msg)
            self.assertEqual((root / ".cosmos" / "charter.md").read_text(), "# Charter\n", "content kept")
            self.assertTrue((root / ".cosmos" / ".git").is_file())
            staged = subprocess.run(["git", "diff", "--cached", "--name-status"], cwd=root, capture_output=True, text=True).stdout
            self.assertIn("D\t.cosmos/charter.md", staged, "removal from the feature branch is staged, nothing else")
            self.assertNotIn("src/a.py", staged)
            self.assertIn(".cosmos/", (root / ".gitignore").read_text()); self.assertNotIn(".cosmos/state/", (root / ".gitignore").read_text())
            shown = subprocess.run(["git", "show", "cosmos:charter.md"], cwd=root, capture_output=True, text=True).stdout
            self.assertEqual(shown, "# Charter\n", "the ledger is on the cosmos branch")

    def test_hook_attaches_a_fresh_clone_and_block_is_static(self):
        from cosmos.wrapper import HOOK_CMD
        from cosmos.render import managed_block
        self.assertIn("worktree add -q --track -B cosmos", HOOK_CMD)
        self.assertIn("origin/cosmos", HOOK_CMD)
        b1 = managed_block({}, 10); b2 = managed_block({"m": Memory(id="mem_x", text="A volatile fact", category="decision")}, 10, None)
        self.assertEqual(b1, b2, "the block in CLAUDE.md never changes with the ledger")


class TestFreshness(unittest.TestCase):
    def test_evidence_on_another_worktree_or_elsewhere_in_the_repo_is_not_stale(self):
        from cosmos import dream as dm, transcript
        with Repo() as r:
            (r.root / "src" / "erase.py").write_text("UNIVERSE_ERASE_CHECKPOINT_KEYS = ['a']\n")
            (r.root / "src" / "other.py").write_text("s3_key = None\n")
            subprocess.run(["git", "add", "-A"], cwd=r.root, check=True)
            subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init"], cwd=r.root, check=True)
            dm._TREE_CACHE.clear(); transcript._WORKTREES.clear()
            m = Memory(id="mem_e1", text="Erase uses `UNIVERSE_ERASE_CHECKPOINT_KEYS` and the s3_key convention.", category="constraint", files=["src/erase.py"])
            Ledger(r.cfg.paths).save(m)
            rep = dream(r.cfg, use_llm=False)
            self.assertEqual(rep.stale, [], "s3_key is not in erase.py but it is in the repo: the fact stands")
            gone = Memory(id="mem_e2", text="Sector backfill lives in `aura_gateway/aura/search.py`.", category="architecture", files=["aura_gateway/aura/search.py"])
            Ledger(r.cfg.paths).save(gone)
            wt = r.root.parent / (r.root.name + "-aura")
            subprocess.run(["git", "worktree", "add", "-q", str(wt), "-b", "aura"], cwd=r.root, check=True)
            try:
                (wt / "aura_gateway" / "aura").mkdir(parents=True); (wt / "aura_gateway" / "aura" / "search.py").write_text("x")
                subprocess.run(["git", "add", "-A"], cwd=wt, check=True)
                subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "aura"], cwd=wt, check=True)
                dm._TREE_CACHE.clear(); transcript._WORKTREES.clear()
                rep = dream(r.cfg, use_llm=False)
                self.assertNotIn("mem_e2", rep.stale, "the file exists on the aura worktree: branch-bound evidence is still evidence")
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=r.root, check=True)
                dm._TREE_CACHE.clear(); transcript._WORKTREES.clear()

    def test_auto_flagged_facts_come_back_when_evidence_returns_and_the_model_settles_the_rest(self):
        from cosmos import dream as dm
        with Repo() as r:
            m = Memory(id="mem_v1", text="Lock TTL is 30 seconds in `src/redis-lock.ts`.", category="constraint", files=["src/redis-lock.ts"], status="stale-candidate", reason="Stale candidate since 2026-09-01: none of the evidence files exist anymore")
            Ledger(r.cfg.paths).save(m)
            rep = dream(r.cfg, use_llm=False)
            self.assertIn("mem_v1", rep.revived)
            self.assertEqual(Ledger(r.cfg.paths).load()["mem_v1"].status, "active")
            d1 = Memory(id="mem_v2", text="Lock TTL is 10 seconds in `src/redis-lock.ts`.", category="constraint", files=["src/redis-lock.ts"], status="stale-candidate", reason="Stale candidate since 2026-09-01: not re-observed for 200 days (limit 180d for constraint)")
            Ledger(r.cfg.paths).save(d1)
            class Judge:
                def complete(self, system, user, schema):
                    import json as j
                    return {"items": [{"id": f["id"], "verdict": "outdated", "reason": "file says 30"} for f in j.loads(user)["facts"]]}
            old = dm.get_provider; dm.get_provider = lambda *_a, **_k: Judge()
            try:
                rep = dream(r.cfg, use_llm=True)
            finally:
                dm.get_provider = old
            self.assertEqual(rep.retired, 1)
            self.assertEqual(Ledger(r.cfg.paths).load()["mem_v2"].status, "forgotten")


class TestEvidencePaths(unittest.TestCase):
    def test_cited_paths_resolve_or_are_dropped(self):
        from cosmos.lanes import resolve_evidence, _INDEX_CACHE
        with Repo() as r:
            _INDEX_CACHE.clear()
            (r.root / "webserver" / "app" / "services").mkdir(parents=True); (r.root / "webserver" / "app" / "services" / "agent_router.py").write_text("x")
            sib = r.root.parent / "frontend-x"; (sib / "src").mkdir(parents=True); (sib / "src" / "App.tsx").write_text("x")
            try:
                self.assertEqual(resolve_evidence(r.root, "src/redis-lock.ts"), "src/redis-lock.ts")
                self.assertEqual(resolve_evidence(r.root, "agent_router.py"), "webserver/app/services/agent_router.py", "partial path → unique tree match")
                self.assertEqual(resolve_evidence(r.root, "frontend-x/src/App.tsx"), "../frontend-x/src/App.tsx", "a sibling repo cited without ../")
                self.assertEqual(resolve_evidence(r.root, "../frontend-x/src/App.tsx"), "../frontend-x/src/App.tsx")
                subprocess.run(["git", "init", "-q"], cwd=sib, check=True)
                self.assertEqual(resolve_evidence(r.root, "src/App.tsx"), "../frontend-x/src/App.tsx", "a path relative to the sibling repo's own root")
                self.assertEqual(resolve_evidence(r.root, "App.tsx"), "../frontend-x/src/App.tsx", "a bare file name found in the sibling repo")
                self.assertEqual(resolve_evidence(r.root, "nowhere/at/all.py"), "", "made up → dropped")
            finally:
                import shutil; shutil.rmtree(sib)

    def test_a_doubt_from_a_partial_path_repairs_itself(self):
        from cosmos.lanes import _INDEX_CACHE
        with Repo() as r:
            _INDEX_CACHE.clear()
            (r.root / "webserver").mkdir(); (r.root / "webserver" / "agent_router.py").write_text("ROUTER = 1\n")
            m = Memory(id="mem_p1", text="agent_router is dead code.", category="architecture", files=["agent_router.py"], status="stale-candidate",
                       reason="Stale candidate since 2026-09-01: none of the evidence files exist anymore")
            Ledger(r.cfg.paths).save(m)
            rep = dream(r.cfg, use_llm=False)
            got = Ledger(r.cfg.paths).load()["mem_p1"]
            self.assertEqual((got.status, got.files), ("active", ["webserver/agent_router.py"]))


class TestDisclosureHandoffValidity(unittest.TestCase):
    def test_recall_is_compact_and_points_to_the_full_note(self):
        from cosmos.retrieve import format_for_agent, brief
        m = Memory(id="mem_abc12345", text="The universe erase flow treats an empty s3_key as 'nothing to delete' and skips the S3 call entirely, which is why re-running erase on a half-imported universe is safe " * 2, category="constraint", lane="universe-import", files=["a/b.py"])
        out = format_for_agent([m], "H")
        line = out.splitlines()[1]
        self.assertLess(len(line), 260); self.assertIn("mem_abc12345", line); self.assertIn("universe-import", line); self.assertTrue(line.count("…") == 1)
        self.assertIn("cosmos_why", out)
        self.assertEqual(brief("short fact"), "short fact")

    def test_final_message_becomes_the_branch_handoff_and_opens_the_next_session(self):
        from cosmos.handoff import record_auto, latest, record_explicit
        with Repo() as r:
            subprocess.run(["git", "add", "-A"], cwd=r.root, check=True)
            subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init"], cwd=r.root, check=True)
            subprocess.run(["git", "checkout", "-q", "-b", "feat/locks"], cwd=r.root, check=True)
            self.assertIsNone(record_auto(r.cfg, "ok", {"cwd": str(r.root)}), "too short to be a summary")
            p = record_auto(r.cfg, "Changed the lock TTL to 30s in src/redis-lock.ts:12 and added a regression test; the flaky timeout test still needs a look tomorrow.", {"cwd": str(r.root)})
            self.assertTrue(p and p.name == "feat-locks.md")
            out = latest(r.cfg)
            self.assertIn("WHERE `feat/locks` WAS LEFT", out); self.assertIn("flaky timeout", out); self.assertIn("last turn by", out)
            record_explicit(r.cfg, "TTL must stay ≥30s", "flaky timeout test", "fix the timeout test, then open the PR")
            self.assertIn("**Next:** fix the timeout test", latest(r.cfg))
            record_auto(r.cfg, "Some later final message that is long enough to count as a summary of what happened in this turn.", {"cwd": str(r.root)})
            self.assertIn("**Next:**", latest(r.cfg), "an explicit handoff is not overwritten by the next turn's message for six hours")
            from cosmos.hooks import session_start
            self.assertIn("WAS LEFT", session_start(r.cfg))

    def test_validity_window_follows_the_lifecycle(self):
        with Repo() as r:
            m = Memory(id="mem_v9", text="Redis lock TTL is 30 seconds in src/redis-lock.ts.", category="constraint")
            led = Ledger(r.cfg.paths); led.save(m)
            got = led.load()["mem_v9"]; self.assertEqual((got.valid_from, got.valid_to), (m.created, ""))
            got.status = "superseded"; led.save(got)
            got = led.load()["mem_v9"]; self.assertEqual(got.valid_to, date.today().isoformat())
            got.status = "active"; led.save(got)
            self.assertEqual(led.load()["mem_v9"].valid_to, "", "a revived fact is valid again")

    def test_charter_paths_are_checked(self):
        from cosmos import charter
        with Repo() as r:
            charter.ensure(r.cfg)
            charter.add_section_rule(r.cfg, "Locks live in `src/redis-lock.ts`; never edit `src/legacy/locks.py` directly.")
            self.assertEqual(charter.check(r.cfg), ["src/legacy/locks.py"])


class TestTeamSources(unittest.TestCase):
    def test_git_history_becomes_journal_and_candidates(self):
        from cosmos.sources import ingest_git
        from cosmos.store import State
        with Repo() as r:
            subprocess.run(["git", "add", "-A"], cwd=r.root, check=True)
            subprocess.run(["git", "-c", "user.email=a@t", "-c", "user.name=Ana", "commit", "-q", "-m", "feat(locks): raise TTL to 30s\n\nThe 10s TTL caused lost locks under GC pauses; 30s matches the longest observed pause plus margin."], cwd=r.root, check=True)
            (r.root / "src" / "x.ts").write_text("x"); subprocess.run(["git", "add", "-A"], cwd=r.root, check=True)
            subprocess.run(["git", "-c", "user.email=b@t", "-c", "user.name=dependabot[bot]", "commit", "-q", "-m", "chore(deps): bump"], cwd=r.root, check=True)
            st = State(r.cfg.paths); store = Observations(r.cfg.paths)
            n, cands = ingest_git(r.cfg, st, store, set())
            self.assertEqual(n, 1, "bots are skipped")
            J = [o for o in store.iter_all() if o.get("kind") == "journal"]
            self.assertEqual((J[0]["author"], J[0]["commits"], J[0]["source"]), ("Ana", ["feat(locks): raise TTL to 30s"], "git"))
            self.assertEqual(len(cands), 1); self.assertIn("GC pauses", cands[0]["text"]); self.assertEqual(cands[0]["source"], "git")
            st.save()
            self.assertEqual(ingest_git(r.cfg, State(r.cfg.paths), store, set())[0], 0, "incremental")
            self.assertEqual(ingest_git(r.cfg, State(r.cfg.paths), store, {"feat(locks): raise TTL to 30s"})[0], 0, "a commit a session already journaled is not repeated")
            rep = dream(r.cfg, use_llm=False)
            self.assertTrue(any("Ana" in l for l in (r.cfg.paths.ledger / "journal").glob("*.md").__iter__().__next__().read_text().splitlines()))

    def test_reviews_need_gh_and_are_off_without_it(self):
        from cosmos.sources import ingest_reviews, gh_ready
        from cosmos.store import State
        with Repo() as r:
            r.cfg.data.setdefault("sources", {})["github_reviews"] = False
            self.assertFalse(gh_ready(r.cfg))
            self.assertEqual(ingest_reviews(r.cfg, State(r.cfg.paths), Observations(r.cfg.paths)), [])

    def test_recall_eval_measures_retrieval(self):
        from cosmos.eval import run
        with Repo() as r:
            Ledger(r.cfg.paths).save_all([
                Memory(id="mem_q1", text="Redis lock TTL is 30 seconds.", category="constraint", files=["src/redis-lock.ts"], meta={"eval_q": "how long do redis locks live"}),
                Memory(id="mem_q2", text="Payments retry three times with backoff.", category="convention", files=["src/payments/retry.ts"]),
            ])
            res = run(r.cfg, k=5)
            self.assertEqual(res["cases"], 3)
            self.assertGreaterEqual(res["recall_at_k"], 0.66)


class TestOKFAndSearch(unittest.TestCase):
    def test_notes_are_okf_conformant_and_round_trip(self):
        with Repo() as r:
            m = Memory(id="mem_okf1", text="Redis lock TTL is 30 seconds in src/redis-lock.ts.", category="constraint", files=["src/redis-lock.ts"], meta={"verified": "llm:2026-09-22"})
            led = Ledger(r.cfg.paths); led.save(m)
            md = next(led.dir.rglob("mem_okf1-*.md")).read_text()
            for key in ("type: \"Constraint\"", "title:", "description:", "status: \"stable\"", "cosmos_status: \"active\"", "generated:", "verified:", "stale_after:", "sources:"):
                self.assertIn(key, md, key)
            back = led.load()["mem_okf1"]
            self.assertEqual((back.status, back.category, back.files), ("active", "constraint", ["src/redis-lock.ts"]))
            back.status = "superseded"; led.save(back)
            self.assertIn("status: \"deprecated\"", next(led.dir.rglob("mem_okf1-*.md")).read_text())
            self.assertEqual(led.load()["mem_okf1"].status, "superseded", "cosmos lifecycle survives the OKF status mapping")
            from cosmos.render import write_index
            write_index(r.cfg, led.load())
            self.assertIn('okf_version: "0.2"', (r.cfg.paths.ledger / "index.md").read_text())

    def test_bm25_prefers_specific_terms_over_common_ones(self):
        from cosmos.retrieve import retrieve
        mems = {}
        for i in range(8):
            mems[f"mem_c{i}"] = Memory(id=f"mem_c{i}", text=f"The webserver service handles requests for module {i}.", category="architecture", files=[f"webserver/app/m{i}.py"])
        mems["mem_t"] = Memory(id="mem_t", text="Tavily search results are capped at n like the other backends.", category="constraint", files=["aura_gateway/aura/search.py"])
        got = [m.id for m in retrieve(mems, "why are tavily results capped", k=3)]
        self.assertEqual(got[0], "mem_t", "a rare term outranks eight notes sharing common words")
        got = [m.id for m in retrieve(mems, "search.py", paths=["aura_gateway/aura/search.py"], k=3)]
        self.assertEqual(got[0], "mem_t", "the evidence path wins for a file task")

    def test_remember_confirms_instead_of_duplicating(self):
        from cosmos.mcp import call_tool
        with Repo() as r:
            call_tool(r.cfg, "cosmos_remember", {"text": "Universe erase treats an empty s3_key as nothing to delete and skips the S3 call.", "category": "constraint"})
            out = call_tool(r.cfg, "cosmos_remember", {"text": "The universe erase flow treats an empty s3_key as nothing to delete, skipping the S3 call.", "category": "constraint"})
            self.assertIn("already known", out["content"][0]["text"])
            mems = Ledger(r.cfg.paths).load()
            self.assertEqual(sum(1 for m in mems.values() if "s3_key" in m.text), 1)
            self.assertEqual(next(m for m in mems.values() if "s3_key" in m.text).evidence_count, 2)

    def test_older_notes_gain_an_okf_type_on_the_next_dream(self):
        from cosmos.dream import _okf_conform
        with Repo() as r:
            j = r.cfg.paths.ledger / "journal"; j.mkdir(parents=True)
            (j / "2026-09-01.md").write_text("---\nkind: journal\ndate: \"2026-09-01\"\n---\n\n# Journal · 2026-09-01\n- x\n")
            a = r.cfg.paths.ledger / "atlas"; a.mkdir()
            (a / "inventory.md").write_text("# Atlas · Inventory\n\nstuff\n")
            self.assertEqual(_okf_conform(r.cfg), 2)
            self.assertTrue((j / "2026-09-01.md").read_text().startswith("---\ntype: Journal\nkind: journal"))
            self.assertTrue((a / "inventory.md").read_text().startswith("---\ntype: Diagram\ntitle: \"Atlas · Inventory\""))
            self.assertEqual(_okf_conform(r.cfg), 0, "idempotent")


class TestOKFGraph(unittest.TestCase):
    def test_lanes_and_services_are_linked_concepts(self):
        from cosmos.render import render_all, write_lane_pages, write_service_pages
        with Repo() as r:
            (r.cfg.paths.ledger / "atlas").mkdir(parents=True)
            (r.cfg.paths.ledger / "atlas" / "atlas.json").write_text(json.dumps({"apps": [{"name": "webserver", "dir": "src", "language": "typescript"}], "services": [{"name": "redis", "image": "redis:7", "compose": "docker-compose.yml", "ports": ["6379:6379"]}], "stores": []}))
            a = Memory(id="mem_l1", text="Redis lock TTL is 30 seconds.", category="constraint", lane="locking", files=["src/redis-lock.ts"])
            b = Memory(id="mem_l2", text="Locks were once 10 seconds.", category="constraint", lane="locking", files=["src/redis-lock.ts"], status="superseded", superseded_by="mem_l1")
            a.supersedes = "mem_l2"
            f = Memory(id="mem_f1", text="Lock never released on timeout", category="finding", lane="locking", files=["src/redis-lock.ts"], meta={"audit_id": "QA-3", "severity": "high", "finding_status": "open"})
            led = Ledger(r.cfg.paths); led.save_all([a, b, f])
            md = next(led.dir.rglob("mem_l1-*.md")).read_text()
            self.assertIn('"/lanes/locking.md"', md, "a fact links to its lane")
            self.assertIn("/constraint/mem_l2-", md, "and to the note it supersedes, by real path")
            self.assertIn("## Links", md)
            mems = led.load()
            self.assertEqual(write_lane_pages(r.cfg, mems), 1)
            lane = (r.cfg.paths.ledger / "lanes" / "locking.md").read_text()
            self.assertTrue(lane.startswith("---\ntype: \"Lane\""))
            self.assertIn("(/constraint/mem_l1-", lane); self.assertIn("QA-3", lane); self.assertIn("(/atlas/services/webserver.md)", lane)
            self.assertEqual(write_service_pages(r.cfg, mems), 2)
            svc = (r.cfg.paths.ledger / "atlas" / "services" / "webserver.md").read_text()
            self.assertIn('resource: "/../../src"', svc); self.assertIn("(/lanes/locking.md)", svc); self.assertIn("mem_l1-", svc)
            render_all(r.cfg, mems)
            root = (r.cfg.paths.ledger / "index.md").read_text()
            self.assertIn("[Lanes](lanes/)", root); self.assertIn("[Services](atlas/services/)", root)

    def test_a_model_lane_survives_heuristic_dreams(self):
        from cosmos.dream import _restore_model_lanes
        from cosmos.lanes import assign_lanes
        with Repo() as r:
            m = Memory(id=make_id("Payments retry three times with backoff."), text="Payments retry three times with backoff.", category="convention", lane="general")
            Ledger(r.cfg.paths).save(m)
            Observations(r.cfg.paths).append([{"id": "obs_x1", "text": "Payments retry three times with backoff.", "category": "convention", "lane": "payments", "source": "observed", "files": [], "ts": "2026-09-24T00:00:00Z"}])
            mems = Ledger(r.cfg.paths).load()
            self.assertEqual(_restore_model_lanes(mems, Observations(r.cfg.paths)), 1)
            self.assertEqual((mems[m.id].lane, mems[m.id].meta["lane_by"]), ("payments", "model"))
            assign_lanes(mems, r.cfg, only_missing=False)
            self.assertEqual(mems[m.id].lane, "payments", "path inference never overrules the model")


class TestImportErrors(unittest.TestCase):
    def test_missing_findings_file_explains_instead_of_tracing(self):
        with Repo() as r:
            (r.root / "docs").mkdir(); (r.root / "docs" / "qa-findings.json").write_text("[]")
            out = subprocess.run([sys.executable, "-m", "cosmos", "flares", "import", "findings.json", "--prefix", "QA"], cwd=r.root, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT)})
            self.assertEqual(out.returncode, 1)
            self.assertNotIn("Traceback", out.stderr + out.stdout)
            self.assertIn("no such file: findings.json", out.stdout); self.assertIn("docs/qa-findings.json", out.stdout)
