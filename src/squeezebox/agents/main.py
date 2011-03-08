"""
    Created on 2011-03-06

    @author: jldupont
"""
import os
import gtk, urllib

from squeezebox.system.mbus import Bus
from squeezebox.helpers.server import Server
#from squeezebox.helpers.player import Player
from squeezebox.helpers.db import EntryHelper
from squeezebox.system.os import filtered_mounts, lookup_mount

context_ui = """
<ui>
    <toolbar name="ToolBar">
        <toolitem name="Squeebox" action="ActivateSqueezeboxMode" />
    </toolbar>
</ui>
"""

class PluginAgent(object):
    
    BUSNAME="__main__"
    MOUNTS_REFRESH_INTERVAL=2 #minutes
    
    def __init__ (self):
        self.spcb=None
        self.activated=False
        self.volume=0
        self.playing=False
        self.current_pos=0
        self.this_dir=os.path.dirname(__file__)
        
        Bus.subscribe(self, "__tick__", self.h_tick)

    def init_toolbar(self):
        """
        TODO: Not able yet to force a custom image for the ToggleAction...
        """
        #print "this_dir: %s" % self.this_dir
        #path=os.path.join(self.this_dir, "squeezecenter.gif" )
        #print path
        #pixbuf = gtk.gdk.pixbuf_new_from_file(path)
        #image=gtk.Image()
        #image.set_from_pixbuf(pixbuf)
        
        self.action = ('ActivateSqueezeboxMode',"gtk-network", _('SqueezeboxTools'),
                        None, _('Activate Squeezebox mode'),
                        self.activate_button_press, True)
        self.action_group = gtk.ActionGroup('SqueezeboxPluginActions')
        self.action_group.add_toggle_actions([self.action])
        #action=self.action_group.get_action("ActivateSqueezeboxMode")
        #print dir(action)
        #action.do_add_child(image)
        
        uim = self.shell.get_ui_manager()
        uim.insert_action_group (self.action_group, 0)
        self.ui_id = uim.add_ui_from_string(context_ui)
        #self.ui_id.insert_item("Text", "Tooltip", "Private", image, None, None, -1)
        uim.ensure_update()
        
    def remove_toolbar(self):
        uim = self.shell.get_ui_manager()
        uim.remove_ui (self.ui_id)
        uim.remove_action_group (self.action_group)

        
    def activate_button_press(self, action):
        #print "!!! Mode activated: %s" % action
        self.activated = not self.activated
        if self.activated:
            self.do_activation()
        else:
            self.do_deactivation()
            
    def do_activation(self):
        """
        When the user requests activation of the Squeezebox mode
        
        * Mute volume but keep current setting
        """
        self.refresh_mounts()
        self.volume=self.sp.get_volume()
        self.sp.set_volume(0)
         
    def do_deactivation(self):
        """
        Deactivation...
        """
        self.sp.set_volume(self.volume)
        

    def activate (self, shell):
        """
        Called by Rhythmbox when the plugin is activated
        """
        print ">> Squeezebox activated"
        self.active=True
        self.shell = shell
        self.sp = shell.get_player()
        self.db=self.shell.props.db
        
        ##
        self.spcb = (
                     self.sp.connect("playing-changed",        self.on_playing_changed),
                     self.sp.connect("playing-song-changed",   self.on_playing_song_changed),
                     self.sp.connect("elapsed-changed",         self.on_elapsed_changed),
                     )
        
        ## Distribute the vital RB objects around
        Bus.publish("__pluging__", "rb_shell", self.shell, self.db, self.sp)
        
        self._reconnect()
        self.init_toolbar()
        
    def deactivate (self, shell):
        """
        Called by RB when the plugin is about to get deactivated
        """
        print ">> Squeezebox de-activated"
        self.remove_toolbar()
            
        for id in self.spcb:
            self.sp.disconnect(id)
        

    ## ================================================  rb signal handlers

    def on_elapsed_changed(self, pl, pos_seconds, *_):
        """
        When the use 'seeks' during track playback
        
        Since this signal is sent on every second, we need to
        implement a filter to determine when the user is actually
        seeking into the track.
        """
        if not self.activated:
            return
        if not self.playing:
            return
        if self.player is None:
            self._reconnect()
            
        if pos_seconds != self.current_pos+1:
            print ">> seeking to: %s" % pos_seconds
            try:
                self.player.seek_to(pos_seconds)
            except:
                print "! Unable to seek to :%s" % pos_seconds

        self.current_pos=pos_seconds

    def on_playing_changed(self, player, playing, *_):
        if not self.activated:
            return
        
        if self.player is None:
            self._reconnect()
            
        #print "playing: %s" % playing
        self.playing=playing
        try:
            if playing:
                self.player.play()
            else:
                self.player.pause()
        except:
            print "! Unable to play/pause"

    def on_playing_song_changed(self, player, entry, *_):
        if not self.activated:
            return
        
        if entry is None:
            return
        
        self.current_pos=0
        
        td=EntryHelper.track_details2(self.db, entry)

        print "> resolving path: %s" % td["path"]
        
        path=self.resolve_path(td["path"])
        if path is None:
            print "*** ERROR resolving path"
            return
            
        print "** resolved path: %s" % path
        
        if self.player is None:
            self._reconnect()
        try:
            self.player.playlist_play(path)
        except:
            print "! Unable to set playing path to: %s" % path


    ## ================================================ message handlers
    
    def h_tick(self, ticks_per_second, 
               second_marker, min_marker, hour_marker, day_marker,
               sec_count, min_count, hour_count, day_count):
        if (min_count % self.MOUNTS_REFRESH_INTERVAL):
            self.refresh_mounts()

    def _reconnect(self):
        try:
            self.sc = Server(hostname="127.0.0.1", port=9090)
            self.sc.connect()
            
            self.players = self.sc.get_players()
            self.player=self.players[0]
        except:
            self.player=None
        
    def refresh_mounts(self):
        self.mounts=filtered_mounts()

    def _decode(self, path):
        try:
            #p=urllib.unquote(path).decode("utf8")
            p=unicode(urllib.unquote(path))
            #p=path.decode("utf8")
        except Exception,_e:
            print "! unable to decode 'file location' for entry: %s" % path
            return None
        return p        

    def resolve_path(self, path):

        if not path.startswith("smb:"):
            return path
        
        ### clean up the "smb:" prefixes
        p=path.replace("smb:", "")
        
        #print "> path 1: %s" % p

        ### replace the unc mounting points with file:// based ones
        mount=lookup_mount(p, allmounts=self.mounts, matchstart=True, trylowercase=True)
        #print "> mount: %s" % mount
        
        if mount is not None:

            try:
                oldprefix=mount[0]
                newprefix=mount[1]
            except:
                print "!! issue with mount: ", mount
            
            if (oldprefix.endswith("/") and (not newprefix.endswith("/"))):
                newprefix += "/"
                
            p=p.replace(oldprefix, newprefix)
            
            ## as stupid as it is...
            p=p.replace(oldprefix.lower(), newprefix)

        return "file://"+p
