import os
from pathlib import Path
from typing import Tuple

from istioswitch.platform_utils import get_base_dir, get_os
from istioswitch.config import set_active_version
from istioswitch.installer import get_versions_dir, is_installed

def use_version(version: str) -> Tuple[bool, str]:
    if not is_installed(version):
        raise ValueError(f"Version {version} is not installed.")
        
    bin_dir = get_base_dir() / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    os_name = get_os()
    
    target_bin = get_versions_dir() / version / ("istioctl.exe" if os_name == "windows" else "istioctl")
    
    if os_name == "windows":
        bat_shim = bin_dir / "istioctl.bat"
        bat_shim.write_text(f'@echo off\n"{target_bin}" %*')
        ps1_shim = bin_dir / "istioctl.ps1"
        ps1_shim.write_text(f'& "{target_bin}" @args')
    else:
        shim = bin_dir / "istioctl"
        shim.write_text(f'#!/bin/sh\nexec "{target_bin}" "$@"')
        shim.chmod(0o755)
        
    set_active_version(version)
    
    # Check if bin_dir is in PATH
    in_path = str(bin_dir) in os.environ.get("PATH", "")
    return in_path, str(bin_dir)
