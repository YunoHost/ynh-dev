#!/usr/bin/python3

import json
import os
import sys
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

import toml
import yaml

CATALOG_LIST_PATH = Path("/etc/yunohost/apps_catalog.yml").resolve()
assert CATALOG_LIST_PATH.exists(), f"Catalog list yaml file '{CATALOG_LIST_PATH} does not exists"

now = time.time()
my_env = os.environ.copy()
my_env["GIT_TERMINAL_PROMPT"] = "0"

DEFAULT_APPS_FOLDER = "/ynh-dev/custom-catalog/"
DEFAULT_APP_BRANCH = "master"


def build(folder: Path | str = DEFAULT_APPS_FOLDER) -> None:
    folder = Path(folder)
    assert folder.exists(), f"'{folder}' doesn't exists."

    app_list_path = folder / "apps.json"
    assert app_list_path.exists(), "no 'apps.json' app list found."

    with app_list_path.open() as f:
        app_list = json.load(f)

    apps = {}
    fail = False

    for app, infos in app_list.items():
        app = app.lower()
        try:
            app_dict = build_app_dict(app, infos, folder)
        except Exception as e:
            print(f"[\033[1m\033[31mFAIL\033[00m] Processing {app} failed: {str(e)}")
            fail = True
            continue

        apps[app_dict["id"]] = app_dict

    # We also remove the app install question and resources parts which aint needed
    # anymore by webadmin etc (or at least we think ;P)
    for app in apps.values():
        if "manifest" in app and "install" in app["manifest"]:
            del app["manifest"]["install"]
        if "manifest" in app and "resources" in app["manifest"]:
            del app["manifest"]["resources"]

    output_file = folder / "catalog.json"
    data = {
        "apps": apps,
        "from_api_version": 3,
    }

    with output_file.open("w") as f:
        f.write(json.dumps(data, sort_keys=True, indent=2))

    if fail:
        sys.exit(1)


def build_app_dict(app: str, infos: dict[str, Any], folder: Path) -> dict[str, Any]:
    app_folder = folder / f"{app}_ynh"

    # Build the dict with all the infos
    manifest_toml = app_folder / "manifest.toml"
    manifest_json = app_folder / "manifest.json"
    if manifest_toml.exists():
        with manifest_toml.open() as f:
            manifest = toml.load(f, _dict=OrderedDict)
    else:
        with manifest_json.open() as f:
            manifest = json.load(f, _dict=OrderedDict)

    return {
        "id": app,
        "git": {
            "branch": infos.get("branch", DEFAULT_APP_BRANCH),
            "revision": infos.get("revision", "HEAD"),
            "url": f"file://{app_folder}",
        },
        "lastUpdate": now,
        "manifest": manifest,
        "state": infos.get("state", "notworking"),
        "level": infos.get("level", -1),
        "maintained": infos.get("maintained", True),
        # "high_quality": infos.get("high_quality", False),
        # "featured": infos.get("featured", False),
        "category": infos.get("category", None),
        "subtags": infos.get("subtags", []),
        "potential_alternative_to": infos.get("potential_alternative_to", []),
        "antifeatures": list(set(list(manifest.get("antifeatures", {}).keys()) + infos.get("antifeatures", []))),
    }


def reset() -> None:
    with CATALOG_LIST_PATH.open("w") as f:
        catalog_list = [{"id": "default", "url": "https://app.yunohost.org/default/"}]
        yaml.safe_dump(catalog_list, f, default_flow_style=False)


def add() -> None:
    with CATALOG_LIST_PATH.open("r") as f:
        catalog_list = yaml.load(f, Loader=yaml.FullLoader)
        ids = [catalog["id"] for catalog in catalog_list]
        if "custom" not in ids:
            catalog_list.append({"id": "custom", "url": None})
            with CATALOG_LIST_PATH.open("w") as f:
                yaml.safe_dump(catalog_list, f, default_flow_style=False)


def override() -> None:
    with CATALOG_LIST_PATH.open("w") as f:
        catalog_list = [{"id": "custom", "url": None}]
        yaml.safe_dump(catalog_list, f, default_flow_style=False)
