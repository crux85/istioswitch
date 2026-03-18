from istioswitch import config


def test_read_write_config(mock_home):
    assert config.read_config() == {}

    config.set_active_version("1.2.3")
    assert config.get_active_version() == "1.2.3"
    assert config.read_config() == {"active_version": "1.2.3"}

    config.set_active_version(None)
    assert config.get_active_version() is None


def test_corrupt_config(mock_home):
    cfg_file = mock_home / ".istioswitch" / "config.json"
    cfg_file.parent.mkdir(parents=True, exist_ok=True)
    cfg_file.write_text("{bad_json:")

    assert config.read_config() == {}
