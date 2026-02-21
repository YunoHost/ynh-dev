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

my_env = os.environ.copy().update({"GIT_TERMINAL_PROMPT": "0"})


class Catalog:
    def __init__(self) -> None:
        self.CATALOG_LIST_PATH = Path("/etc/yunohost/apps_catalog.yml")
        self.DEFAULT_APPS_FOLDER = Path("/ynh-dev/custom-catalog/")
        self.DEFAULT_APP_BRANCH = "master"
        self.DEFAULT_CATALOG = [{"id": "default", "url": "https://app.yunohost.org/default/"}]
        # assert self.CATALOG_LIST_PATH.exists(), f"Catalog list yaml file '{self.CATALOG_LIST_PATH} does not exists"

    def build(self, folder: Path | None = None) -> None:
        folder = folder or self.DEFAULT_APPS_FOLDER
        assert folder.exists(), f"'{folder}' doesn't exist."
        apps_list_path = folder / "apps.json"
        assert apps_list_path.exists(), "no 'apps.json' app list found."
        apps_list = json.load(apps_list_path.open())

        apps = {}
        fail = False

        for app_, infos in apps_list.items():
            app = app_.lower()
            try:
                app_dict = self.build_app_dict(app, infos, folder)
            except (OSError, json.JSONDecodeError, toml.TomlDecodeError) as e:
                print(f"[\033[1m\033[31mFAIL\033[00m] Processing {app} failed: {e!s}")
                fail = True
                continue

            apps[app_dict["id"]] = app_dict

        # We also remove the app install question and resources parts which aint
        # needed anymore by webadmin etc (or at least we think ;P)
        for app in apps.values():
            if "manifest" in app and "install" in app["manifest"]:
                del app["manifest"]["install"]
            if "manifest" in app and "resources" in app["manifest"]:
                del app["manifest"]["resources"]

        data = {
            "apps": apps,
            "from_api_version": 3,
        }

        output_file = folder / "catalog.json"
        json.dump(data, output_file.open("w"), sort_keys=True, indent=2)

        if fail:
            sys.exit(1)

    def build_app_dict(self, app: str, infos: dict[str, Any], folder: Path) -> dict[str, Any]:
        app_folder = folder / f"{app}_ynh"

        # Build the dict with all the infos
        manifest_toml = app_folder / "manifest.toml"
        manifest_json = app_folder / "manifest.json"
        if manifest_toml.exists():
            manifest = toml.load(manifest_toml.open(), _dict=OrderedDict)
        else:
            manifest = json.load(manifest_json.open(), _dict=OrderedDict)

        return {
            "id": app,
            "git": {
                "branch": infos.get("branch", self.DEFAULT_APP_BRANCH),
                "revision": infos.get("revision", "HEAD"),
                "url": f"file://{app_folder}",
            },
            "lastUpdate": time.time(),
            "manifest": manifest,
            "state": infos.get("state", "notworking"),
            "level": infos.get("level", -1),
            "maintained": infos.get("maintained", True),
            # "high_quality": infos.get("high_quality", False),
            # "featured": infos.get("featured", False),
            "category": infos.get("category"),
            "subtags": infos.get("subtags", []),
            "potential_alternative_to": infos.get("potential_alternative_to", []),
            "antifeatures": list(set(list(manifest.get("antifeatures", {}).keys()) + infos.get("antifeatures", []))),
        }

    def reset(self) -> None:
        yaml.safe_dump(self.DEFAULT_CATALOG, self.CATALOG_LIST_PATH.open("w"), default_flow_style=False)

    def add(self) -> None:
        if not self.CATALOG_LIST_PATH.exists():
            self.reset()
        catalog_list = yaml.safe_load(self.CATALOG_LIST_PATH.open())
        ids = [catalog["id"] for catalog in catalog_list]
        if "custom" not in ids:
            catalog_list.append({"id": "custom", "url": None})
            yaml.safe_dump(catalog_list, self.CATALOG_LIST_PATH.open("w"), default_flow_style=False)

    def override(self) -> None:
        catalog_list = [{"id": "custom", "url": None}]
        yaml.safe_dump(catalog_list, self.CATALOG_LIST_PATH.open("w"), default_flow_style=False)
