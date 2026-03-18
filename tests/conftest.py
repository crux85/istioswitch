import pytest
import sys
import platform
from pathlib import Path

@pytest.fixture
def mock_home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path

@pytest.fixture
def mock_os_arch(monkeypatch):
    def patch_os_arch(os_name="linux", arch="amd64"):
        if os_name == "windows":
            monkeypatch.setattr(sys, "platform", "win32")
        elif os_name == "macos":
            monkeypatch.setattr(sys, "platform", "darwin")
        else:
            monkeypatch.setattr(sys, "platform", "linux")
            
        if arch == "amd64":
            monkeypatch.setattr(platform, "machine", lambda: "x86_64")
        elif arch == "arm64":
            monkeypatch.setattr(platform, "machine", lambda: "arm64")
    return patch_os_arch
