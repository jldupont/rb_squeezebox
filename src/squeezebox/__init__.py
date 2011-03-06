"""
    Squeezebox - Rhythmbox plugin

    @author: Jean-Lou Dupont
    
    MESSAGES OUT:
    =============
    - "appname"
    - "devmode"
    - "tick"
    
"""
DEV_MODE=True
PLUGIN_NAME="squeezebox"
TICK_FREQ=1
TIME_BASE=1000
MSWITCH_OBSERVE_MODE=True

import os, sys

curdir=os.path.dirname(__file__)
sys.path.insert(0, curdir)

import gobject, dbus.glib
from dbus.mainloop.glib import DBusGMainLoop

gobject.threads_init()  #@UndefinedVariable
dbus.glib.init_threads()
DBusGMainLoop(set_as_default=True)

from system.base import TickGenerator
from system.mbus import Bus

import system.base as base
base.debug=DEV_MODE

import system.mswitch as mswitch
mswitch.observe_mode=MSWITCH_OBSERVE_MODE

import rhythmdb, rb #@UnresolvedImport

import agents.bridge
from agents.main import PluginAgent

class SqueezeboxPlugin (rb.Plugin):
    
    BUSNAME="__pluging__"
    
    def __init__ (self):
        rb.Plugin.__init__ (self)
        self.main=PluginAgent()
        Bus.subscribe(self.BUSNAME, "devmode?", self.hq_devmode)
        Bus.subscribe(self.BUSNAME, "appname?", self.hq_appname)

    def activate (self, shell):
        """
        When RB activates this plugin
        """
        self.main.activate(shell)
        
    def deactivate(self, shell):
        """
        When RB deactivates this plugin
        """
        self.main.deactivate(shell)

    ## ======================================================= Message Handlers
            
    def hq_appname(self):
        Bus.publish(self.BUSNAME, "appname", PLUGIN_NAME)
        
    def hq_devmode(self):
        Bus.publish(self.BUSNAME, "devmode", DEV_MODE)

        


def tick_publisher(*p):
    Bus.publish("__main__", "__tick__", *p)

_tg=TickGenerator(1000/TIME_BASE, tick_publisher)
gobject.timeout_add(TIME_BASE, _tg.input)
