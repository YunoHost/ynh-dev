# ynh-dev, a yunohost dev env

This script is a cli to manage a yunohost development environement.
With this you can develop on the unstable version of yunohost quickly.

## Setup

Install dependencies
```shell
# Debian, Ubuntu, Mint
sudo apt-get install vagrant
# Fedora
sudo dnf install vagrant vagrant-libvirt
```

Next download ynh-dev script

```shell
wget https://raw.githubusercontent.com/zamentur/yunohost-development/master/ynh-dev
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
```
cd /path/to/dev/env
./ynh-dev run ynh.local virtualbox testing
```

## Inside the Virtual machine (VM)

Once logged into your VM, go to `/vagrant` to enjoy folder sharing, and take
advantages of the `ynh-dev` script.

###  Upgrade the container
```
ynh-dev/ynh-dev upgrade
```

###  Deploy your change
```
ynh-dev/ynh-dev deploy
```

### Deploy your change in realtime (each time you saved source code)
```
ynh-dev/ynh-dev watch
```

### Get ip address of your vm
```
ynh-dev/ynh-dev ip
```

## More info 

https://yunohost.org/#/dev_fr (french)
