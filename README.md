Rhythmbox pluging for controlling Squeezebox

Installation
============
There are 3 methods:

1. Use the Ubuntu Debian repository [jldupont](https://launchpad.net/~jldupont/+archive/jldupont)  with the package "rb-squeezebox"

2. Download a 'tag' from the git repo and place the "squeezebox" folder in ".gnome2/rhythmbox/plugins

3. Use the "Download Source" function of this git repo and place the "squeezebox" folder in "~/.gnome2/rhythmbox/plugins

Note that option #3 isn't preferred as one might get an "unstable" snapshot. 


Usage
=====

When the plugin is enabled, a "gnome network icon" (I didn't find the way to use a custom image at this time, sorry) will be displayed in Rhythmbox toolbar at the top.
Each press of the button will toggle between "activated" and "deactivated" state of the Squeezebox control.

In the "activated" mode, Rhythmbox's current volume setting will be saved and muted.  Each track played will be relayed to the first Squeezebox found on the network.

In the "deactivated" mode, the volume setting will be restored.  


History
=======

0.1 : initial release

0.2 : added track seek feature i.e. when the user drags the time tracking cursor