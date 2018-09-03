# Build your own YunoHost Vagrant box

## Get Debian base boxes

```bash
vagrant box add debian/stretch64
```

## Build YunoHost boxes

Download the vagrant file to build from debian boxes

```bash
wget https://raw.githubusercontent.com/YunoHost/Vagrantfile/master/prebuild/Vagrantfile
```

## Run your homemade boxes

Run the box you need by calling `vagrant up DEBIAN_CODENAME-YUNOHOST_VERSION`

```bash
vagrant up stretch-unstable --provider lxc
```

- `DEBIAN_CODENAME`: `jessie` or `stretch`
- `DISTRIB`: `unstable`.

You can now log into your box with `vagrant ssh stretch-unstable`

## Package your own boxes

You can package it to use it more quickly later:

```bash
vagrant up stretch-unstable --provider lxc
vagrant package stretch-unstable  --output ./my-yunohost-stretch-unstable-lxc.box --provider lxc
vagrant box add my-yunohost/stretch-unstable ./my-yunohost-stretch-unstable-lxc.box --provider lxc
```
