"""Runtime configuration checks, never setup or execution of an installed Crew."""

from pathlib import Path

from .contracts import require


def owned_path(root, path):
    root = Path(root).resolve()
    candidate = Path(path)
    candidate = candidate if candidate.is_absolute() else root / candidate
    require(candidate.resolve().is_relative_to(root), "Path leaves the workshop workspace")
    current = candidate
    while current != root:
        require(not current.is_symlink(), "Linked originals are not allowed")
        if current.is_file():
            require(current.stat().st_nlink == 1, "Hard-linked originals are not allowed")
        current = current.parent
    return candidate


def container_config(config):
    service = config["services"]["review"]
    require(service.get("ports", []) == [], "No container ports may be published")
    require(
        not service.get("privileged") and not service.get("network_mode"),
        "Privileged/host-network containers are not allowed",
    )
    require(service.get("read_only") is True, "Container root filesystem must be read-only")
    require(service.get("cap_drop") == ["ALL"], "Drop container capabilities")
    require(
        service.get("security_opt") == ["no-new-privileges:true"], "Disable privilege escalation"
    )
    require(service.get("volumes") == ["../:/workshop:ro"], "Only the workshop copy may be mounted")
    environment = service["environment"]
    require(environment.get("KIROCREW_HOME") == "/state/crew", "Crew state must be disposable")
    require(environment.get("WORKSHOP_ISOLATED") == "1", "Missing container runtime guard")
    require(
        "HOME" not in environment and "CODEX_HOME" not in environment,
        "Do not repurpose host configuration variables",
    )
    require(
        service.get("tmpfs") == ["/state", "/tmp"], "Runtime state must not persist on the host"
    )
    return {"safe_configuration": True, "live_runtime_verified": False}
