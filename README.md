# ynh-dev, a yunohost dev env

This script is a Command line tool to manage your local development environement for YunoHost
With this you can develop on the unstable version of YunoHost quickly.

This tool allow you:

 * to create a directory with a clone of each repository
 * to replace already installed yunohost debian packages by symlinks from those reporistories
 * if needed, to manage yunohost instances on your host machine with vagrant by:
   * creating yunohost vagrant vm
   * sharing folder between your host and your yunohost vagrant vm (so you can develop directly on your host)
   * finding the ip address of your yunohost vagrant vm

There are 2 ways to use this tools:

1. on your host machine (more comfortable)
2. on an existing yunohost instance (for exemple if you need the vm is exposed on internet: test let's encrypt, test email ...)


## 1. Use this tool with your host machine
Here is the development flow:

1. [first time] Setup ynh-dev and Setup a copy of each git repository
2. Create or run a yunohost vagrant instance
3. Upgrade, postinstall and deploy development version from repositories
4. Code on your host
5. Test by cli on the instance or test on your host browser
6. Suspend or kill your vm

### 1.1 [first time] Setup ynh-dev and Setup a copy of each git repository
These operation need to be done on the host machine.

#### Install dependencies
##### Debian, Ubuntu, Mint
```shell
sudo apt-get install vagrant virtualbox git
```

##### Fedora
```shell
sudo dnf install vagrant git
```

 VirtualBox 5.1.4 only works with Vagrant ≥ 1.8.5. It could be installed from Fedora 25 or [rawhide](https://stackoverflow.com/a/24968411).
- [Install Virtualbox 5.1.x](http://www.if-not-true-then-false.com/2010/install-virtualbox-with-yum-on-fedora-centos-red-hat-rhel)


#### Install ynh-dev
```shell
wget https://github.com/YunoHost/ynh-dev/raw/master/ynh-dev
chmod u+x ynh-dev
```

#### Create the environment
This command create a clone of main git repositories and organize its.
```shell
./ynh-dev create-env /path/to/dev/env
```

### 1.2 Create or run a yunohost vagrant instance

This command is a helper to run a Vagrant virtual machine in the right place with YunoHost installed (but not postinstalled).
```shell
cd /path/to/dev/env
./ynh-dev run ynh.local unstable
```

The `run` command takes 2 arguments: domain and YunoHost version.

After running the container, you'll be automatically logged inside a new yunohost VM or inside the previous suspended VM.

#### Sharing folder between host and virtual machines

A shared folder between host and virtual machines could ease your development.
Once logged into your VM, go to `/vagrant` to enjoy folder sharing, and take
advantages of the `ynh-dev` script.

### 1.3 Upgrade, postinstall and use git repositories

According to what you want to test or code, you could need to upgrade, to postinstall and to deploy core code in this order or no.

For example if you want :

* to test an app => upgrade and postinstall
* to test a common core code => upgrade, postinstall and deploy your code
* to test the impact of a core code on postinstall => upgrade, deploy your code, postinstall

#### Upgrade
May be the container is not up to date.

It will update every debian packages, including YunoHost ones.
```shell
/vagrant/ynh-dev upgrade
```

You could need to update ynh-dev script, to do it:
```shell
/vagrant/ynh-dev self-update
```

#### Postinstall

If it's a new yunohost container, you probably want to run the postinstall now:

```shell
(sudo) yunohost tools postinstall -d ynh.local
```

#### Use your git repositories in place of debian package

When doing `create-env` command, every YunoHost package have been cloned in the
corresponding path. Use these Git repositories inside the VM (with symlink).
Your changes will be available immediatly in your VM.

    /vagrant/ynh-dev use-git

***Note***: These changes can't be reverted now.

Alternatively you can use Git only for one packages (ssowat, yunohost,
moulinette, yunohost-admin)

    /vagrant/ynh-dev use-git PACKAGE_NAME

### 1.4 Code on your host
At this point, you are able to code on your host machine, with the EDI of your choice.

All change will be available on the container inside the share folder /vagrant.


### 1.5 Test by cli on the instance or test on your host browser
#### Test by cli on the container
If you have run use-git, all change on core git repositories are automatically deployed on your container, so you can test your code.

#### Test on your host browser
If you want to test on your host browser, you need to know the ip addres.

You can get the ip address of your container by running this command inside the container

    /vagrant/ynh-dev ip

Next, you just have to write the ip inside your browser.

You probably want access by local domain name, to do that you can edit your /etc/hosts file to add a line like this:

IP_ADDRESS LOCAL_DOMAIN

### 1.6. Suspend or kill your vm
When you have finished or if you want to shut down you computer, you should kill or suspend the VM

To kill the vm, just do on your host:

```shell
cd /path/to/dev/env
vagrant destroy unstable
# or
./ynh-dev kill
```

To suspend the vm

```shell
cd /path/to/dev/env
vagrant suspend unstable
```

To halt a vm:

```bash
./ynh-dev halt
```

## 2. Directly on a YunoHost instance

Firstly, you need to understand that it is a dev tool, you shouldn't run it on a production environment !

This case allow you to use ynh-dev on a vm exposed on the internet.

It could be useful to develop code using external services which need to be able to reach your vm. Let's encrypt is a good example. An other way, is to use the first method with the vpnclient_ynh apps and a VPN with an ipv4 associated.

The development flow is quite similar to the first method:

1. [first time] Setup ynh-dev and Setup a copy of each git repository
2. Upgrade, postinstall and deploy development version from repositories
3. Code on your host
4. Test by cli on the instance or test on your host browser

### 2.1. Setup
It's possible to setup ynh-dev inside an existing instance of YunoHost rather than create vagrant vm with ynh-dev. In this particular case, you need to setup your env inside a /vagrant directory even if you don't use vagrant.

```shell
sudo apt-get install git
wget https://github.com/YunoHost/ynh-dev/raw/master/ynh-dev
chmod u+x ynh-dev
./ynh-dev create-env /vagrant
```
### 2.2 Upgrade, postinstall and use git repositories
Identical to 1.3, but take care to don't postinstall on a yunohost already postinstalled !

Important, when you use the git repositories, you can't do the reverse operation simply... (To do it you need to wait an update of the concern package)

### 2.3 Code on the instance directly
Contrary to the first method, you have not a share folder so you need to develop inside the instance. Alternatively, you could explore to setup sshfs or this kind of solution.

### 2.4 Test
Identical to 1.5, but ynh-dev ip doesn't work. You should prefer this command to find your ip address:

    ip addr

Keep in mind, that if you use your /etc/hosts file, let's encrypt or other service couldn't access the VM. So you probably need to set up a correct domain.



## More info

[yunohost.org/dev_fr](https://yunohost.org/dev_fr) (in french) not up-to-date.
