import json
from pathlib import Path
from typing import Optional
from istioswitch.platform_utils import get_base_dir

def get_config_path() -> Path:
    return get_base_dir() / "config.json"

def read_config() -> dict:
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}

def write_config(config: dict) -> None:
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def get_active_version() -> Optional[str]:
    return read_config().get("active_version")

def set_active_version(version: Optional[str]) -> None:
    config = read_config()
    if version is None:
        if "active_version" in config:
            del config["active_version"]
    else:
        config["active_version"] = version
    write_config(config)
