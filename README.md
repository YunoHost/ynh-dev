# ynh-dev - Yunohost dev environnement manager

Report issues here: https://github.com/yunohost/issues

ynh-dev is a CLI tool to manage your local development environement for YunoHost. This allow you to develop on the various repository of the YunoHost project.

In particular, it allows :

 * to create a directory with a clone of each repository of the YunoHost project ;
 * to replace already installed yunohost debian packages by symlinks to those git clones ;
 * to manage yunohost instances on your host machine with Vagrant by:
   * creating a Vagrant VM with a pre-installed Yunohost system ;
   * sharing the dev environnement your host the VM (so you can develop directly on your host)
   * finding the ip address of your yunohost vagrant vm

yhn-dev can be used :

1. on your local machine with VMs (more comfortable)
2. on a remote machine dedicated to dev (e.g. if you need the VM to be exposed on internet : test let's encrypt, email stack ...)

## Develop on your local machine

Here is the development flow:

1. [first time] Setup ynh-dev and the development environnement
2. Create or run a yunohost vagrant instance
3. Upgrade, postinstall and deploy development version from repositories
4. Develop on your host
5. Test via the CLI or webadmin
6. Suspend or kill your vm

### 1. [first time] Setup ynh-dev and the development environnement

These operation need to be done on the host machine.

#### Install dependencies

- Debian, Ubuntu, Mint

```bash
sudo apt-get install vagrant virtualbox git
```

- Fedora

```bash
sudo dnf install vagrant git
```

[Install Virtualbox 5.1.x](http://www.if-not-true-then-false.com/2010/install-virtualbox-with-yum-on-fedora-centos-red-hat-rhel)

- Archlinux, Manjaro

```bash
sudo pacman -S vagrant virtualbox git
sudo pacman -S linux44-virtualbox-host-modules
sudo modprobe vboxdrv
sudo modprobe vboxnetadp
sudo insmod /lib/modules/4.4.33-1-MANJARO/extramodules/vboxnetflt.ko.gz 
sudo insmod /lib/modules/4.4.33-1-MANJARO/extramodules/vboxnetadp.ko.gz
```


#### Install ynh-dev

Clone the ynh-dev repo :

```bash
git clone https://github.com/YunoHost/ynh-dev
cd ynh-dev
```

#### Create the environment

This command create a clone of all Yunohost's main git repositories in `./`.

```bash
./ynh-dev create-env ./
```

### 2. Create or run a yunohost vagrant instance

This command is a helper to run a Vagrant virtual machine in the right place with YunoHost pre-installed.

```bash
./ynh-dev run yolo.test stretch-unstable
```

The `run` command takes 2 arguments: domain and YunoHost version.

After running the container, you'll be automatically logged inside a new yunohost VM or inside the previous suspended VM.

If you meet an error with `vboxsf` you might need to install the guest addons:

```bash
vagrant plugin install vagrant-vbguest
```

#### Shared folder between host and virtual machines

One logged into the VM, you can go to `/vagrant` and find all the files from your dev environnement, including the `ynh-dev` script itself.

### 3. Upgrade and configure your dev instance

According to what you intend to develop or test, you might need to upgrade, to postinstall.

For example if you want :

* to test an app => upgrade and postinstall
* to test a common core code => upgrade, postinstall and deploy your code
* to test the impact of a core code on postinstall => upgrade, deploy your code, postinstall

#### Upgrade

If the container is not up to date, you can run the following command to update debian packages, including YunoHost ones.

```bash
/vagrant/ynh-dev upgrade
```

#### Use your git repositories in place of debian package

When doing `create-env` command, every YunoHost package have been cloned in the
corresponding path. You can link your VM to use these git clones such that changes you make in the code are directly used in the VM :

```bash
/vagrant/ynh-dev use-git PACKAGE
```

PACKAGE should can be ssowat, yunohost, moulinette or yunohost-admin. You might want to run use-git several times depending on what you want to develop precisely.

***Note***: The `use-git` operation can't be reverted now. DON'T DO THIS IN PRODUCTION !


#### Postinstall

If you need a properly installed YunoHost to develop and test, you probably want to run the postinstall now:

```bash
(sudo) yunohost tools postinstall -d yolo.test
```

### 4. Develop on your host
At this point, you are able to code on your host machine, with the EDI of your choice.

All change will be available on the container inside the share folder /vagrant.


### 5. Test changes via the CLI or the web interface

#### Tests in CLI

If you have run `use-git`, all changes on the local git clones are automatically available in your VM, so you can run any `yunohost foo bar` command.

#### Tests the web interface

You should be able to access the web interface via the IP address on the vagrant container. The IP can be known from inside the container with :

```bash
/vagrant/ynh-dev ip
```

If you want to access to the interface using the domain name, you shall tweak your /etc/hosts and add a line such as:

```bash
111.222.333.444 yolo.test
```

### 6. Suspend or kill your vm

When you're finished or if you want to shut down your computer, you should kill or suspend the VM.

To kill the vm (this will destroy it), just do on your host:

```bash
cd /path/to/dev/env
vagrant destroy stretch-unstable
# or
./ynh-dev kill
```

To suspend the VM:

```bash
cd /path/to/dev/env
vagrant suspend stretch-unstable
```

Alternatively you can shut it down:

```bash
cd /path/to/dev/env
vagrant halt stretch-unstable
```

## 7. Other common operation

There are several other operations that you might want to perform directly
using Vagrant. All those operation needs to be done in the environment (where
the VagrantFile is located).

Show vagrant commands:

    vagrant

See all running boxes:

    vagrant status

Open a terminal on a running box:

    vagrant ssh stretch-unstable

Start a box (only do that after the boxe as already been created by ynh-dev)

    vagrant up stretch-unstable

## Develop on a remote server

Firstly, you need to understand that it is a dev tool : you shouldn't run it on a production environment !

This case allows you to use ynh-dev on a vm exposed on the internet. This can be useful when testing features for which the server is required to be reachable from the whole internet (e.g. Let's Encrypt certificate install, or mail-related features). An alterative is to use a VPN (through vpnclient_ynh) with an IPv4.

The development flow is quite similar to the first method:

1. [first time] Setup ynh-dev and Setup a copy of each git repository
2. Upgrade, postinstall and deploy development version from repositories
3. Code on your host
4. Test by cli on the instance or test on your host browser

### 1. Setup

It's possible to setup ynh-dev inside an existing instance of YunoHost rather than create vagrant vm with ynh-dev. In this particular case, you need to setup your env inside a `/vagrant/` directory even if you don't use vagrant.

```bash
sudo apt-get install git
git clone https://github.com/YunoHost/ynh-dev /vagrant/
cd /vagrant/
```

### 2. Upgrade, postinstall and use git repositories

Identical to 1.3, but take care to don't postinstall on a yunohost already postinstalled !

Important, when you use the git repositories, you can't do the reverse operation simply... (To do it you need to wait an update of the concern package)

### 3. Code on the instance directly

Contrary to the first method, you have not a share folder so you need to develop inside the instance. Alternatively, you could explore to setup sshfs or this kind of solution.

### 4. Test

Identical to 1.5, but ynh-dev ip doesn't work. You should prefer this command to find your ip address:

```bash
ip addr
```

Keep in mind, that if you use your /etc/hosts file, let's encrypt or other service couldn't access the VM. So you probably need to set up a correct domain.



## More info

[yunohost.org/dev_fr](https://yunohost.org/dev_fr) (in french) not up-to-date.
