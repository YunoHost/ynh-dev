#!/usr/bin/env python3

import argparse
import atexit
import json
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Any

import psutil
import pyinotify
import yaml

from .catalog_manager import Catalog


def ips() -> list[str]:
    return subprocess.check_output(["hostname", "--all-ip-addresses"]).decode("utf-8").split()


def install_yarn() -> None:
    print("Installing dependencies ... (this may take a while)")
    if not shutil.which("yarn"):
        subprocess.check_call(["apt", "install", "yarnpkg"])


def install_tox() -> Path:
    if not shutil.which("tox"):
        subprocess.check_call(["apt", "install", "pipx"])
        subprocess.check_call(["pipx", "install", "tox"])
    return Path("/root/.local/bin/tox")


def install_pytest() -> None:
    if not shutil.which("pytest"):
        subprocess.check_call(["apt", "install", "python3-pip"])


def clone_or_pull(url: str, path: Path) -> None:
    if path.exists():
        subprocess.check_call(["git", "pull"], cwd=path)
    else:
        subprocess.check_call(["git", "clone", url, str(path)])


def install_package_linter() -> None:
    package_linter_dir = Path("/ynh-dev/package_linter")
    clone_or_pull("https://github.com/YunoHost/package_linter", package_linter_dir)
    subprocess.check_call(["python", "-m", "venv", "venv"], cwd=package_linter_dir)
    subprocess.check_call(["venv/bin/pip", "install", "-r", "requirements.txt"], cwd=package_linter_dir)


def symlink(target: Path, link: Path) -> None:
    if link.is_symlink():
        link.unlink()
    if link.exists():
        if link.is_dir():
            shutil.rmtree(link)
        else:
            link.unlink()
    link.symlink_to(target)


class SSOWat:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.name = "ssowat"

    def use(self, root: Path) -> None:
        symlink(self.path, root / "usr/share/ssowat")
        debugger_dir = self.path.parent / "ZeroBraneStudio"
        ssowat_conf_file = root / "etc/nginx/conf.d/ssowat.conf"
        if "lua_package_path" not in (content := ssowat_conf_file.read_text()):
            ssowat_conf_file.write_text(f"""\
                lua_package_path '{debugger_dir}/lualibs/?/?.lua;{debugger_dir}/lualibs/?.lua;;';
                lua_package_cpath '{debugger_dir}/bin/linux/x64/clibs/?.so;;';
                {content}
            """)

        if not debugger_dir.exists():
            print(
                textwrap.dedent("""
                If you want to debug ssowat, you can clone https://github.com/pkulchenko/ZeroBraneStudio
                into the ynh-dev directory of your host, open it, and open a file at the root of the ssowat
                project in ynh-dev directory, click on "Project -> Project Directory -> Set From Current File".
                You can start the remote debugger with "Project -> Start Debugger Server".
                Add the line "require("mobdebug").start('THE_IP_OF_YOUR_HOST_IN_THE_CONTAINER_NETWORK')" at
                the top of the file access.lua and reload nginx in your container with "systemctl reload nginx".
                After that you should be able to debug ssowat \\o/. The debugger should pause the first time it
                reaches the line "require("mobdebug").start('...')", but you can add breakpoints where needed.
                More info here: http://notebook.kulchenko.com/zerobrane/debugging-openresty-nginx-lua-scripts-with-zerobrane-studio
                and here: https://github.com/pkulchenko/MobDebug.
            """)
            )

    def dev(self, root: Path) -> None:
        self.use(root)

    def lint(self) -> None:
        print(f"Linker not implemented for {self.name}")


class Moulinette:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.name = "moulinette"

    def use(self, root: Path) -> None:
        symlink(self.path / "locales", root / "usr/share/moulinette/locale")
        symlink(self.path / "moulinette", root / "usr/lib/python3/dist-packages/moulinette")

    def dev(self, root: Path) -> None:
        self.use(root)

    def lint(self) -> None:
        tox = install_tox()
        subprocess.run([str(tox), "run"], cwd=self.path, check=False)
        subprocess.run([str(tox), "run", "-e", "py311-mypy"], cwd=self.path, check=False)


class YunoHost:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.name = "yunohost"

    def use(self, root: Path) -> None:
        for file in (self.path / "bin").iterdir():
            symlink(file, root / file.name)
        for file in (self.path / "share").iterdir():
            symlink(file, root / "usr/share/yunohost" / file.name)
        for file in (self.path / "helpers").iterdir():
            symlink(file, root / "usr/share/yunohost" / file.name)

        symlink(self.path / "hooks", root / "usr/share/yunohost/hooks")
        symlink(self.path / "conf", root / "usr/share/yunohost/conf")
        symlink(self.path / "locales", root / "usr/share/yunohost/locales")
        symlink(self.path / "src", root / "usr/lib/python3/dist-packages/yunohost")

        subprocess.check_call(
            [self.path / "doc/generate_bash_completion.py", "-o", root / "etc/bash_completion.d/yunohost"]
        )
        subprocess.check_call(
            [self.path / "doc/generate_zsh_completion.py", "-o", root / "usr/share/zsh/vendor-completions/_yunohost"]
        )

    def dev(self, root: Path) -> None:
        self.use(root)
        self.run_api()

    def run_api(self) -> None:
        services = ["yunohost-api", "yunohost-portal-api"]

        def kill_api() -> None:
            for service in services:
                if subprocess.run(["systemctl", "--quiet", "is-active", service], check=False).returncode == 0:
                    subprocess.run(["systemctl", "stop", service], check=False)
                for proc in psutil.process_iter():
                    if any(service in arg for arg in proc.cmdline()):
                        proc.kill()
                        proc.wait()

        def start_api_debug() -> None:
            for service in services:
                subprocess.Popen([service, "--debug"], close_fds=True)

        def restart_api() -> None:
            print()
            print("==========================")
            print("Restarting services")
            print("==========================")
            print()
            kill_api()
            start_api_debug()

        def wait_inotify() -> pyinotify.Notifier:
            wm = pyinotify.WatchManager()
            notifier = pyinotify.Notifier(wm)
            excl = pyinotify.ExcludeFilter(["^test_.*", ".*\\.pyc$"])
            mask = pyinotify.IN_MODIFY  # type: ignore
            for path in ["share", "locales", "src"]:
                wm.add_watch(f"/ynh-dev/yunohost/{path}", mask, exclude_filter=excl)
            for path in ["moulinette"]:
                wm.add_watch(f"/ynh-dev/moulinette/{path}", mask, exclude_filter=excl)
            return notifier

        print(
            "Monitoring for changes in python files, restarting yunohost-api and yunohost-portal-api when changes occur!"
        )
        restart_api()
        atexit.register(kill_api)

        while wait_inotify().check_events():
            restart_api()

    def lint(self) -> None:
        tox = install_tox()
        subprocess.run([str(tox), "run"], cwd=self.path, check=False)
        subprocess.run([str(tox), "run", "-e", "py311-mypy"], cwd=self.path, check=False)

    def test(self) -> None:
        test_apps_dir = self.path / "tests" / "apps"
        clone_or_pull("https://github.com/YunoHost/test_apps", test_apps_dir)


class YunoHostAdmin:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.name = "yunohost-admin"

    def build(self, root: Path) -> None:
        dev_path = self.path / "app"
        target = root / "usr/share/yunohost/admin"
        target_bkp = target.with_name(target.name + "-bkp")
        if not target_bkp.exists():
            target.rename(target_bkp)

        subprocess.check_call(["yarnpkg", "build"], cwd=dev_path)
        symlink(dev_path / "dist", target)
        print(f"App built and available at https://{ips()[0]}/yunohost/admin")

    def dev(self, root: Path) -> None:
        dev_path = self.path / "app"
        cache_path = root / "var/cache/ynh-dev/yunohost-admin"
        cache_path.mkdir(parents=True, exist_ok=True)
        symlink(dev_path / ".env", cache_path / ".env")
        symlink(cache_path / "node_modules", dev_path / "node_modules")
        symlink(dev_path / "package.json", cache_path / "package.json")
        symlink(dev_path / "yarn.lock", cache_path / "yarn.lock")

        install_yarn()
        subprocess.check_call(["yarnpkg", "install", "--frozen-lockfile"], cwd=cache_path)

        # Inject container ip in .env file
        # Used by vite to expose itself on network and proxy api requests.
        (dev_path / ".env").open("w").write(f"VITE_IP={ips()[0]}\n")

        installed = Path("/etc/yunohost/installed").exists()
        if installed:
            subprocess.check_call(["yunohost", "firewall", "allow", "TCP", "8080"])
        else:
            firewall = Path("/etc/yunohost/firewall.yml")
            assert firewall.exists(), f"Firewall yaml file {firewall} does not exists ?"
            settings = yaml.safe_load(firewall.open("r"))
            if not settings.get(8080, {}).get("open", False):
                settings[8080] = {"open": True, "comment": "yunohost-admin dev vite"}
            yaml.safe_dump(settings, firewall.open("w"), default_flow_style=False)

        print("Now running dev server")
        subprocess.run(["yarnpkg", "dev", "--host"], cwd=dev_path, check=False)

    def lint(self) -> None:
        print(f"Linker not implemented for {self.name}")

    def test(self) -> None:
        pass
        # # Pytest and tests dependencies
        # if ! type "pytest" > /dev/null 2>&1; then
        #     info "> Installing pytest ..."
        #     apt-get update
        #     apt-get install python3-pip -y
        #     pip3 install pytest pytest-sugar pytest-cov --break-system-packages
        # fi
        # for DEP in pytest-mock requests-mock mock; do
        #     if [ -z "$(pip3 show $DEP)" ]; then
        #         info "Installing $DEP with pip3"
        #         pip3 install $DEP --break-system-packages
        #     fi
        # done

        # # ./src/tests is being moved to ./tests, this small patch supports both paths
        # if [[ -e "/ynh-dev/yunohost/tests/conftest.py" ]]; then
        #     tests_parentdir=/ynh-dev/yunohost
        # else
        #     tests_parentdir=/ynh-dev/yunohost/src
        # fi

        # # Apps for test
        # cd "$tests_parentdir/tests"
        # [ -d "apps" ] || git clone https://github.com/YunoHost/test_apps ./apps
        # cd apps
        # git pull > /dev/null 2>&1

        # # Run tests
        # info "Running tests for YunoHost"
        # [ -e "/etc/yunohost/installed" ] || critical "You should run postinstallation before running tests :s."

        # testpath=tests
        # if [[ -n "$TEST_MODULE" ]]; then
        #     testpath="${testpath}/test_${TEST_MODULE}.py"
        #     if [[ -n "$TEST_FUNCTION" ]]; then
        #         testpath="${testpath}::test_${TEST_FUNCTION}"
        #     fi
        # fi
        # cd "$tests_parentdir"
        # pytest "$testpath"


class YunoHostPortal:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.name = "yunohost-portal"

    def use(self, root: Path) -> None:
        dev_path = self.path
        target = root / "usr/share/yunohost/portal"
        target_bkp = target.with_name(target.name + "-bkp")
        if not target_bkp.exists():
            target.rename(target_bkp)

        subprocess.check_call(["yarnpkg", "generate"], cwd=dev_path)
        symlink(dev_path / ".output" / "public", target)
        print(f"App built and available at https://{ips()[0]}/yunohost/sso")

    def dev(self, root: Path) -> None:
        dev_path = self.path
        env_file = dev_path / ".env"
        cache_path = root / "var/cache/ynh-dev/yunohost-portal"
        cache_path.mkdir(parents=True, exist_ok=True)
        symlink(env_file, cache_path / ".env")
        symlink(cache_path / "node_modules", dev_path / "node_modules")
        symlink(dev_path / "package.json", cache_path / "package.json")
        symlink(dev_path / "yarn.lock", cache_path / "yarn.lock")

        if not env_file.is_file():
            ip = ips()[0]
            domain = json.loads(subprocess.check_output(["yunohost", "domain", "main-domain", "--output-as=json"]))[
                "current_main_domain"
            ]
            print(
                textwrap.dedent(f"""\
                There's no 'yunohost-portal/.env' file.

                Based on your current main domain (but you can use any domain added on your YunoHost instance)
                the file should look like:

                NUXT_PUBLIC_API_IP=\"$MAIN_DOMAIN\"

                If not already, add your instance's IP into '/etc/yunohost/.portal-api-allowed-cors-origins'
                to avoid CORS issues and make sure to add a redirection in your host's '/etc/hosts' which,
                based on your instance ip and main domain, would be:

                {ip} {domain}
            """)
            )

        install_yarn()
        subprocess.check_call(["yarnpkg", "install", "--frozen-lockfile"], cwd=cache_path)

        subprocess.check_call(["yunohost", "firewall", "allow", "TCP", "3000"])
        subprocess.check_call(["yunohost", "firewall", "allow", "TCP", "24678"])

        print("Now running dev server")
        subprocess.run(["yarnpkg", "dev", "--host"], cwd=dev_path, check=False)

    def lint(self) -> None:
        print(f"Linker not implemented for {self.name}")


def test_app(app: Path) -> None:
    install_package_linter()
    subprocess.check_call(
        [
            "/ynh-dev/package_linter/venv/bin/python3",
            "/ynh-dev/package_linter/package_linter.py",
            str(app),
        ]
    )


PROJECTS: dict[str, Any] = {
    "moulinette": Moulinette,
    "ssowat": SSOWat,
    "yunohost": YunoHost,
    "yunohost-admin": YunoHostAdmin,
    "yunohost-portal": YunoHostPortal,
}


def main_container() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(title="container actions", required=True, dest="action")
    ip = sub.add_parser("ip", help="Give the ip of the guest container")
    action = sub.add_parser("use-git", help="Use Git repositories from dev environment path")
    action.add_argument("components", type=str, nargs="+", choices=PROJECTS)
    action = sub.add_parser("use-git-dev", help="Use Git repositories from dev environment path and start dev server")
    action.add_argument("components", type=str, nargs="+", choices=PROJECTS)
    action = sub.add_parser("lint", help="Lint source code from core or app packages.")
    action.add_argument("components", type=str, nargs="+", choices=PROJECTS)
    action = sub.add_parser("test", help="Deploy, update and run tests for some packages")
    action.add_argument("components", type=str, nargs="+", choices=PROJECTS)

    sub.add_parser(
        "api",
        help="""
        Start yunohost-api and yunohost-portal-api in debug mode in the current terminal,
        and auto-restart them when code changes
    """,
    )
    sub.add_parser("rebuild-api-doc", help="Rebuild the API swagger doc")

    catalog = sub.add_parser("catalog")
    catalog_sub = catalog.add_subparsers(dest="catalog_action", required=True)
    catalog_sub.add_parser("build", help="Rebuild the custom catalog")
    catalog_sub.add_parser("add", help="Add the custom catalog in Yunohost catalog list")
    catalog_sub.add_parser("override", help="Override default catalog with the custom catalog")
    catalog_sub.add_parser("reset", help="Reset the catalog list to Yunohost's default")

    args = parser.parse_args()

    match args.action:
        case "ip":
            print("\n".join(ips()))
        case "use-git":
            for arg in args.components:
                project = PROJECTS[arg](f"/ynh-dev/{arg}")
                project.use(Path("/"))
        case "use-git-dev":
            for arg in args.components:
                project = PROJECTS[arg](f"/ynh-dev/{arg}")
                project.dev(Path("/"))
        case "lint":
            for arg in args.components:
                project = PROJECTS[arg](f"/ynh-dev/{arg}")
                project.lint()
        case "test":
            for arg in args.components:
                if arg in PROJECTS:
                    project = PROJECTS[arg](f"/ynh-dev/{arg}")
                    project.test()
                else:
                    test_app(Path(f"/ynh-dev/apps/{args.component}"))
        case "catalog":
            getattr(Catalog(), args.catalog_action)()


if __name__ == "__main__":
    main_container()
