#!/bin/bash

read -p "This script will create a new 'ynh-dev' folder with a dev environment inside. Is this okay ? [Y/N]" -n 1 -r
echo $REPLY
[[ $REPLY =~ ^[Yy]$ ]] || { echo "Aborting."; exit 1; }

set -x

sudo apt-get install vagrant lxc git -y

git clone https://github.com/YunoHost/ynh-dev
cd ./ynh-dev
git clone https://github.com/YunoHost/moulinette
git clone https://github.com/YunoHost/yunohost
git clone https://github.com/YunoHost/yunohost-admin
git clone https://github.com/YunoHost/SSOwat ssowat

mkdir -p apps

set +x

echo " "
echo "---------------------------------------------------------------"
echo "Done ! You should cd into 'ynh-dev' then run './ynh-dev --help'"
echo "---------------------------------------------------------------"
echo " "
