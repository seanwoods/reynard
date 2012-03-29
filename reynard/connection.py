from cherrypy import Tool
from Queue import Queue

import cherrypy

class ConnectionKeeper(cherrypy.process.plugins.SimplePlugin):
    def __init__(self, bus, factory, description):
        self.bus = bus
        self.description = description
        self.factory = factory
        self.connection_queue = Queue(10)

        cherrypy.process.plugins.SimplePlugin.__init__(self, bus)

    def start(self):
        self.bus.log("Populating connection queue for %s" % self.description)

        while not self.connection_queue.full():
            self.connection_queue.put(self.factory())

    def stop(self):
        self.bus.log("Cleaning up connections for %s" % self.description)
        
        while not self.connection_queue.empty():
            self.connection_queue.get(False)
    
    def connect(self):
        return self.connection_queue.get()
    
    def disconnect(self, cxn):
        self.connection_queue.put(cxn)
    
def connect():
        cxn = cherrypy.engine.publish('connect')
        
        if len(cxn) == 0:
            cherrypy.request.db = None
        elif len(cxn) == 1:
            cherrypy.request.db = cxn[0]
        else:
            cherrypy.request.db = cxn

def disconnect():
        if hasattr(cherrypy.request, 'db'):
            cherrypy.engine.publish('disconnect', cherrypy.request.db)
            cherrypy.request.db = None

cherrypy.tools.connect = Tool('on_start_resource', connect)
cherrypy.tools.disconnect = Tool('on_end_resource', disconnect)

for channel in ('connect', 'disconnect'):
    if channel not in cherrypy.engine.listeners:
        cherrypy.engine.listeners[channel] = set()

