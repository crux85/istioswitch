import pytest
import subprocess
from istioswitch import detector


def test_get_current_context_success(monkeypatch):
    def mock_run(*args, **kwargs):
        class MockResult:
            returncode = 0
            stdout = "my-cluster-context\n"

        return MockResult()

    monkeypatch.setattr(subprocess, "run", mock_run)
    assert detector.get_current_context() == "my-cluster-context"


def test_get_current_context_fail(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)
    assert detector.get_current_context() == "unknown-context"


def test_get_current_context_not_found(monkeypatch):
    def mock_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, "run", mock_run)
    assert detector.get_current_context() == "unknown-context"


def test_detect_istio_version_success(monkeypatch):
    def mock_run(*args, **kwargs):
        class MockResult:
            returncode = 0
            stdout = "docker.io/istio/pilot:1.26.4"

        return MockResult()

    monkeypatch.setattr(subprocess, "run", mock_run)

    assert detector.detect_istio_version() == "1.26.4"


def test_detect_istio_version_with_context(monkeypatch):
    def mock_run(cmd, *args, **kwargs):
        assert "--context" in cmd
        assert "myctx" in cmd

        class MockResult:
            returncode = 0
            stdout = "docker.io/istio/pilot:1.25.3-distroless"

        return MockResult()

    monkeypatch.setattr(subprocess, "run", mock_run)

    assert detector.detect_istio_version("myctx") == "1.25.3"


def test_detect_istio_version_fail(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)

    with pytest.raises(RuntimeError, match="Failed to detect istiod"):
        detector.detect_istio_version()


def test_detect_istio_version_not_found(monkeypatch):
    def mock_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, "run", mock_run)

    with pytest.raises(RuntimeError, match="not found"):
        detector.detect_istio_version()


def test_detect_istio_version_empty_output(monkeypatch):
    def mock_run(*args, **kwargs):
        class MockResult:
            returncode = 0
            stdout = "   \n"

        return MockResult()

    monkeypatch.setattr(subprocess, "run", mock_run)

    with pytest.raises(RuntimeError, match="No image found"):
        detector.detect_istio_version()


def test_detect_istio_version_bad_output(monkeypatch):
    def mock_run(*args, **kwargs):
        class MockResult:
            returncode = 0
            stdout = "invalid-image-format"

        return MockResult()

    monkeypatch.setattr(subprocess, "run", mock_run)

    with pytest.raises(RuntimeError, match="Could not parse version"):
        detector.detect_istio_version()
