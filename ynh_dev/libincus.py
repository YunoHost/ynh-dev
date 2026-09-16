#!/usr/bin/env python3

import json
import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any


class Incus:
    def __init__(self) -> None:
        pass

    def arch(self) -> str:
        plat = platform.machine()
        if plat in ["x86_64", "amd64"]:
            return "amd64"
        if plat in ["arm64", "aarch64"]:
            return "arm64"
        if plat in ["armhf"]:
            return "armhf"
        raise RuntimeError(f"Unknown platform {plat}!")

    def _run(self, *args: str, interactive: bool = False, **kwargs: Any) -> str:
        command = ["incus", *args]
        if interactive:
            subprocess.run(command, **kwargs, stdin=subprocess.PIPE, capture_output=False, check=True)
            result = ""
        else:
            result = subprocess.check_output(command, **kwargs).decode("utf-8")
        return result

    def _run_logged_prefixed(self, *args: str, prefix: str = "", **kwargs: Any) -> None:
        command = ["incus", *args]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs)
        assert process.stdout
        with process.stdout:
            for line in iter(process.stdout.readline, b""):  # b'\n'-separated lines
                linestr = line if isinstance(line, str) else line.decode("utf-8")
                logging.debug("%s%s", prefix, linestr.rstrip("\n"))
        exitcode = process.wait()  # 0 means success
        if exitcode:
            raise RuntimeError(f"Could not run {' '.join(command)}")

    def instance_stopped(self, name: str) -> bool:
        assert self.instance_exists(name)
        res = json.loads(self._run("info", name))
        return str(res["Status"]) == "STOPPED"

    def instance_exists(self, name: str) -> bool:
        res = json.loads(self._run("list", "-f", "json"))
        instance_names = [instance["name"] for instance in res]
        return name in instance_names

    def instance_start(self, name: str) -> None:
        self._run("start", name)

    def instance_stop(self, name: str) -> None:
        self._run("stop", name)

    def instance_delete(self, name: str) -> None:
        self._run("delete", name)

    def launch(self, image_name: str, instance_name: str, *args: str) -> None:
        self._run("launch", image_name, instance_name, *args)

    def push_file(self, instance_name: str, file: Path, target: str) -> None:
        self._run("file", "push", str(file), f"{instance_name}{target}")
        os.sync()

    def execute(self, instance_name: str, *args: str, exec_: bool = False, cwd: str | None = None) -> None:
        cwd_args = ["--cwd", cwd] if cwd else []
        incus_args: list[str] = ["exec", instance_name, *cwd_args, "--", *args]
        if exec_:
            incus = shutil.which("incus")
            assert incus
            os.execv(incus, ["incus", *incus_args])
        else:
            self._run_logged_prefixed(*incus_args, prefix=" In container |\t")

    def publish(self, instance_name: str, image_alias: str, properties: dict[str, str]) -> None:
        properties_list = [f"{key}={value}" for key, value in properties.items()]
        self._run("publish", instance_name, "--alias", image_alias, *properties_list)

    def image_export(self, image_alias: str, image_target: str, target_dir: Path) -> None:
        self._run("image", "export", image_alias, image_target, cwd=target_dir)

    def image_exists(self, alias: str) -> bool:
        res = json.loads(self._run("image", "list", "-f", "json"))
        image_aliases = [alias["name"] for image in res for alias in image["aliases"]]
        return alias in image_aliases

    def image_alias_exists(self, alias: str) -> bool:
        res = json.loads(self._run("image", "alias", "list", "-f", "json"))
        aliases = [alias["name"] for alias in res]
        return alias in aliases

    def image_delete(self, alias: str) -> None:
        self._run("image", "delete", alias)

    def image_download(self, alias: str) -> None:
        if self.image_alias_exists(alias):
            self.image_delete(alias)
        self._run("image", "copy", alias, "local:", "--copy-aliases", "--auto-update", interactive=True)

    def remotes(self) -> dict[str, dict[str, str]]:
        return json.loads(self._run("remote", "list", "-f", "json"))

    def remote_add(self, name: str, url: str, public: bool, protocol: str) -> None:
        self._run(
            "remote",
            "add",
            name,
            url,
            "--protocol",
            protocol,
            *(["--public"] if public else []),
        )
