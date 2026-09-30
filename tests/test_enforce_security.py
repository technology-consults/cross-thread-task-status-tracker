#!/usr/bin/env python3
"""Unit tests for scripts/enforce/security.py.

Convention: a main() printing "<N> passed, <M> failed", exit 0 on
success, 1 on failure.

Every trigger payload is built by string concatenation so this file's
own added lines never trip the gates it tests.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
MOD_PATH = os.path.join(REPO_ROOT, "scripts", "enforce", "security.py")

spec = importlib.util.spec_from_file_location("security_mod", MOD_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

_passed = 0
_failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
    else:
        _failed += 1
        print("FAIL: %s" % name)


def mdiff(files):
    """{path: (is_new, [(lineno, line), ...])} -> the module's diff dict."""
    return {"files": {p: {"is_new": n, "added": a}
                      for p, (n, a) in files.items()}}


# --- secrets -----------------------------------------------------------------

def test_secrets_aws_key():
    payload = 'KEY = "' + "AKIA" + "IOSFODNN7EXAMPLE" + '"'
    diff = mdiff({"scripts/x.py": (False, [(1, payload)])})
    out = mod.check_secrets(diff, REPO_ROOT, set())
    check("secrets: AWS key ID blocked",
          len(out) == 1 and out[0][0] == "secrets")


def test_secrets_pem_header():
    payload = "-----BEGIN " + "PRIVATE KEY-----"
    diff = mdiff({"scripts/x.py": (False, [(1, payload)])})
    out = mod.check_secrets(diff, REPO_ROOT, set())
    check("secrets: PEM header blocked",
          len(out) == 1 and out[0][0] == "secrets")


def test_secrets_assignment():
    payload = ("api" + "_key = " + chr(34) + "sk-1234567890abcdef" + chr(34))
    diff = mdiff({"scripts/x.py": (False, [(1, payload)])})
    out = mod.check_secrets(diff, REPO_ROOT, set())
    check("secrets: credential assignment blocked",
          len(out) == 1 and out[0][0] == "secrets")


def test_secrets_short_placeholder_passes():
    payload = "api" + "_key = " + chr(34) + "xxx" + chr(34)
    diff = mdiff({"scripts/x.py": (False, [(1, payload)])})
    check("secrets: short placeholder passes",
          mod.check_secrets(diff, REPO_ROOT, set()) == [])


def test_secrets_word_boundary():
    diff = mdiff({"scripts/x.py": (False, [(1, "tokenize(text)")])})
    check("secrets: 'tokenize' does not trip",
          mod.check_secrets(diff, REPO_ROOT, set()) == [])


def test_secrets_env_lookup_passes():
    diff = mdiff({"scripts/x.py":
                  (False, [(1, 'token = os.environ.get("GITHUB_TOKEN")')])})
    check("secrets: env lookup without a value passes",
          mod.check_secrets(diff, REPO_ROOT, set()) == [])


# --- token-in-log ------------------------------------------------------------

def test_token_in_log_fstring():
    payload = ("pr" + "int(" + "f" + chr(39) + "{sec" + "ret}" + chr(39)
               + ")")
    diff = mdiff({"scripts/x.py": (False, [(2, payload)])})
    out = mod.check_token_in_log(diff, REPO_ROOT, set())
    check("token-in-log: f-string interpolation blocked",
          len(out) == 1 and out[0][0] == "token-in-log")


def test_token_in_log_direct_var():
    payload = "pr" + "int(" + "sec" + "ret" + ")"
    diff = mdiff({"scripts/x.py": (False, [(2, payload)])})
    out = mod.check_token_in_log(diff, REPO_ROOT, set())
    check("token-in-log: credential var passed to print blocked",
          len(out) == 1 and out[0][0] == "token-in-log")


def test_token_in_log_label_passes():
    diff = mdiff({"scripts/x.py": (False, [(2, 'print("token expired")')])})
    check("token-in-log: mere word mention passes",
          mod.check_token_in_log(diff, REPO_ROOT, set()) == [])


def test_token_in_log_non_python_skipped():
    payload = "pr" + "int(" + "sec" + "ret" + ")"
    diff = mdiff({"notes.md": (False, [(1, payload)])})
    check("token-in-log: non-.py skipped",
          mod.check_token_in_log(diff, REPO_ROOT, set()) == [])


def test_token_in_log_allowlist():
    payload = "pr" + "int(" + "sec" + "ret" + ")"
    diff = mdiff({"scripts/debug.py": (False, [(1, payload)])})
    check("token-in-log: allowlisted path exempt",
          mod.check_token_in_log(diff, REPO_ROOT,
                                 {"scripts/debug.py"}) == [])


def main():
    test_secrets_aws_key()
    test_secrets_pem_header()
    test_secrets_assignment()
    test_secrets_short_placeholder_passes()
    test_secrets_word_boundary()
    test_secrets_env_lookup_passes()
    test_token_in_log_fstring()
    test_token_in_log_direct_var()
    test_token_in_log_label_passes()
    test_token_in_log_non_python_skipped()
    test_token_in_log_allowlist()
    print("%d passed, %d failed" % (_passed, _failed))
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
