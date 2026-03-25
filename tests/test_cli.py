import pytest
from click.testing import CliRunner
from istioswitch import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_list_command(runner, monkeypatch):
    monkeypatch.setattr(
        "istioswitch.installer.get_installed_versions", lambda: ["1.0", "1.1"]
    )
    monkeypatch.setattr("istioswitch.config.get_active_version", lambda: None)

    result = runner.invoke(cli.cli, ["list"])
    assert result.exit_code == 0
    assert "1.0" in result.output
    assert "1.1" in result.output


def test_list_command_error(runner, monkeypatch):
    def mock_get(*args, **kwargs):
        raise RuntimeError("Local read error")

    monkeypatch.setattr("istioswitch.installer.get_installed_versions", mock_get)
    result = runner.invoke(cli.cli, ["list"])
    assert "Local read error" in result.output
    # Fixes coverage for line 96-99: list exception block returns nothing
    assert result.exit_code == 0


def test_cli_fallback_command(runner, monkeypatch):
    # Fixes coverage for line 51-52: treating unknown command as a version string
    monkeypatch.setattr("istioswitch.installer.is_installed", lambda x: True)
    monkeypatch.setattr(
        "istioswitch.switcher.use_version", lambda x: (True, "/fake/bin")
    )

    result = runner.invoke(cli.cli, ["1.99.0"])
    assert result.exit_code == 0
    assert "Switched to istioctl 1.99.0" in result.output


def test_current_command_none(runner, monkeypatch):
    monkeypatch.setattr("istioswitch.config.get_active_version", lambda: None)
    result = runner.invoke(cli.cli, ["current"])
    assert result.exit_code == 0
    assert "No active version set." in result.output


def test_current_command_active(runner, monkeypatch):
    monkeypatch.setattr("istioswitch.config.get_active_version", lambda: "1.0")
    result = runner.invoke(cli.cli, ["current"])
    assert result.exit_code == 0
    assert "Active version: 1.0" in result.output


def test_version_switch_command(runner, monkeypatch):
    monkeypatch.setattr("istioswitch.installer.is_installed", lambda x: True)
    monkeypatch.setattr(
        "istioswitch.switcher.use_version", lambda x: (True, "/fake/bin")
    )

    # Calling CLI with just a version string should invoke the fallback logic
    result = runner.invoke(cli.cli, ["1.0"])
    assert result.exit_code == 0
    assert "Switched to istioctl 1.0" in result.output


def test_version_switch_not_installed(runner, monkeypatch):
    installed = False

    def mock_is_installed(v):
        return installed

    def mock_install_version(v):
        nonlocal installed
        installed = True

    monkeypatch.setattr("istioswitch.installer.is_installed", mock_is_installed)
    monkeypatch.setattr("istioswitch.installer.install_version", mock_install_version)
    monkeypatch.setattr(
        "istioswitch.switcher.use_version", lambda x: (True, "/fake/bin")
    )

    result = runner.invoke(cli.cli, ["1.0"])
    assert result.exit_code == 0
    assert "installing" in result.output.lower()
    assert "Switched to istioctl 1.0" in result.output


def test_version_switch_not_in_path_win(runner, monkeypatch):
    monkeypatch.setattr("istioswitch.installer.is_installed", lambda x: True)
    monkeypatch.setattr(
        "istioswitch.switcher.use_version", lambda x: (False, "/fake/bin")
    )
    monkeypatch.setattr("istioswitch.cli.get_os", lambda: "windows")

    result = runner.invoke(cli.cli, ["1.0"])
    assert result.exit_code == 0
    assert "setx PATH" in result.output


def test_version_switch_not_in_path_linux(runner, monkeypatch):
    monkeypatch.setattr("istioswitch.installer.is_installed", lambda x: True)
    monkeypatch.setattr(
        "istioswitch.switcher.use_version", lambda x: (False, "/fake/bin")
    )
    monkeypatch.setattr("istioswitch.cli.get_os", lambda: "linux")

    result = runner.invoke(cli.cli, ["1.0"])
    assert result.exit_code == 0
    assert "export PATH=" in result.output


def test_version_switch_error(runner, monkeypatch):
    monkeypatch.setattr("istioswitch.installer.is_installed", lambda x: True)

    def mock_use(*args):
        raise RuntimeError("Use error")

    monkeypatch.setattr("istioswitch.switcher.use_version", mock_use)

    result = runner.invoke(cli.cli, ["1.0"])
    assert "Use error" in result.output


def test_install_command_interactive(runner, monkeypatch):
    # Mocking questionary.select().ask()
    class MockQuestionary:
        def __init__(self, answer):
            self.answer = answer

        def ask(self):
            return self.answer

    monkeypatch.setattr(
        "istioswitch.installer.get_available_versions", lambda x: ["1.2.3", "1.2.2"]
    )

    # Test valid selection
    monkeypatch.setattr(
        "questionary.select", lambda msg, choices: MockQuestionary("1.2.3")
    )
    monkeypatch.setattr("istioswitch.installer.is_installed", lambda x: False)
    monkeypatch.setattr("istioswitch.installer.install_version", lambda x: None)
    monkeypatch.setattr(
        "istioswitch.switcher.use_version", lambda x: (True, "/fake/bin")
    )

    result = runner.invoke(cli.cli, ["install"])
    assert result.exit_code == 0
    assert "Switched to istioctl 1.2.3" in result.output


def test_install_command_interactive_cancelled(runner, monkeypatch):
    class MockQuestionary:
        def ask(self):
            return None

    monkeypatch.setattr(
        "istioswitch.installer.get_available_versions", lambda x: ["1.2.3"]
    )
    monkeypatch.setattr("questionary.select", lambda msg, choices: MockQuestionary())

    result = runner.invoke(cli.cli, ["install"])
    assert result.exit_code == 0
    assert "Installation cancelled" in result.output


def test_install_command_interactive_no_versions(runner, monkeypatch):
    monkeypatch.setattr("istioswitch.installer.get_available_versions", lambda x: [])
    result = runner.invoke(cli.cli, ["install"])
    assert result.exit_code == 0
    assert "No versions found" in result.output


def test_install_command_interactive_fetch_error(runner, monkeypatch):
    def mock_get(*args, **kwargs):
        raise RuntimeError("Fetch error")

    monkeypatch.setattr("istioswitch.installer.get_available_versions", mock_get)
    result = runner.invoke(cli.cli, ["install"])
    assert result.exit_code == 0
    assert "Error fetching versions" in result.output


def test_install_command(runner, monkeypatch):
    monkeypatch.setattr("istioswitch.installer.is_installed", lambda x: False)
    monkeypatch.setattr("istioswitch.installer.install_version", lambda x: None)

    result = runner.invoke(cli.cli, ["install", "1.0"])
    assert result.exit_code == 0
    assert "istioctl 1.0 installed" in result.output


def test_install_command_already(runner, monkeypatch):
    monkeypatch.setattr("istioswitch.installer.is_installed", lambda x: True)
    result = runner.invoke(cli.cli, ["install", "1.0"])
    assert result.exit_code == 0
    assert "already installed" in result.output


def test_install_command_error(runner, monkeypatch):
    monkeypatch.setattr("istioswitch.installer.is_installed", lambda x: False)

    def mock_install(*args):
        raise RuntimeError("Install error")

    monkeypatch.setattr("istioswitch.installer.install_version", mock_install)
    result = runner.invoke(cli.cli, ["install", "1.0"])
    assert "Install error" in result.output


def test_detect_command(runner, monkeypatch):
    monkeypatch.setattr("istioswitch.detector.detect_istio_version", lambda x: "1.0")
    monkeypatch.setattr(
        "istioswitch.detector.get_current_context", lambda: "my-cluster"
    )

    result = runner.invoke(cli.cli, ["detect"])
    assert result.exit_code == 0
    assert "Detected Istio version on my-cluster:" in result.output
    assert "1.0" in result.output
    # Assert it didn't try to switch
    assert "Switched to istioctl" not in result.output


def test_detect_command_error(runner, monkeypatch):
    monkeypatch.setattr(
        "istioswitch.detector.get_current_context", lambda: "my-cluster"
    )

    def mock_detect(*args):
        raise RuntimeError("Detect error")

    monkeypatch.setattr("istioswitch.detector.detect_istio_version", mock_detect)
    result = runner.invoke(cli.cli, ["detect"])
    assert "Detect error" in result.output


def test_auto_switch(runner, monkeypatch):
    monkeypatch.setattr("istioswitch.detector.detect_istio_version", lambda: "1.0")
    monkeypatch.setattr(
        "istioswitch.detector.get_current_context", lambda: "my-cluster"
    )
    monkeypatch.setattr("istioswitch.installer.is_installed", lambda x: True)
    monkeypatch.setattr(
        "istioswitch.switcher.use_version", lambda x: (True, "/fake/bin")
    )

    # Calling CLI without commands
    result = runner.invoke(cli.cli, [])
    assert result.exit_code == 0
    assert "Detected Istio version on context my-cluster: 1.0" in result.output
    assert "Switched to istioctl 1.0" in result.output


def test_uninstall_command(runner, monkeypatch):
    monkeypatch.setattr("istioswitch.installer.uninstall_version", lambda x: None)
    monkeypatch.setattr("istioswitch.config.get_active_version", lambda: "1.0")
    monkeypatch.setattr("istioswitch.config.set_active_version", lambda x: None)

    result = runner.invoke(cli.cli, ["uninstall", "1.0"])
    assert result.exit_code == 0
    assert "removed from cache" in result.output


def test_uninstall_command_error(runner, monkeypatch):
    def mock_uninstall(*args):
        raise RuntimeError("Uninstall error")

    monkeypatch.setattr("istioswitch.installer.uninstall_version", mock_uninstall)
    result = runner.invoke(cli.cli, ["uninstall", "1.0"])
    assert "Uninstall error" in result.output
