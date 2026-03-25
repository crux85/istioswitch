import hashlib
import shutil
import tarfile
import zipfile
import os
from pathlib import Path
from typing import List
import httpx
from rich.progress import Progress

from istioswitch.platform_utils import get_base_dir, get_asset_name, get_os


def _get_http_client() -> httpx.Client:
    """Returns an httpx.Client configured with system proxies if available."""
    proxy = (
        os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
    )
    no_proxy = os.environ.get("NO_PROXY") or os.environ.get("no_proxy")

    client_args = {}

    if proxy:
        client_args["proxy"] = proxy
        client_args["verify"] = False

        if no_proxy:
            # For httpx >= 0.24.0 we use mounts to bypass proxies
            mounts = {}
            for domain in no_proxy.split(","):
                domain = domain.strip()
                if domain:
                    mounts[f"all://*{domain}"] = None
            if mounts:
                client_args["mounts"] = mounts

    return httpx.Client(**client_args)


def get_versions_dir() -> Path:
    return get_base_dir() / "versions"


def get_installed_versions() -> List[str]:
    import re
    versions_dir = get_versions_dir()
    if not versions_dir.exists():
        return []
        
    versions = []
    for item in versions_dir.iterdir():
        if item.is_dir() and (item / "istioctl").exists() or (item / "istioctl.exe").exists():
            versions.append(item.name)
            
    def version_key(v):
        match = re.match(r'^v?(\d+)\.(\d+)\.(\d+)', v)
        if match:
            return tuple(int(x) for x in match.groups())
        return (0, 0, 0)
        
    versions.sort(key=version_key, reverse=True)
    return versions

def is_installed(version: str) -> bool:
    exe_name = "istioctl.exe" if get_os() == "windows" else "istioctl"
    return (get_versions_dir() / version / exe_name).exists()


def get_available_versions(limit: int = 20) -> List[str]:
    url = "https://api.github.com/repos/istio/istio/releases"
    try:
        with _get_http_client() as client:
            response = client.get(url, params={"per_page": 50}, timeout=10)
            response.raise_for_status()
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error fetching releases: {e}")

    import re
    versions = []
    for rel in response.json():
        if rel.get("prerelease") or rel.get("draft"):
            continue
        tag = rel["tag_name"]
        if tag:
            versions.append(tag)
            
    def version_key(v):
        match = re.match(r'^v?(\d+)\.(\d+)\.(\d+)', v)
        if match:
            return tuple(int(x) for x in match.groups())
        return (0, 0, 0)
        
    versions.sort(key=version_key, reverse=True)
    return versions[:limit]


def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest() == expected_hash


def download_file(url: str, dest: Path) -> None:
    try:
        with _get_http_client() as client:
            with client.stream(
                "GET", url, follow_redirects=True, timeout=30
            ) as response:
                if response.status_code == 404:
                    raise ValueError("Asset not found on GitHub")
                response.raise_for_status()
                total_size = int(response.headers.get("Content-Length", 0))
                with Progress() as progress:
                    task = progress.add_task("Downloading...", total=total_size)
                    with open(dest, "wb") as f:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))
    except httpx.RequestError as e:
        if dest.exists():
            dest.unlink()
        raise RuntimeError(f"Failed to download: {e}")


def fetch_expected_checksum(version: str, asset_name: str) -> str:
    url = f"https://github.com/istio/istio/releases/download/{version}/{asset_name}.sha256"
    try:
        with _get_http_client() as client:
            response = client.get(url, follow_redirects=True, timeout=10)
            if response.status_code == 404:
                raise ValueError("Checksum file not found")
            response.raise_for_status()
            content = response.text.strip()
            # Usually formatted as "HASH  filename"
            return content.split()[0]
    except httpx.RequestError as e:
        raise RuntimeError(f"Failed to fetch checksum: {e}")


def extract_binary(archive_path: Path, dest_dir: Path, version: str) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    os_name = get_os()
    binary_name = "istioctl.exe" if os_name == "windows" else "istioctl"

    version_clean = version.lstrip("v")
    expected_member = f"istio-{version_clean}/bin/{binary_name}"

    try:
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as z:
                with (
                    z.open(expected_member) as source,
                    open(dest_dir / binary_name, "wb") as target,
                ):
                    target.write(source.read())
        else:
            with tarfile.open(archive_path, "r:gz") as tar:
                member = tar.getmember(expected_member)
                f = tar.extractfile(member)
                if f:
                    with open(dest_dir / binary_name, "wb") as target:
                        target.write(f.read())

        if os_name != "windows":
            (dest_dir / binary_name).chmod(0o755)
    except (KeyError, tarfile.TarError, zipfile.BadZipFile) as e:
        raise RuntimeError(f"Binary extraction failed: {e}")


def install_version(version: str) -> None:
    if is_installed(version):
        return

    asset_name = get_asset_name(version)
    download_url = (
        f"https://github.com/istio/istio/releases/download/{version}/{asset_name}"
    )

    tmp_dir = get_base_dir() / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    archive_path = tmp_dir / asset_name

    try:
        download_file(download_url, archive_path)
        expected_checksum = fetch_expected_checksum(version, asset_name)
        if not verify_checksum(archive_path, expected_checksum):
            raise ValueError("Checksum verification failed.")

        target_dir = get_versions_dir() / version
        extract_binary(archive_path, target_dir, version)
    finally:
        if archive_path.exists():
            archive_path.unlink()


def uninstall_version(version: str) -> None:
    target_dir = get_versions_dir() / version
    if target_dir.exists():
        shutil.rmtree(target_dir)
    else:
        raise ValueError(f"Version {version} is not cached.")
