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
TICK_FREQ=4
TIME_BASE=250
MSWITCH_OBSERVE_MODE=True

import os
import sys

curdir=os.path.dirname(__file__)
sys.path.insert(0, curdir)
print curdir

import gobject
import dbus.glib
from dbus.mainloop.glib import DBusGMainLoop

gobject.threads_init()  #@UndefinedVariable
dbus.glib.init_threads()
DBusGMainLoop(set_as_default=True)


import rhythmdb, rb #@UnresolvedImport

from system.base import TickGenerator
from system.mbus import Bus
from helpers.db import EntryHelper

import system.base as base
base.debug=DEV_MODE

import system.mswitch as mswitch
mswitch.observe_mode=MSWITCH_OBSERVE_MODE

import agents.bridge

from helpers.server import Server
from helpers.player import Player


class SqueezeboxPlugin (rb.Plugin):
    """
    Must derive from rb.Plugin in order
    for RB to use the plugin
    """
    BUSNAME="__pluging__"
    
    def __init__ (self):
        rb.Plugin.__init__ (self)
        self.spcb=None
        
        Bus.subscribe(self.BUSNAME, "devmode?", self.hq_devmode)
        Bus.subscribe(self.BUSNAME, "appname?", self.hq_appname)
        Bus.subscribe(self.BUSNAME, "__tick__", self.h_tick)

    def activate (self, shell):
        """
        Called by Rhythmbox when the plugin is activated
        """
        self.active=True
        self.shell = shell
        self.sp = shell.get_player()
        self.db=self.shell.props.db
        

        ##
        self.spcb = (
                     self.sp.connect("playing-changed",        self.on_playing_changed),
                     self.sp.connect("playing-song-changed",   self.on_playing_song_changed),
                     )
        
        ## Distribute the vital RB objects around
        Bus.publish("__pluging__", "rb_shell", self.shell, self.db, self.sp)
        
        self.type_song=self.db.entry_type_get_by_name("song")
        
        self._reconnect()
        
    def deactivate (self, shell):
        """
        Called by RB when the plugin is about to get deactivated
        """
        self.shell = None
            
        for id in self.spcb:
            self.sp.disconnect(id)

    ## ================================================  rb signal handlers

    def on_playing_changed(self, player, playing, *_):
        """
        """
        print "playing: %s" % playing

    def on_playing_song_changed(self, player, entry, *_):
        """
        """
        td=EntryHelper.track_details2(self.db, entry)
        print td

    ## ================================================ message handlers
    
    def hq_appname(self):
        Bus.publish(self.BUSNAME, "appname", PLUGIN_NAME)
        
    def hq_devmode(self):
        Bus.publish(self.BUSNAME, "devmode", DEV_MODE)

    def h_tick(self, ticks_per_second, 
               second_marker, min_marker, hour_marker, day_marker,
               sec_count, min_count, hour_count, day_count):
        """        
        """

    def _reconnect(self):
        try:
            self.sc = Server(hostname="127.0.0.1", port=9090)
            self.sc.connect()
            
            self.players = self.sc.get_players()
            self.player=self.players[0]
        except:
            self.player=None
        


def tick_publisher(*p):
    Bus.publish("__main__", "__tick__", *p)

_tg=TickGenerator(1000/TIME_BASE, tick_publisher)
gobject.timeout_add(TIME_BASE, _tg.input)
