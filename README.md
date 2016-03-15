# ynh-dev, a yunohost dev env
This script is a cli to manage a yunohost development environement. With this you can develop on the unstable version of yunohost quickly.

## Setup
Install dependencies
```shell
# Debian, Ubuntu, Mint
sudo apt-get install docker vagrant
# Fedora
sudo dnf install docker vagrant vagrant-libvirt
```

Next download ynh-dev script

```shell
wget https://raw.githubusercontent.com/zamentur/yunohost-development/master/ynh-dev
chmod u+x ynh-dev
```
## Usage
### Create the environment

```shell
ynh-dev create-env /path/to/dev/env
```

### Run a container
```
ynh-dev run ynh.local virtualbox testing8
```

###  Upgrade the container
```
ynh-dev upgrade
```

###  Deploy your change
```
ynh-dev deploy
```

### Deploy your change in realtime (each time you saved source code)
```
ynh-dev watch
```
## Useful command
### Get ip address of your vm
```
ynh-dev ip
```

## More info 

https://yunohost.org/#/dev_fr (french)
