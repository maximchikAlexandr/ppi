"""Unit tests for history value objects, git plan/parse, and history plan."""

from __future__ import annotations

import pytest

from ppi.history.git_parse import (
    GitCommitInfo,
    GitParseError,
    parse_commit_list,
    parse_git_show_commit,
)
from ppi.history.git_plan import (
    GitCommand,
    cmd_add_worktree,
    cmd_checkout_commit,
    cmd_current_branch,
    cmd_git_version,
    cmd_list_non_merge_commits,
    cmd_prune_worktrees,
    cmd_remove_worktree,
    cmd_show_commit,
    cmd_verify_branch,
)
from ppi.history.history_plan import (
    AddonsScanRoots,
    build_history_plan,
)
from ppi.history.mappers import placeholder_commit_ref, to_commit_ref
from ppi.history.value_objects import (
    AuthorEmail,
    BranchName,
    BranchNotFound,
    CommitHash,
    CommitOrder,
    DefaultBranch,
    DetachedHead,
    EpochSeconds,
    ExplicitBranch,
    GitCommandError,
    GitExecutableMissing,
    HeadAlias,
    RepoPath,
    WorktreePath,
    branch_input_from_cli,
    format_git_failure,
)

# --- value_objects ---------------------------------------------------------


def test_commit_hash_ok():
    assert str(CommitHash.of("abc123")) == "abc123"


def test_commit_hash_parse_none():
    assert CommitHash.parse("nothex") is None
    assert CommitHash.parse("") is None


def test_commit_hash_rejects_invalid():
    with pytest.raises(ValueError):
        CommitHash.of("xyz!")


def test_branch_name_ok():
    assert str(BranchName.of("main")) == "main"


def test_branch_name_rejects_invalid():
    with pytest.raises(ValueError):
        BranchName.of("bad name")


def test_commit_order_ok():
    assert int(CommitOrder.of(0)) == 0


def test_commit_order_rejects_negative():
    with pytest.raises(ValueError):
        CommitOrder.of(-1)


def test_epoch_seconds_parse():
    assert int(EpochSeconds.parse("1700")) == 1700
    assert EpochSeconds.parse("notint") is None
    assert EpochSeconds.parse("-1") is None


def test_author_email_rejects_whitespace():
    with pytest.raises(ValueError):
        AuthorEmail.of("bad email")


def test_repo_path_rejects_relative():
    with pytest.raises(ValueError):
        RepoPath.of("rel")


def test_worktree_path_rejects_relative():
    with pytest.raises(ValueError):
        WorktreePath.of("rel")


def test_branch_input_from_cli():
    assert isinstance(branch_input_from_cli(None), DefaultBranch)
    assert isinstance(branch_input_from_cli("HEAD"), HeadAlias)
    assert isinstance(branch_input_from_cli("main"), ExplicitBranch)


def test_format_git_failure():
    assert "detached" in format_git_failure(DetachedHead())
    assert format_git_failure(BranchNotFound(branch="x")) == "Branch not found: x"
    assert format_git_failure(GitCommandError(message="boom")) == "boom"
    assert "PATH" in format_git_failure(GitExecutableMissing())


# --- git_plan --------------------------------------------------------------


def test_git_command_full_args():
    cmd = GitCommand.of("/repo", "rev-parse", "HEAD")
    assert cmd.full_args == ("git", "-C", "/repo", "rev-parse", "HEAD")


def test_cmd_current_branch():
    assert cmd_current_branch(RepoPath.of("/r")).args == (
        "rev-parse",
        "--abbrev-ref",
        "HEAD",
    )


def test_cmd_verify_branch():
    assert cmd_verify_branch(RepoPath.of("/r"), BranchName.of("main")).args == (
        "rev-parse",
        "--verify",
        "main",
    )


def test_cmd_list_non_merge_commits():
    assert cmd_list_non_merge_commits(RepoPath.of("/r"), BranchName.of("main")).args == (
        "rev-list",
        "--no-merges",
        "--reverse",
        "main",
    )


def test_cmd_show_commit():
    cmd = cmd_show_commit(RepoPath.of("/r"), CommitHash.of("abc123"))
    assert cmd.args[0] == "show"
    assert cmd.args[-1] == "abc123"


def test_cmd_add_worktree():
    cmd = cmd_add_worktree(RepoPath.of("/r"), WorktreePath.of("/wt"), BranchName.of("main"))
    assert cmd.args == (
        "worktree",
        "add",
        "--detach",
        "/wt",
        "main",
    )


def test_cmd_checkout_commit():
    assert cmd_checkout_commit(WorktreePath.of("/wt"), CommitHash.of("abc123")).args == (
        "checkout",
        "--detach",
        "--quiet",
        "--force",
        "abc123",
    )


def test_cmd_remove_worktree():
    assert cmd_remove_worktree(RepoPath.of("/r"), WorktreePath.of("/wt")).args == (
        "worktree",
        "remove",
        "--force",
        "/wt",
    )


def test_cmd_prune_worktrees():
    assert cmd_prune_worktrees(RepoPath.of("/r")).args == ("worktree", "prune")


def test_cmd_git_version():
    assert cmd_git_version(RepoPath.of("/r")).full_args == ("git", "-C", "/r", "--version")


# --- git_parse -------------------------------------------------------------


def test_parse_git_show_commit_ok():
    raw = "abc123\x1fTest\x1ftest@example.com\x1f1700000000\x1f1700000001\x1finit"
    res = parse_git_show_commit(raw)
    assert res.is_ok()
    info = res.default_value(None)
    assert str(info.commit_hash) == "abc123"
    assert str(info.author_email) == "test@example.com"
    assert int(info.authored_at) == 1700000000
    assert info.summary == "init"


def test_parse_git_show_commit_empty():
    res = parse_git_show_commit("")
    assert res.is_error()
    assert res.error.reason == GitParseError.EMPTY_OUTPUT


def test_parse_git_show_commit_wrong_field_count():
    res = parse_git_show_commit("a\x1fb\x1fc\x1fd\x1fe")
    assert res.is_error()
    assert res.error.reason == GitParseError.WRONG_FIELD_COUNT


def test_parse_git_show_commit_invalid_hash():
    res = parse_git_show_commit("nothex\x1fb\x1fc\x1f1\x1f2\x1fs")
    assert res.is_error()
    assert res.error.reason == GitParseError.INVALID_HASH


def test_parse_git_show_commit_invalid_epoch():
    res = parse_git_show_commit("abc123\x1fb\x1fc\x1fnotint\x1f2\x1fs")
    assert res.is_error()
    assert res.error.reason == GitParseError.INVALID_EPOCH


def test_parse_commit_list():
    assert parse_commit_list("  a  \n\nb\n") == ("a", "b")


# --- mappers ---------------------------------------------------------------


def test_to_commit_ref():
    info = GitCommitInfo(
        commit_hash=CommitHash.of("abc123"),
        author_name="T",
        author_email=AuthorEmail.of("t@e.com"),
        authored_at=EpochSeconds.of(1),
        committed_at=EpochSeconds.of(2),
        summary="s",
    )
    ref = to_commit_ref(info, CommitOrder.of(3))
    assert ref.commit_hash == "abc123"
    assert ref.commit_order == 3
    assert ref.author_email == "t@e.com"
    assert ref.authored_at == 1


def test_placeholder_commit_ref():
    p = placeholder_commit_ref("dead", 0)
    assert p.commit_hash == "dead"
    assert p.author_name == ""


# --- history_plan ----------------------------------------------------------


def test_addons_scan_roots_inside(tmp_path):
    wt = tmp_path / "wt"
    wt.mkdir()
    (wt / "addons").mkdir()
    res = AddonsScanRoots.from_cli(wt, ["addons"])
    assert res.is_ok()
    assert len(res.default_value(None).roots) == 1


def test_addons_scan_roots_outside_rejected(tmp_path):
    wt = tmp_path / "wt"
    wt.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    res = AddonsScanRoots.from_cli(wt, [str(outside)])
    assert res.is_error()


def test_addons_scan_roots_empty_uses_worktree(tmp_path):
    wt = tmp_path / "wt"
    wt.mkdir()
    res = AddonsScanRoots.from_cli(wt, [])
    assert res.is_ok()
    roots = res.default_value(None)
    assert roots.roots[0].value == str(wt.resolve())


def test_addons_scan_roots_dotdot_rejected(tmp_path):
    wt = tmp_path / "wt"
    wt.mkdir()
    (tmp_path / "outside").mkdir()
    res = AddonsScanRoots.from_cli(wt, ["../outside"])
    assert res.is_error()


def test_build_history_plan_filters_skip():
    plan = build_history_plan(["a", "b", "c"], skip={"b"})
    assert plan.commits == ("a", "c")
    assert plan.order_by_hash["c"] == 2