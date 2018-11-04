#!/bin/bash

# Compute box name
BOX="ynh-dev"

# Create box
vagrant up $BOX

# Package box
vagrant package $BOX --output /tmp/$BOX.box

# Destroy current box
vagrant destroy $BOX

# User message, and exit
echo ""
echo "Your Vagrant box was packaged to /tmp/$BOX.box"
echo "You might want to run : vagrant box add 'yunohost/ynh-dev' /tmp/$BOX.box"
exit
