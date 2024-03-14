#!/usr/bin/env bash
set -x

git clone https://github.com/yunohost/ynh-dev
cd ./ynh-dev || exit 1
git clone https://github.com/YunoHost/moulinette
git clone https://github.com/YunoHost/yunohost
git clone https://github.com/YunoHost/yunohost-admin
git clone https://github.com/YunoHost/SSOwat ssowat
git clone https://github.com/YunoHost/yunohost-portal

mkdir -p apps

set +x

echo " "
echo "---------------------------------------------------------------------"
echo "Done ! You should cd into 'ynh-dev' then check out './ynh-dev --help'"
echo "---------------------------------------------------------------------"
echo " "
