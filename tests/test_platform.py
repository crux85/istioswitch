import pytest
import sys
import platform
from istioswitch import platform_utils


def test_get_os_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert platform_utils.get_os() == "windows"


def test_get_os_macos(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert platform_utils.get_os() == "macos"


def test_get_os_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert platform_utils.get_os() == "linux"


def test_get_os_unsupported(monkeypatch):
    monkeypatch.setattr(sys, "platform", "freebsd")
    with pytest.raises(RuntimeError):
        platform_utils.get_os()


def test_get_arch_amd64(monkeypatch):
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    assert platform_utils.get_arch() == "amd64"


def test_get_arch_arm64(monkeypatch):
    monkeypatch.setattr(platform, "machine", lambda: "arm64")
    assert platform_utils.get_arch() == "arm64"


def test_get_arch_unsupported(monkeypatch):
    monkeypatch.setattr(platform, "machine", lambda: "mips")
    with pytest.raises(RuntimeError):
        platform_utils.get_arch()


def test_get_base_dir(mock_home):
    assert platform_utils.get_base_dir() == mock_home / ".istioswitch"


def test_get_asset_name(mock_os_arch):
    mock_os_arch("windows", "amd64")
    assert platform_utils.get_asset_name("1.0") == "istio-1.0-win.zip"

    mock_os_arch("linux", "amd64")
    assert platform_utils.get_asset_name("1.0") == "istio-1.0-linux-amd64.tar.gz"

    mock_os_arch("macos", "arm64")
    assert platform_utils.get_asset_name("1.0") == "istio-1.0-osx-arm64.tar.gz"
