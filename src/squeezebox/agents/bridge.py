"""
    Message Bridge
    
    Performs "bridging" of messages between the shared Bus (mbus)
    living on the main-thread and the other threads hanging off
    the "mswitch"

    Why do we have to go through this trouble?
    ------------------------------------------
    
    I wanted to use "agents" interacting with RB but those couldn't
    be thread based as RB wasn't designed to work with those (at least
    that's the way I believe the situation to be).
 

    @author: jldupont
    @date: Jun 3, 2010
"""
from Queue import Queue

from squeezebox.system.mbus import Bus
from squeezebox.system.base import mswitch, custom_dispatch


class BridgeAgent(object):
    
    NAME="__bridge__"
    
    def __init__(self):
        
        self.iq=Queue()  #normal queue
        self.ipq=Queue() #high priority queue

        mswitch.subscribe(self.NAME, self.iq, self.ipq)        
        Bus.subscribe(self.NAME, "*", self.h_msg)
        
    def _dispatcher(self, mtype, *pargs):
        
        ## let's not repeart ourselves...
        if mtype=="__tick__":
            return
        
        try:
            handled=Bus.publish(self.NAME, mtype, *pargs)
            return (handled, False)
        except Exception,e:
            print "BridgeAgent._dispatcher: pargs: %s ---- exception: %s" % (str(pargs), e)
            return (False, False)
        
    def h_msg(self, mtype, *pa):    
        #if mtype!="__tick__":
        #    print "to mswitch: mtype(%s) pa:%s" % (mtype, pa)
            
        if mtype!="_sub":
            mswitch.publish(self.NAME, mtype, *pa)

        if mtype=="__tick__":
            custom_dispatch(self.NAME, 
                            self.iq, self.ipq, 
                            self._dispatcher)


_=BridgeAgent()

