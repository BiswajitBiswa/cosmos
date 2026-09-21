"""`cosmos audit lint`: flag repository filter keys that are not real columns of the repository's model.

Generalised from a QA audit's filter check: `BaseRepository.apply_filters`-style helpers silently DROP
unknown keys, so a typo or an operator suffix (`org_id__eq`) on a model without that column becomes a no-op filter
(that class of bug produced two real findings). Pure AST over the call sites + one import of the repository modules.

Limits (be honest with the output): only literal dict keys at the call site are seen - keys built dynamically or
nested in a lookup table are invisible; models must expose `__table__.columns` or plain class attributes.
Runs in the target project's interpreter, so its dependencies must be importable (run it from the repo root).
"""
from __future__ import annotations

import ast
import glob
import importlib
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

DEFAULT_OPS = {"eq", "ne", "lt", "lte", "gt", "gte", "like", "ilike", "in", "notin", "isnull", "between", "contains", "array_overlap",
               "icontains", "overlap", "any", "eq_value", "contains_value", "jsonb_contains", "jsonb_overlap", "jsonb_array_overlap"}
DEFAULT_METHODS = ("get", "list", "update", "update_many", "delete", "count", "upsert")


@dataclass
class LintConfig:
    repo_base: str                      # "pkg.crud.base:BaseRepository"
    crud_glob: str                      # "pkg/pkg/crud/*.py"
    module_prefix: str                  # "pkg.crud."
    roots: List[str]                    # source roots to scan
    sys_path: List[str] = field(default_factory=list)
    ops: Set[str] = field(default_factory=lambda: set(DEFAULT_OPS))
    methods: Tuple[str, ...] = DEFAULT_METHODS
    registry: Set[str] = field(default_factory=set)         # model names allowed in dotted keys ("Company.name")
    plain_only_methods: Set[str] = field(default_factory=lambda: {"update_many"})   # reject operator suffixes


@dataclass(frozen=True)
class Issue:
    path: str
    line: int
    call: str
    key: str
    model: str
    kind: str        # not_a_column | suffix_not_supported

    def __str__(self) -> str:
        why = f"NOT a column of {self.model}" if self.kind == "not_a_column" else f"operator suffix not supported by {self.call.split('.')[-1]} (plain column names only; model {self.model})"
        return f"{self.path}:{self.line}  {self.call}  filter '{self.key}'  {why}"


def _cols(model: Any) -> Set[str]:
    out: Set[str] = set()
    table = getattr(model, "__table__", None)
    if table is not None and hasattr(table, "columns"):
        out |= {c.name for c in table.columns}
    out |= {k for k in vars(model) if not k.startswith("_")}
    return out


def load_repositories(cfg: LintConfig) -> Dict[str, Any]:
    for p in cfg.sys_path:
        if p not in sys.path:
            sys.path.insert(0, p)
    mod_name, _, cls_name = cfg.repo_base.partition(":")
    base = getattr(importlib.import_module(mod_name), cls_name)
    repos: Dict[str, Any] = {}
    for f in sorted(glob.glob(cfg.crud_glob)):
        mod = cfg.module_prefix + os.path.basename(f)[:-3]
        if mod == mod_name:
            continue
        try:
            m = importlib.import_module(mod)
        except Exception:
            continue
        for name, obj in vars(m).items():
            if isinstance(obj, base) and getattr(obj, "model", None) is not None:
                repos[name] = obj.model
    return repos


def lint(cfg: LintConfig, repos: Optional[Dict[str, Any]] = None) -> List[Issue]:
    repos = repos if repos is not None else load_repositories(cfg)
    issues: List[Issue] = []
    for root in cfg.roots:
        for dp, _, fs in os.walk(root):
            if "__pycache__" in dp:
                continue
            for fn in fs:
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(dp, fn)
                try:
                    tree = ast.parse(open(p, encoding="utf-8").read())
                except Exception:
                    continue
                for node in ast.walk(tree):
                    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)):
                        continue
                    var, meth = node.func.value.id, node.func.attr
                    model = repos.get(var)
                    if model is None or meth not in cfg.methods:
                        continue
                    dicts = [a for a in node.args if isinstance(a, ast.Dict)]
                    dicts += [k.value for k in node.keywords if k.arg == "filters" and isinstance(k.value, ast.Dict)]
                    if meth in ("update", "upsert", "update_many") and len(dicts) > 1:
                        dicts = dicts[:1]          # second dict is obj_in, not filters
                    valid = _cols(model)
                    for d in dicts:
                        for k in d.keys:
                            if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                                continue
                            key = k.value
                            if key in ("__or__", "__and__"):
                                continue
                            base_key, has_op = key, False
                            if "__" in key:
                                head, _, tail = key.rpartition("__")
                                if tail in cfg.ops and head:
                                    base_key, has_op = head, True
                            if has_op and meth in cfg.plain_only_methods:
                                issues.append(Issue(p, node.lineno, f"{var}.{meth}", key, model.__name__, "suffix_not_supported"))
                                continue
                            if "." in base_key and base_key.split(".")[0] in cfg.registry:
                                continue
                            if "->" in base_key or base_key in valid:
                                continue
                            issues.append(Issue(p, node.lineno, f"{var}.{meth}", key, model.__name__, "not_a_column"))
    return sorted(set(issues), key=lambda i: (i.path, i.line, i.key))


def config_from(cfg_audit: Dict[str, Any], overrides: Dict[str, Any]) -> LintConfig:
    d = dict(cfg_audit.get("lint", {}) or {})
    d.update({k: v for k, v in overrides.items() if v})
    missing = [k for k in ("repo_base", "crud_glob", "module_prefix", "roots") if not d.get(k)]
    if missing:
        raise SystemExit("lint needs " + ", ".join(missing) + " — pass flags or set .cosmos/config.json → audit.lint")
    return LintConfig(repo_base=d["repo_base"], crud_glob=d["crud_glob"], module_prefix=d["module_prefix"], roots=list(d["roots"]),
                      sys_path=list(d.get("sys_path", [])), ops=set(d.get("ops", DEFAULT_OPS)), methods=tuple(d.get("methods", DEFAULT_METHODS)),
                      registry=set(d.get("registry", [])), plain_only_methods=set(d.get("plain_only_methods", ["update_many"])))
