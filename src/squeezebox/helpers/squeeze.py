'''
Created on 2011-03-26

@author: jldupont
'''
from squeezebox.helpers.server import Server

class SqueezeCenterControl(object):
    
    def __init__(self):
        self.player=None
        self.sc=None
        self.players=None
        self._reconnect()
    
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

    def setPlayPath(self, path):    
        try:
            self.player.playlist_play(path)
            return True
        except:
            self._reconnect()
            try:
                self.player.playlist_play(path)
                return True
            except:
                print "! Unable to set playing path to: %s" % path
                return False
    def play(self):
        self.setMode(True)
            
    def pause(self):
        self.setMode(False)
        
    def getPos(self):
        """
        Raises exception on purpose if there is a communication problem
        """
        try:
            return self.player.get_time_elapsed()
        except:
            self._reconnect()
            return self.player.get_time_elapsed()
    
    def seekTo(self, pos_seconds):
        try:
            self.player.seek_to(pos_seconds)
            return True
        except:
            self._reconnect()
            try:
                self.player.seek_to(pos_seconds)
                return True
            except:
                print "! Unable to seek"
                return False
        
    def getMode(self):
        try:
            return self.player.get_mode().lower()
        except:
            self._reconnect()
            try:
                return self.player.get_mode().lower()
            except:
                print "! Unable to get player mode"
                return None
            
    def setMode(self, playing):
        try:
            self._setMode(playing)
            return True
        except:
            self._reconnect()
            try:
                self._setMode(playing)
                return True
            except:
                print "! Unable to play/pause"
                return False
            
    def _setMode(self, playing):
        if playing:
            self.player.play()
        else:
            self.player.pause()
        
        
    