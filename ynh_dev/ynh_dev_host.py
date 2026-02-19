#!/usr/bin/env python3

import argparse
import grp
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .libincus import Incus

DISTS = ["bullseye", "bookworm", "trixie"]
VARIANTS = ["appci", "before-install", "build-and-lint", "core-tests", "demo", "dev"]
BRANCHES = ["stable", "testing", "unstable"]

YNH_DEV_DIR = Path(__file__).parent.parent


def main_host() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(title="host actions", required=True, dest="action")
    sub.add_parser("init", help="Download source repositories")
    sub.add_parser("start", help="(Create and) starts a box")
    sub.add_parser("attach", help="Attach an already started box")
    sub.add_parser("destroy", help="Destroy the ynh-dev box")

    parser.add_argument("-d", "--dist", type=str, choices=DISTS, default="bookworm")
    parser.add_argument("-v", "--variant", type=str, choices=VARIANTS, default="core-tests")
    parser.add_argument("-b", "--ynh_branch", type=str, choices=BRANCHES, default="stable")
    parser.add_argument("-n", "--name", type=str)

    args = parser.parse_args()
    logging.getLogger().setLevel(logging.INFO)

    check_incus_setup()
    ensure_incus_remote()

    image = f"yunohost/{args.dist}-{args.ynh_branch}/{args.variant}"
    container = f"ynh-dev-{args.dist}-{args.ynh_branch}-{args.variant}{f'-{args.name}' if args.name else ''}"

    incus = Incus()

    match args.action:
        case "init":
            init()
        case "start":
            if not incus.image_exists(image):
                logging.info(f"Downloading {image}...")
                incus.image_download("yunohost:" + image)
            if incus.instance_exists(container):
                logging.warning(f"Container {container} is already started!")

            else:
                logging.info(f"Launching {image} -> {container}...")
                incus.launch(image, container, "-c", "security.nesting=true", "-c", "security.privileged=true")
                incus._run(
                    "config",
                    "device",
                    "add",
                    container,
                    "ynh-dev-shared-folder",
                    "disk",
                    "path=/ynh-dev",
                    f"source={YNH_DEV_DIR}",
                )

            incus.execute(container, "dhclient")
            attach(incus, container)

        case "attach":
            attach(incus, container)

        case "destroy":
            incus.instance_stop(container)
            incus.instance_delete(container)



def clone_or_pull(url: str, path: Path) -> None:
    if path.exists():
        subprocess.check_call(["git", "pull"], cwd=path)
    else:
        subprocess.check_call(["git", "clone", url, str(path)])


def init() -> None:
    clone_or_pull("https://github.com/YunoHost/moulinette", YNH_DEV_DIR / "moulinette")
    clone_or_pull("https://github.com/YunoHost/yunohost", YNH_DEV_DIR / "yunohost")
    clone_or_pull("https://github.com/YunoHost/yunohost-admin", YNH_DEV_DIR / "yunohost-admin")
    clone_or_pull("https://github.com/YunoHost/SSOwat ssowat", YNH_DEV_DIR / "SSOwat ssowat")
    clone_or_pull("https://github.com/YunoHost/yunohost-portal", YNH_DEV_DIR / "yunohost-portal")
    (YNH_DEV_DIR / "apps").mkdir(exist_ok=True)


def attach(incus: Incus, container: str) -> None:
    logging.info(f"Attaching to {container}.")
    incus.execute(container, "/bin/bash", cwd="/ynh-dev", exec_=True)


def check_incus_setup() -> None:
    if shutil.which("incus") is None:
        logging.error(
            "You need to have Incus installed for ynh-dev to be usable from the host machine. "
            "Refer to the README to know how to install it."
        )
        sys.exit(1)
    incus_group = grp.getgrnam("incus-admin").gr_gid
    if incus_group not in os.getgroups():
        logging.error("You need to be in the incus-admin group!")
        sys.exit(1)

    if "incusbr0" not in subprocess.check_output(["ip", "addr"]).decode("utf-8"):
        logging.warning("There is no 'incusbr0' interface... Did you ran 'incus admin init' ?")


def ensure_incus_remote() -> None:
    remote_url = "https://repo.yunohost.org/incus/"
    if ynh_remote := Incus().remotes().get("yunohost"):
        if (url := ynh_remote["Addr"]) != remote_url:
            logging.error(f"Remote yunohost has url {url} instead of {remote_url}!")
            sys.exit(1)
        return
    Incus().remote_add("yunohost", remote_url, True, "simplestreams")


if __name__ == "__main__":
    main_host()
