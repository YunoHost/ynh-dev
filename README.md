# ynh-dev, a yunohost dev env

This script is a cli to manage a yunohost development environement.
With this you can develop on the unstable version of yunohost quickly.

## Setup

Install dependencies
```shell
# Debian, Ubuntu, Mint
sudo apt-get install vagrant
# Fedora
sudo dnf install vagrant
```

Next download ynh-dev script

```shell
wget https://github.com/YunoHost/ynh-dev/raw/opi-boxes/ynh-dev
chmod u+x ynh-dev
```

## Host usage

The `ynh-dev` tool provides 2 usefull command to run into your host machine. One
create a development environment by cloning Git repositories, the other one is a
helper to run a Vagrant virtual machine in the right place.

### Create the environment

```shell
./ynh-dev create-env /path/to/dev/env
```

### Run a container
```shell
cd /path/to/dev/env
./ynh-dev run ynh.local virtualbox testing
```

You'll be automatically logged in the VM through ssh.

You probably wan't to run the postinstall now:

    (sudo) yunohost tools postinstall -d ynh.local

## Inside the Virtual machine (VM)

Once logged into your VM, go to `/vagrant` to enjoy folder sharing, and take
advantages of the `ynh-dev` script.

###  Upgrade the container

It will update every debian packages, including YunoHost ones.

    /vagrant/ynh-dev upgrade

###  Use Git repositories

When doing `create-env` command, every YunoHost package have been cloned in the
corresponding path. Use these Git repositories inside the VM (with symlink).
Your changes will be available immediatly in your VM.

    /vagrant/ynh-dev use-git

***Note***: These changes can be reverted now.

Alternatively you can use Git only for one packages (ssowat, yunohost,
moulinette, yunohost-admin)

    /vagrant/ynh-dev use-git PACKAGE_NAME


### Get ip address of your vm

    /vagrant/ynh-dev ip


### Update `ynh-dev` script

    /vagrant/ynh-dev self-update


## More info 

[yunohost.org/dev_fr](https://yunohost.org/dev_fr) (in french)
