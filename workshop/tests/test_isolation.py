import os
from pathlib import Path

import pytest
import yaml

from pr_review_workshop.contracts import ContractError
from pr_review_workshop.isolation import container_config, owned_path


def test_container_boundary():
    config = yaml.safe_load(Path("container/compose.yml").read_text())
    assert container_config(config)["safe_configuration"]
    config["services"]["review"]["volumes"].append("/var/run/docker.sock:/var/run/docker.sock")
    with pytest.raises(ContractError):
        container_config(config)


@pytest.mark.parametrize("field", ["privileged", "network_mode", "ports"])
def test_broader_runtime_refused(field):
    config = yaml.safe_load(Path("container/compose.yml").read_text())
    config["services"]["review"][field] = True
    with pytest.raises(ContractError):
        container_config(config)


def test_independent_files_only(tmp_path):
    original = tmp_path / "original"
    original.write_text("test")
    link = tmp_path / "link"
    link.symlink_to(original)
    with pytest.raises(ContractError):
        owned_path(tmp_path, link)
    hard = tmp_path / "hard"
    os.link(original, hard)
    with pytest.raises(ContractError):
        owned_path(tmp_path, hard)
    with pytest.raises(ContractError):
        owned_path(tmp_path, tmp_path.parent / "outside")


def test_distinct_skill_and_workspace_test_state():
    assert Path(".kiro/skills/workshop-prepare-pr/SKILL.md").is_file()
    assert not Path(".kiro/skills/kirocrew-prepare-pr").exists()
    assert "--basetemp=.work/pytest" in Path("pyproject.toml").read_text()
    dockerfile = Path("container/Dockerfile").read_text()
    assert "USER 65532:65532" in dockerfile and "EXPOSE" not in dockerfile
