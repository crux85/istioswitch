import platform
import sys
from pathlib import Path


def get_os() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    elif sys.platform.startswith("darwin"):
        return "macos"
    elif sys.platform.startswith("linux"):
        return "linux"
    raise RuntimeError(f"Unsupported OS: {sys.platform}")


def get_arch() -> str:
    machine = platform.machine().lower()
    if machine in ("amd64", "x86_64", "x64"):
        return "amd64"
    elif machine in ("arm64", "aarch64"):
        return "arm64"
    raise RuntimeError(f"Unsupported architecture: {machine}")


def get_base_dir() -> Path:
    return Path.home() / ".istioswitch"


def get_asset_name(version: str) -> str:
    os_name = get_os()
    arch = get_arch()

    if os_name == "windows":
        return f"istio-{version}-win.zip"
    elif os_name == "macos":
        return f"istio-{version}-osx-{arch}.tar.gz"
    elif os_name == "linux":
        return f"istio-{version}-linux-{arch}.tar.gz"
    raise RuntimeError(f"Unsupported OS: {os_name}")
