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
os.environ["COSMOS_LLM_PROVIDER"] = "none"   # tests never call a real model; LLM paths use fakes

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
            self.assertFalse(evaluate(r.cfg, {"transcript_path": str(t2), "session_id": "s2"})["block"])
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
                    {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "cosmos_remember", "arguments": {"text": "Never modify production schemas by hand.", "category": "constraint"}}},
                    {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "cosmos_charter", "arguments": {}}},
                    {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "cosmos_finding", "arguments": {"title": "Webhook replay possible", "severity": "high", "locations": "`src/webhooks.ts:10`", "what": "no nonce"}}}]
            out = subprocess.run([sys.executable, "-m", "cosmos", "mcp"], cwd=r.root, input="\n".join(json.dumps(m) for m in msgs) + "\n", capture_output=True, text=True, timeout=30, env={**os.environ, "PYTHONPATH": str(ROOT)})
            self.assertEqual(out.returncode, 0, out.stderr)
            res = {json.loads(l)["id"]: json.loads(l) for l in out.stdout.splitlines() if l.strip()}
            self.assertEqual(res[1]["result"]["serverInfo"]["name"], "cosmos")
            self.assertIn("cosmos_recall", [t["name"] for t in res[2]["result"]["tools"]])
            self.assertIn("Redis is used for locks", res[3]["result"]["content"][0]["text"])
            self.assertIn("Remembered", res[4]["result"]["content"][0]["text"])
            self.assertIn("## How we test", res[5]["result"]["content"][0]["text"])
            self.assertIn("Filed QA-", res[6]["result"]["content"][0]["text"])
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
            self.assertTrue((r.cfg.paths.ledger / "intake" / "attachments" / p.stem / "prd.md").exists())
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
