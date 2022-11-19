#!/usr/bin/python3

import os
import json
import toml
import shutil
import time
import subprocess
from collections import OrderedDict


now = time.time()
my_env = os.environ.copy()
my_env["GIT_TERMINAL_PROMPT"] = "0"

DEFAULT_APPS_FOLDER = "/ynh-dev/custom-apps/"
DEFAULT_APP_BRANCH = "master"


def build(folder=DEFAULT_APPS_FOLDER):
    assert os.path.exists(folder), f"'{folder}' doesn't exists."

    app_list_path = os.path.join(folder, "apps.json")
    assert os.path.exists(app_list_path), "no 'apps.json' app list found."

    with open(app_list_path) as f:
        app_list = json.load(f)

    apps = {}

    for app, infos in app_list.items():
        app = app.lower()
        try:
            app_dict = build_app_dict(app, infos, folder)
        except Exception as e:
            print(f"Processing {app} failed: {str(e)}")
            continue

        apps[app_dict["id"]] = app_dict

    # We also remove the app install question and resources parts which aint needed anymore by webadmin etc (or at least we think ;P)
    for app in apps.values():
        if "manifest" in app and "install" in app["manifest"]:
            del app["manifest"]["install"]
        if "manifest" in app and "resources" in app["manifest"]:
            del app["manifest"]["resources"]

    output_file = os.path.join(folder, "catalog.json")
    data = {
        "apps": apps,
        "from_api_version": 3,
    }

    with open(output_file, "w") as f:
        f.write(json.dumps(data, sort_keys=True, indent=2))


def build_app_dict(app, infos, folder):
    app_folder = os.path.join(folder, app + "_ynh")

    # Build the dict with all the infos
    manifest_toml = os.path.join(app_folder, "manifest.toml")
    manifest_json = os.path.join(app_folder, "manifest.json")
    if os.path.exists(manifest_toml):
        with open(manifest_toml) as f:
            manifest = toml.load(f, _dict=OrderedDict)
    else:
        with open(manifest_json) as f:
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
        "antifeatures": list(
            set(
                list(manifest.get("antifeatures", {}).keys())
                + infos.get("antifeatures", [])
            )
        ),
    }


if __name__ == "__main__":
    build()
