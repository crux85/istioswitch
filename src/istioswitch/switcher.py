import os
import shutil
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

    bin_name = "istioctl.exe" if os_name == "windows" else "istioctl"
    target_bin = get_versions_dir() / version / bin_name
    link_path = bin_dir / bin_name

    # Clean up old links or shims
    for old_file in [link_path, bin_dir / "istioctl.bat", bin_dir / "istioctl.ps1"]:
        try:
            if old_file.exists() or old_file.is_symlink():
                old_file.unlink()
        except OSError:
            pass

    # Try creating a symlink, fallback to copying if not permitted (e.g., Windows non-admin)
    try:
        os.symlink(target_bin, link_path)
    except OSError:
        shutil.copy2(target_bin, link_path)

    if os_name != "windows":
        try:
            link_path.chmod(0o755)
        except OSError:
            pass

    set_active_version(version)

    # Check if bin_dir is in PATH
    in_path = str(bin_dir) in os.environ.get("PATH", "")
    return in_path, str(bin_dir)
