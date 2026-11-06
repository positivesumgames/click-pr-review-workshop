import subprocess

import pytest

from pr_review_workshop.contracts import ContractError
from pr_review_workshop.maintenance import MAINTAINER, git, refresh


def command(root, *args, stdin=None):
    result = subprocess.run(
        ["git", "-C", str(root), *args], input=stdin, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def commit_tree(root, tree, message, parents=()):
    args = [
        "-c",
        "user.name=Workshop test",
        "-c",
        "user.email=test@example.invalid",
        "commit-tree",
        tree,
        "-m",
        message,
    ]
    for parent in parents:
        args.extend(["-p", parent])
    return command(root, *args)


def repository(tmp_path):
    root = tmp_path / "maintainer"
    root.mkdir()
    command(root, "init", "-b", "main")
    (root / "click.txt").write_text("baseline\n")
    command(root, "add", "click.txt")
    base = commit_tree(root, command(root, "write-tree"), "upstream baseline")
    command(root, "update-ref", "refs/heads/main", base)
    command(root, "update-ref", "refs/remotes/upstream/main", base)
    (root / "workshop.txt").write_text("curriculum\n")
    command(root, "add", "workshop.txt")
    workshop = commit_tree(root, command(root, "write-tree"), "workshop", (base,))
    command(root, "update-ref", "refs/heads/main", workshop)
    command(root, "remote", "add", "origin", f"https://github.com/{MAINTAINER}.git")
    command(root, "remote", "add", "upstream", "https://github.com/pallets/click.git")
    return root, base, workshop


def test_refresh_keeps_curriculum_and_main(tmp_path):
    root, base, workshop = repository(tmp_path)
    (root / "click.txt").write_text("updated upstream\n")
    command(root, "add", "click.txt")
    command(root, "rm", "--cached", "workshop.txt")
    upstream = commit_tree(root, command(root, "write-tree"), "upstream update", (base,))
    command(root, "update-ref", "refs/remotes/upstream/main", upstream)
    command(root, "restore", "--source=main", "--staged", "--worktree", ".")
    result = refresh(root, MAINTAINER, "maintenance/test", fetch=False)
    assert result["merge_prepared"] and result["main_unchanged"]
    assert git(root, "rev-parse", "main") == workshop
    assert (root / "workshop.txt").read_text() == "curriculum\n"
    assert (root / "click.txt").read_text() == "updated upstream\n"


def test_dirty_refresh_refused(tmp_path):
    root, _, _ = repository(tmp_path)
    (root / "dirty").write_text("user work")
    with pytest.raises(ContractError, match="clean"):
        refresh(root, MAINTAINER, fetch=False)
    assert git(root, "branch", "--show-current") == "main"


def test_wrong_origin_refused(tmp_path):
    root, _, _ = repository(tmp_path)
    command(root, "remote", "set-url", "origin", "https://github.com/pallets/click.git")
    with pytest.raises(ContractError, match="origin"):
        refresh(root, MAINTAINER, fetch=False)


def test_fresh_learner_branches_share_main_not_upstream_history(tmp_path):
    maintainer, _, maintainer_head = repository(tmp_path)
    learner = tmp_path / "learner"
    learner.mkdir()
    command(learner, "init", "-b", "main")
    (learner / "workshop.txt").write_text((maintainer / "workshop.txt").read_text())
    command(learner, "add", ".")
    new_head = commit_tree(learner, command(learner, "write-tree"), "generated template")
    command(learner, "update-ref", "refs/heads/main", new_head)
    command(learner, "switch", "-c", "exercise")
    assert command(learner, "merge-base", "main", "exercise") == new_head
    assert new_head != maintainer_head
