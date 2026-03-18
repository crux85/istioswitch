import pytest
import os
from istioswitch import switcher, config

def test_use_version_linux(mock_home, mock_os_arch, monkeypatch):
    mock_os_arch("linux", "amd64")
    
    # fake installation
    ver_dir = mock_home / ".istioswitch" / "versions" / "1.0"
    ver_dir.mkdir(parents=True, exist_ok=True)
    (ver_dir / "istioctl").touch()
    
    monkeypatch.setattr(os, "environ", {"PATH": "/usr/bin"})
    
    in_path, bin_dir = switcher.use_version("1.0")
    
    assert not in_path
    assert config.get_active_version() == "1.0"
    
    shim = mock_home / ".istioswitch" / "bin" / "istioctl"
    assert shim.exists()
    assert "exec" in shim.read_text()

def test_use_version_windows(mock_home, mock_os_arch, monkeypatch):
    mock_os_arch("windows", "amd64")
    
    ver_dir = mock_home / ".istioswitch" / "versions" / "1.0"
    ver_dir.mkdir(parents=True, exist_ok=True)
    (ver_dir / "istioctl.exe").touch()
    
    bin_dir_path = mock_home / ".istioswitch" / "bin"
    monkeypatch.setattr(os, "environ", {"PATH": str(bin_dir_path)})
    
    in_path, bin_dir = switcher.use_version("1.0")
    
    assert in_path
    assert (bin_dir_path / "istioctl.bat").exists()
    assert (bin_dir_path / "istioctl.ps1").exists()

def test_use_not_installed(mock_home, mock_os_arch):
    mock_os_arch("linux", "amd64")
    with pytest.raises(ValueError):
        switcher.use_version("1.0")
