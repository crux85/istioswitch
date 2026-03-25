import pytest
import tarfile
import zipfile
import hashlib
from io import BytesIO
from unittest.mock import MagicMock
from istioswitch import installer
import httpx


def test_get_installed_versions(mock_home, mock_os_arch):
    mock_os_arch("linux", "amd64")
    versions_dir = mock_home / ".istioswitch" / "versions"

    # Not created yet
    assert installer.get_installed_versions() == []

    versions_dir.mkdir(parents=True)

    # Create fake installed versions
    (versions_dir / "1.20.0").mkdir()
    (versions_dir / "1.20.0" / "istioctl").touch()

    (versions_dir / "1.19.5").mkdir()
    (versions_dir / "1.19.5" / "istioctl").touch()

    (versions_dir / "2.0.0").mkdir()
    (versions_dir / "2.0.0" / "istioctl.exe").touch()  # Test windows naming

    # Create empty dir (should be ignored)
    (versions_dir / "1.18.0").mkdir()

    installed = installer.get_installed_versions()
    # It should sort semantically: 2.0.0, 1.20.0, 1.19.5
    assert installed == ["2.0.0", "1.20.0", "1.19.5"]


def test_get_available_versions(monkeypatch):
    mock_get = MagicMock()
    mock_get.return_value.json.return_value = [
        {"tag_name": "1.2.3", "prerelease": False, "draft": False},
        {"tag_name": "1.2.4-rc1", "prerelease": True, "draft": False},
        {"tag_name": "1.2.2", "prerelease": False, "draft": False},
    ]
    monkeypatch.setattr("httpx.Client.get", mock_get)

    versions = installer.get_available_versions()
    assert versions == ["1.2.3", "1.2.2"]


def test_get_available_versions_limit(monkeypatch):
    mock_get = MagicMock()
    mock_get.return_value.json.return_value = [
        {"tag_name": f"1.{i}", "prerelease": False, "draft": False} for i in range(5)
    ]
    monkeypatch.setattr("httpx.Client.get", mock_get)

    versions = installer.get_available_versions(limit=2)
    assert versions == ["1.0", "1.1"]


def test_get_available_versions_network_error(monkeypatch):
    def mock_get(*args, **kwargs):
        raise httpx.RequestError("Network error")

    monkeypatch.setattr("httpx.Client.get", mock_get)

    with pytest.raises(RuntimeError, match="Network error"):
        installer.get_available_versions()


def test_verify_checksum(tmp_path):
    f = tmp_path / "file.txt"
    f.write_bytes(b"hello world")

    sha256 = hashlib.sha256(b"hello world").hexdigest()

    assert installer.verify_checksum(f, sha256) is True
    assert installer.verify_checksum(f, "wrong") is False


def test_fetch_expected_checksum(monkeypatch):
    mock_get = MagicMock()
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = "abcdef123456  istioctl.exe"
    monkeypatch.setattr("httpx.Client.get", mock_get)

    assert installer.fetch_expected_checksum("1.0", "istio-1.0") == "abcdef123456"


def test_fetch_expected_checksum_not_found(monkeypatch):
    mock_get = MagicMock()
    mock_get.return_value.status_code = 404
    monkeypatch.setattr("httpx.Client.get", mock_get)

    with pytest.raises(ValueError, match="Checksum file not found"):
        installer.fetch_expected_checksum("1.0", "istio-1.0")


def test_fetch_expected_checksum_network_error(monkeypatch):
    def mock_get(*args, **kwargs):
        raise httpx.RequestError("Error")

    monkeypatch.setattr("httpx.Client.get", mock_get)

    with pytest.raises(RuntimeError, match="Failed to fetch checksum"):
        installer.fetch_expected_checksum("1.0", "istio-1.0")


def test_download_file(monkeypatch, tmp_path):
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.headers = {"Content-Length": "10"}

        def iter_bytes(self, chunk_size):
            yield b"12345"
            yield b"67890"

        def raise_for_status(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    mock_stream = MagicMock(return_value=MockResponse())
    monkeypatch.setattr("httpx.Client.stream", mock_stream)

    dest = tmp_path / "dl.txt"
    installer.download_file("http://fake", dest)
    assert dest.read_bytes() == b"1234567890"


def test_download_file_not_found(monkeypatch, tmp_path):
    class MockResponse:
        def __init__(self):
            self.status_code = 404

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    mock_stream = MagicMock(return_value=MockResponse())
    monkeypatch.setattr("httpx.Client.stream", mock_stream)

    with pytest.raises(ValueError, match="Asset not found"):
        installer.download_file("http://fake", tmp_path / "dl.txt")


def test_download_file_error(monkeypatch, tmp_path):
    def mock_stream(*args, **kwargs):
        raise httpx.RequestError("Error")

    monkeypatch.setattr("httpx.Client.stream", mock_stream)

    dest = tmp_path / "dl.txt"
    dest.write_bytes(b"existing")
    with pytest.raises(RuntimeError, match="Failed to download"):
        installer.download_file("http://fake", dest)
    assert not dest.exists()  # Should be unlinked


def test_install_already_installed(mock_home, mock_os_arch, monkeypatch):
    mock_os_arch("linux", "amd64")
    (mock_home / ".istioswitch" / "versions" / "1.0").mkdir(parents=True, exist_ok=True)
    (mock_home / ".istioswitch" / "versions" / "1.0" / "istioctl").touch()

    installer.install_version("1.0")  # Should return early without exceptions


def test_install_version_full(mock_home, mock_os_arch, monkeypatch, tmp_path):
    mock_os_arch("linux", "amd64")

    monkeypatch.setattr("istioswitch.installer.is_installed", lambda x: False)
    monkeypatch.setattr(
        "istioswitch.installer.get_asset_name", lambda x: "istio-1.0.tar.gz"
    )
    monkeypatch.setattr(
        "istioswitch.installer.download_file",
        lambda url, dest: dest.write_bytes(b"archive"),
    )
    monkeypatch.setattr(
        "istioswitch.installer.fetch_expected_checksum", lambda v, a: "fakehash"
    )
    monkeypatch.setattr(
        "istioswitch.installer.verify_checksum", lambda path, hash: True
    )

    extract_called = False

    def mock_extract(archive, dest, version):
        nonlocal extract_called
        extract_called = True

    monkeypatch.setattr("istioswitch.installer.extract_binary", mock_extract)

    installer.install_version("1.0")
    assert extract_called


def test_install_version_checksum_fail(mock_home, mock_os_arch, monkeypatch, tmp_path):
    mock_os_arch("linux", "amd64")

    monkeypatch.setattr("istioswitch.installer.is_installed", lambda x: False)
    monkeypatch.setattr(
        "istioswitch.installer.get_asset_name", lambda x: "istio-1.0.tar.gz"
    )
    monkeypatch.setattr(
        "istioswitch.installer.download_file",
        lambda url, dest: dest.write_bytes(b"archive"),
    )
    monkeypatch.setattr(
        "istioswitch.installer.fetch_expected_checksum", lambda v, a: "fakehash"
    )
    monkeypatch.setattr(
        "istioswitch.installer.verify_checksum", lambda path, hash: False
    )

    with pytest.raises(ValueError, match="Checksum verification failed"):
        installer.install_version("1.0")


def test_uninstall_version(mock_home):
    ver_dir = mock_home / ".istioswitch" / "versions" / "1.0"
    ver_dir.mkdir(parents=True, exist_ok=True)
    installer.uninstall_version("1.0")
    assert not ver_dir.exists()

    with pytest.raises(ValueError):
        installer.uninstall_version("2.0")


def test_extract_binary_tar(tmp_path, mock_os_arch):
    mock_os_arch("linux", "amd64")
    tar_path = tmp_path / "test.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tarinfo = tarfile.TarInfo("istio-1.0/bin/istioctl")
        tarinfo.size = 4
        tar.addfile(tarinfo, BytesIO(b"data"))

    dest = tmp_path / "dest"
    installer.extract_binary(tar_path, dest, "1.0")

    assert (dest / "istioctl").exists()
    assert (dest / "istioctl").read_bytes() == b"data"


def test_extract_binary_zip(tmp_path, mock_os_arch):
    mock_os_arch("windows", "amd64")
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("istio-1.0/bin/istioctl.exe", b"data")

    dest = tmp_path / "dest"
    installer.extract_binary(zip_path, dest, "1.0")

    assert (dest / "istioctl.exe").exists()
    assert (dest / "istioctl.exe").read_bytes() == b"data"


def test_extract_binary_fail(tmp_path, mock_os_arch):
    mock_os_arch("windows", "amd64")
    zip_path = tmp_path / "test.zip"
    zip_path.write_bytes(b"not a zip")
    dest = tmp_path / "dest"

    with pytest.raises(RuntimeError, match="Binary extraction failed"):
        installer.extract_binary(zip_path, dest, "1.0")
