# ynh-dev - Yunohost dev environment manager

Please report issues on the following repository: <https://github.com/yunohost/issues>

## Table Of Contents

- [ynh-dev - Yunohost dev environment manager](#ynh-dev---yunohost-dev-environment-manager)
  - [Table Of Contents](#table-of-contents)
  - [Introduction](#introduction)
    - [Local Development Path](#local-development-path)
    - [Remote Development Path](#remote-development-path)
  - [Local Development Environment](#local-development-environment)
    - [1. Setup `ynh-dev` and the development environment](#1-setup-ynh-dev-and-the-development-environment)
    - [2. Manage YunoHost's dev LXCs](#2-manage-yunohosts-dev-lxcs)
    - [3. Development and container testing](#3-development-and-container-testing)
    - [4. Testing the web interface](#4-testing-the-web-interface)
    - [5. Running the automated tests](#5-running-the-automated-tests)
    - [Advanced: using snapshots](#advanced-using-snapshots)
    - [Troubleshooting](#troubleshooting)
  - [Remote Development Environment](#remote-development-environment)
    - [1. Setup your VPS and install YunoHost](#1-setup-your-vps-and-install-yunohost)
    - [2. Setup `ynh-dev` and the development environment](#2-setup-ynh-dev-and-the-development-environment)
    - [3. Develop and test](#3-develop-and-test)
  - [Further Resources](#further-resources)

---

## Introduction

`ynh-dev` is a CLI tool to manage your local development environment for YunoHost.

This allow you to develop on the various repositories of the YunoHost project.

In particular, it allows you to:

- Create a directory with a clone of each repository of the YunoHost project
- Replace Yunohost debian packages with symlinks to those git clones

Because there are many diverse constraints on the development of the Yunohost
project, there is no "official" one-size-fits-all development environment.
However, we do provide documentation for what developers are using now in
various circumstances.

Please keep this in mind when reviewing the following options with regard to
your capacities and resources when aiming to setup a development environment.

`yhn-dev` can be used for the following scenarios:

### Local Development Path

Yunohost can be developed on using a combination of the following technologies:

- Git (any version is sufficient)
- Incus

Because LXC are containers, they are typically lightweight and quick to start and stop.
But you may find the initial setup complex (in particular network configuration).
Incus makes managing an LXC ecosystem much simpler.

This local development path allows to work without an internet connection,
but be aware that it will *not* allow you to easily test your email stack
or deal with deploying SSL certificates, for example, as your machine is
likely to not be exposed on the internet. A remote machine should be used
for these cases.

If choosing this path, please keep reading at the [local development
environment](#local-development-environment) section.

### Remote Development Path

Yunohost can be deployed as a typical install on a remote VPS. You can then use
`ynh-dev` to configure a development environment on the server.

This method can potentially be faster than the local development environment
assuming you have familiarity with working on VPS machines, if you always have
internet connectivity when working, and if you're okay with paying a fee. It
is also a good option if the required system dependencies (Incus/LXC, Virtualbox,
etc.) are not easily available to you on your distribution.

Please be aware that this method should **not** be used for a end-user facing
production environment.

If choosing this path, please keep reading at the [remote development
environment](#remote-development-environment) section.

## Local Development Environment

Here is the development flow:

1. Setup `ynh-dev` and the development environment
2. Manage YunoHost's development LXCs
3. Develop on your local host and testing in the container

### 1. Setup `ynh-dev` and the development environment

First you need to install the system dependencies.

`ynh-dev` essentially requires Git and the Incus/LXC ecosystem. Be careful that
**Incus/LXC can conflict with other installed virtualization technologies such as
libvirt or vanilla LXCs**, especially because they all require a daemon based
on DNSmasq and therefore require to listen on port 53.

Incus can be installed on Debian 13 or Ubuntu 24.04 with the following command:

```bash
apt install incus
```

If you have an older distribution, you need to add the Zabbly repository to your package manager.  
To do so please follow the installation guide that you can find on <https://github.com/zabbly/incus>.

You then need to add yourself in the incus-admin group, to run incus without sudo every time:

```bash
sudo usermod -a -G incus-admin $(whoami)
```

Now the group incus-admin should be present when you type the command:

```bash
groups
```

If not you need to create the group first:

```bash
newgrp incus-admin
sudo usermod -a -G incus-admin $(whoami)
```

Then you shall initialize Incus which will ask you a bunch of question. Usually
answering the default (just pressing enter) to all questions is fine.

```bash
incus admin init
```

Pre-built images are centralized on `https://repo.yunohost.org/incus` and we'll download them from there to speed things up:

```bash
incus remote add yunohost https://repo.yunohost.org/incus --protocol simplestreams --public
```

On Archlinux-based distributions (Arch, Manjaro, ...) it was found that it's needed
that Incus/LXC will throw some error about "newuidmap failed to write mapping / Failed
to set up id mapping" ... It can be [fixed with the following](https://discuss.linuxcontainers.org/t/solved-arch-linux-containers-only-run-when-security-privileged-true/4006/4) :

```bash
## N.B.: this is ONLY for Arch-based distros
echo "root:1000000:65536" > /etc/subuid
echo "root:1000000:65536" > /etc/subgid
```

Then, go into your favorite development folder and deploy `ynh-dev` with:

```bash
curl https://raw.githubusercontent.com/yunohost/ynh-dev/master/deploy.sh | bash
```

This will create a new `ynh-dev` folder with everything you need inside.

In particular, you shall notice that there are clones or the various git
repositories. In the next step, we shall start a LXC and 'link' those folders
between the host and the LXC.

### 2. Manage YunoHost's dev LXCs

When ran on the host, the `./ynh-dev` command allows you to manage YunoHost's dev LXCs.

Start your actual dev LXC using :

```bash
cd ynh-dev  # if not already done
./ynh-dev start
```

This should automatically download from `https://repo.yunohost.org/incus` a pre-build
ynh-dev LXC image running Yunohost unstable, and create a fresh container from it.

After starting the LXC, your terminal will automatically be attached to it. If you
later disconnect from the LXC, you can go back in with `./ynh-dev attach`. Later,
you might want to destroy the LXC. You can do so with `./ynh-dev destroy`.

If you container **doesn't have an ip address nor access to internet**, this is
likely because you either have a conflict with another virtualization system or
that a program running on the host is using the port 53 and therefore prevent
Incus's dnsmasq to run correctly (as stated before in the setup section.)

### 3. Development and container testing

After SSH-ing inside the container, you should notice that the *directory* `/ynh-dev` is a shared folder with your host.
In particular, it contains the various git clones `yunohost`, `yunohost-admin` and so on - as well as the `./ynh-dev` script itself.

**Most of the time, the first thing you'll want to do is to start by running `yunohost tools postinstall` as the first command**
(except if you are working on something that happens before the postinstall).

Inside the container, `./ynh-dev` can be used to link the git clones living in the host to the code being ran inside the container.

For instance, after running:

```bash
./ynh-dev use-git yunohost
```

The code of the git clone `'yunohost'` will be directly available inside the container.
Which mean that running any `yunohost` command inside the container will use the code from the host...
This allows to develop with any tool you want on your host, then test the changes in the container.

The `use-git` action can be used for any package among `yunohost`, `yunohost-admin`, `moulinette` and `ssowat` with similar consequences.
You might want to run use-git several times depending on what you want to develop precisely.

When using `use-git` on package `yunohost`, please do it also on its dependency package `moulinette`.
Both packages should be on branch `bookworm`.

***Note***: The `use-git` operation can't be reverted now. Do **not** do this in production.

### 4. Testing the web interface

You should be able to access the web interface via the IP address of the container.
The IP can be known from inside the container using either from `ip a` or with `./ynh-dev ip`.

If you want to access to the interface using the domain name, you shall tweak your `/etc/hosts` and add a line such as:

```bash
111.222.333.444 yolo.test
```

Note that `./ynh-dev use-git yunohost-admin` has a particular behavior: it starts a `gulp` watcher
that shall re-compile automatically any changes in the javascript code. Hence this particular `use-git`
will keep running until you kill it after your work is done.

### 5. Running the automated tests

In packages like `yunohost`, you have automated non-regression tests at your disposal (that you may change if you want to suggest changes).

> [!TIP]
> You might be interested in creating a separate incus container to run your tests than for the one you use for packages
>
> In such case, you may initiate or attach the container with a specific name, like:
>
> ```bash
> ./ynh-dev start bookworm ynh-test
> ```
>
> And run `yunohost tools postinstall` like for the other container.

To run the tests, assuming you have already run `./ynh-dev use-git PKG` within the container, you can use the following command:

```bash
./ynh-dev test PKG
```

For example, to run all Python tests for Yunohost (excluding bash helper tests):

```bash
./ynh-dev test yunohost
```

To run tests for a specific file, such as `tests/test_appurl.py`:

```bash
./ynh-dev test yunohost appurl
```

Or, to run a specific test function, like `test_urlaavailable()` within the `tests/test_appurl.py` file:

```bash
./ynh-dev test yunohost/appurl:urlavailable
```

Note that `./ynh-dev test` automatically installs the necessary dependencies (`pip`, `pytest`, `mock`) for test execution.

### Advanced: using snapshots

You can check `incus snapshot --help` to learn how to manage incus snapshots.

### Troubleshooting

If you experiment network issues with your incus during rebuild container steps. Probably your container are not able to get a local IP with DHCP.

It could be due to bridge conflict (for example if you have incus installed too) or dnsmasq port already used.

This [ticket](https://github.com/YunoHost/issues/issues/1664) could help.

If you have docker and incus, and your dns resolution inside incus container does not work at all, you can try:
```
sudo iptables -I DOCKER-USER -i incusbr0 -o eno1 -j ACCEPT
```

## Remote Development Environment

Here is the development flow:

1. Setup your VPS and install YunoHost
2. Setup `ynh-dev` and the development environment
3. Develop and test

### 1. Setup your VPS and install YunoHost

Setup a VPS somewhere (e.g. Scaleway, Digital Ocean, etc.) and install YunoHost following the [usual instructions](https://yunohost.org/#/install_manually).

Depending on what you want to achieve, you might want to run the postinstall right away - and/or setup a domain with an actually working DNS.

### 2. Setup `ynh-dev` and the development environment

Deploy a `ynh-dev` folder at the root of the filesystem with:

```bash
cd /
curl https://raw.githubusercontent.com/yunohost/ynh-dev/master/deploy.sh | bash
cd /ynh-dev
```

### 3. Develop and test

Inside the VPS, `./ynh-dev` can be used to link the git clones to actual the code being ran.

For instance, after running:

```bash
./ynh-dev use-git yunohost
```

Any `yunohost` command will run from the code of the git clone.

The `use-git` action can be used for any package among `yunohost`, `yunohost-admin`, `moulinette` and `ssowat` with similar consequences.

## Further Resources

- [yunohost.org/dev](https://yunohost.org/dev)
