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

yhn-dev can be used either :
1. on your local machine with LXCs (you can peacefully develop independently of your internet connection)
2. on a remote machine dedicated to dev (e.g. if you need the VM to be exposed on internet : test let's encrypt, email stack ...)

## Develop on your local machine

Here is the development flow:

1. Setup ynh-dev and the development environnement
2. Manage YunoHost's dev LXCs
3. Developping on your host, and testing in the container

### 1. Setup ynh-dev and the development environnement

First you need to install the dependencies. ynh-dev essentially requires git, vagrant, and an LXC ecosystem.

Please consider using the [latest Vagrant version from their website](https://www.vagrantup.com/downloads.html), distribution versions can include weird bugs that have been fixed upstream. If you still prefer to do that, here are the instructions:

The following commands should work on **Linux Mint 19** (and possibly on any Debian Stretch?) :

```bash
sudo apt update
sudo apt install git vagrant lxc-templates lxctl lxc cgroup-lite redir bridge-utils libc6 debootstrap
vagrant plugin install vagrant-lxc
echo "cgroup        /sys/fs/cgroup        cgroup        defaults    0    0" | sudo tee -a /etc/fstab
sudo mount /sys/fs/cgroup
lxc-checkconfig
echo "veth" | sudo tee -a /etc/modules
```

On **Debian Buster**, I had to re-patch the driver.rb of vagrant-lxc plugin with [this version](https://raw.githubusercontent.com/fgrehm/vagrant-lxc/2a5510b34cc59cd3cb8f2dcedc3073852d841101/lib/vagrant-lxc/driver.rb) (especially the `roofs_path` function). I also had to install `apparmor` then `systemctl restart apparmor` for `lxc-start` to work. Also check instruction on https://feeding.cloud.geek.nz/posts/lxc-setup-on-debian-stretch/

If you run **Archlinux**, this page should be quite useful to setup LXC : https://github.com/fgrehm/vagrant-lxc/wiki/Usage-on-Arch-Linux-hosts

On **both Debian and Archlinux**, typically `/etc/default/lxc-net` and `/etc/lxc/default.conf` should look like this :

```
 > cat /etc/default/lxc-net
USE_LXC_BRIDGE="true"
LXC_BRIDGE="lxcbr0"
LXC_ADDR="10.0.3.1"
LXC_NETMASK="255.255.255.0"
LXC_NETWORK="10.0.3.0/24"
LXC_DHCP_RANGE="10.0.3.2,10.0.3.254"
LXC_DHCP_MAX="253"

> cat /etc/lxc/default.conf
lxc.net.0.type = veth
lxc.net.0.link = lxcbr0
lxc.net.0.flags = up
lxc.net.0.hwaddr = 00:16:3e:xx:xx:xx
```

On **Debian Buster**, for backup stuff to work correctly with apparmor, I also had to add `mount options=(ro, remount, bind, rbind),` to `/etc/apparmor.d/lxc/lxc-default-cgns` and restart the apparmor service.

Then, go into your favorite development folder and deploy ynh-dev with :

```bash
curl https://raw.githubusercontent.com/yunohost/ynh-dev/master/deploy.sh | bash
```

This will create a new `ynh-dev` folder with everything you need inside. In particular, you shall notice that there are clones or the various git repositories. In the next step, we shall start a LXC and 'link' those folders between the host and the LXC.

### 2. Learn how to manage YunoHost's dev LXCs

When ran on the host, the `./ynh-dev` command allows you to manage YunoHost's dev LXCs.

First, you might want to start a new LXC with :

```bash
cd ynh-dev  # if not already done
./ynh-dev start
```

This should download an already built LXC from `build.yunohost.org`. If this does not work (or the LXC is outdated), you might want to (re)build a fresh LXC locally with `./ynh-dev rebuild`.

After starting the LXC, you should be automatically SSH'ed inside. If you later disconnect from the LXC, you can go back in with `./ynh-dev ssh`

Later, you might want to destroy the LXC. You can do so with `./ynh-dev destroy`.


### 3. Developping on your host, and testing in the container

After SSH-ing inside the container, you should notice that the *directory* `/ynh-dev` is a shared folder with your host. In particular, it contains the various git clones `yunohost`, `yunohost-admin` and so on - as well as the `./ynh-dev` script itself.

Inside the container, `./ynh-dev` can be used to link the git clones living in the host to the code being ran inside the container.

For instance, after running

```bash
./ynh-dev use-git yunohost
```

the code of the git clone `'yunohost'` will be directly available inside the container. Which mean that running any `yunohost` command inside the container will use the code from the host... This allows to develop with any tool you want on your host, then test the changes in the container.

The `use-git` action can be used for any package among `yunohost`, `yunohost-admin`, `moulinette` and `ssowat` with similar consequences. You might want to run use-git several times depending on what you want to develop precisely.

***Note***: The `use-git` operation can't be reverted now. DON'T DO THIS IN PRODUCTION !


#### Testing the web interface

You should be able to access the web interface via the IP address of the container. The IP can be known from inside the container using either from `ip a` or with `./ynh-dev ip`.

If you want to access to the interface using the domain name, you shall tweak your /etc/hosts and add a line such as:

```bash
111.222.333.444 yolo.test
```

Note that `./ynh-dev use-git yunohost-admin` has a particular behavior : it starts a `gulp` watcher that shall re-compile automatically any changes in the javascript code. Hence this particular `use-git` will keep running until you kill it after your work is done.


#### Advanced : using snapshots

Vagrant is not well integrated with LXC snapshots. However, you may still use `lxc-snapshot` directly to manage snapshots.

## Develop on a remote server

Instead of running a LXC locally, you may choose (or need) to develop on a dev VPS. *Be aware that this is a dev tool : do NOT run this procedure on a production environment !*.

Since you do not need to manage LXC, the setup is somewhat "easier" :

1. Setup your VPS and install YunoHost
2. Setup ynh-dev and the development environnement
3. Develop and test

### 1. Setup your VPS and install YunoHost

Setup a VPS somewhere (e.g. Scaleway, Digital Ocean, ...) and install YunoHost following https://yunohost.org/#/install_manually

Depending on what you want to achieve, you might want to run the postinstall right away - and/or setup a domain with an actually working DNS.

### 2. Setup ynh-dev and the development environnement

Deploy a `ynh-dev` folder at the root of the filesystem with :

```
cd /
curl https://raw.githubusercontent.com/yunohost/ynh-dev/master/deploy.sh | bash
cd /ynh-dev
```

### 3. Develop and test

Inside the VPS, `./ynh-dev` can be used to link the git clones to actual the code being ran.

For instance, after running

```bash
./ynh-dev use-git yunohost
```

any `yunohost` command will run from the code of the git clone. The `use-git` action can be used for any package among `yunohost`, `yunohost-admin`, `moulinette` and `ssowat` with similar consequences.

## More info

[yunohost.org/dev_fr](https://yunohost.org/dev_fr) (in french) not up-to-date.
