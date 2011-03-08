"""
    Created on 2011-03-06

    @author: jldupont
"""
import os
import gio, gtk, urllib

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
    
    ADJUST_INTERVAL=5 ##seconds
    
    def __init__ (self):
        self.spcb=None
        self.activated=False
        self.volume=0
        self.playing=False
        self.current_pos=0
        self.this_dir=os.path.dirname(__file__)
        
        ## the last captured SB state
        self.last_sb_state=None
        
        self.skip_time_adjust=False
        
        Bus.subscribe(self, "__tick__", self.h_tick)

    def init_toolbar(self):
        """
        TODO: Not able yet to force a custom image for the ToggleAction...
        """
        """        
        self.action = ('ActivateSqueezeboxMode',"gtk-network", _('SqueezeboxTools'),
                        None, _('Activate Squeezebox mode'),
                        self.activate_button_press, True)
        """
        self.action = ('ActivateSqueezeboxMode',None, _('SqueezeboxTools'),
                None, _('Activate Squeezebox mode'),
                self.activate_button_press, True)

        self.action_group = gtk.ActionGroup('SqueezeboxPluginActions')
        self.action_group.add_toggle_actions([self.action])
        action=self.action_group.get_action("ActivateSqueezeboxMode")
        action.set_gicon(self.get_icon())
        
        #print dir(action)
        #action.do_add_child(image)
        
        uim = self.shell.get_ui_manager()
        uim.insert_action_group (self.action_group, 0)
        self.ui_id = uim.add_ui_from_string(context_ui)
        #self.ui_id.insert_item("Text", "Tooltip", "Private", image, None, None, -1)
        uim.ensure_update()
        
    def get_icon(self):
        path=os.path.join(self.this_dir, "squeezecenter.gif" )
        file=gio.File(path)
        icon=gio.FileIcon(file)
        return icon
    
        
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
            
        self._maybe_reconnect()
                
        try:      self.player.pause()
        except:   pass

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
        
        self._maybe_reconnect()
        
        ## skip one time adjustment upon re-sync
        ## of SB <--> RB            
        if self.skip_time_adjust:
            self.skip_time_adjust=False
            return
        
        if pos_seconds != self.current_pos+1:
            print ">> seeking to: %s" % pos_seconds
            try:
                self.player.seek_to(pos_seconds)
            except:
                print "! Unable to seek to :%s" % pos_seconds

        self.current_pos=pos_seconds

    def on_playing_changed(self, player, playing, *_):
        """
        Easy condition to deal with since we consider RB
        to be the 'master' of the play state
        """
        if not self.activated:
            return
        
        self._maybe_reconnect()
                    
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
        """
        We also need to check if the Squeezebox was paused/stopped
        through other means during playback: we need to reflect 
        this state here back on RB.
        
        The tough part:  the 2 aren't perfectly synchronized so it is
        possible that the SB finishes playing the current track before
        RB and vice-versa.  In this case, we need to check the difference
        between the 2 'time markers' in order to assess if the SB was
        paused/stopped before the end of the current track.
        """
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
        
        self._maybe_reconnect()
        try:
            self.player.playlist_play(path)
        except:
            print "! Unable to set playing path to: %s" % path


    ## ================================================ helpers
    def on_sb_change(self, mode):
        """
        Triggered when the state of remote SqueezeBox changes
        
        Adjust time tracker based on SB
        
        SB paused:  adjust RB time marker,  pause RB
        SB play:    adjust RB time marker,  play  RB
        """
        
        ## if RB is already playing, no big deal...
        if mode=="play":
            if self.sp.get_playing():
                return
        
        self._maybe_reconnect()
        self.skip_time_adjust=True
        
        try:
            sb_tm=self.player.get_elapsed_time()
            self.sp.set_playing_time(sb_tm)
            print "* On SB Change: time marker: %s" % sb_tm
        except:
            print "! Unable to seek RB to SB's time marker"
    
        if mode=="pause":
            self.sp.pause()
        else:
            self.sp.play()
    
    def adjustBasedOnSB(self):
        """
        Adjust the state of RB based on the state
        of the remote SqueezeBox

        @return None     if there was no change since last poll        
        @return "pause"  if the remote SB is paused/stopped
        #return "play"   if the play was resumed
        """
        if self.player is None:
            self._reconnect()
        try:
            mode=self.player.get_mode().lower()
        except:
            mode=None
        
        ## no change since last time
        if mode == self.last_sb_state:
            return None
        
        self.last_sb_state=mode
        
        if mode=="pause" or mode=="stop":
            self.sp.pause()
            return "pause"

        self.sp.play()
                
        return "play"
        
            
    def _maybe_reconnect(self):
        if self.player is None:
            self._reconnect()

    def _reconnect(self):
        try:
            self.sc = Server(hostname="127.0.0.1", port=9090)
            self.sc.connect()
            
            self.players = self.sc.get_players()
            self.player=self.players[0]
        except:
            self.player=None
        
    
    ## ================================================ message handlers    
    def h_tick(self, ticks_per_second, 
               second_marker, min_marker, hour_marker, day_marker,
               sec_count, min_count, hour_count, day_count):
        """
        - Check mounts at regular interval
        - Sync with SqueezeBox state regularly
        """
        if (min_count % self.MOUNTS_REFRESH_INTERVAL):
            self.refresh_mounts()
        
        if not self.activated:
            return
        
        self._maybe_reconnect()
        
        if (sec_count % self.ADJUST_INTERVAL!=0):
            return
            
        mode=self.player.get_mode().lower()
        if mode!=self.last_sb_state:
            print "* Detected SB change state: %s" % mode
            self.on_sb_change(mode)
            self.last_sb_state=mode
        
    ## =======================================================================  MOUNT related
        
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
