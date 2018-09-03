# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

NETWORK = "192.168.33."

HOSTS = {
   "ynh-dev" => ["83", "stretch-unstable"],
   "ynh-dev-buster" => ["84", "buster-unstable"],
}

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  
  # Force guest type, because YunoHost /etc/issue can't be tuned
  config.vm.guest = :debian
  
  HOSTS.each do | (name, cfg) |
    ipaddr, version = cfg
    
    config.vm.define name do |machine|
      machine.vm.box = "yunohost/" + version
      # Force guest type, because YunoHost /etc/issue can't be tuned
      machine.vm.guest = :debian

      machine.vm.provider "lxc" do |lxc|
        config.vm.box_url = "https://build.yunohost.org/yunohost-" + version + "-lxc.box" 
        config.vm.synced_folder ".", "/ynh-dev", id: "vagrant-root"
        config.vm.network :private_network, ip: NETWORK + ipaddr, lxc__bridge_name: 'lxcbr0' 
      end
    end
  end # HOSTS-each

end
