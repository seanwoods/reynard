"""
Access tools for CherryPy.
"""
import cherrypy

from cherrypy import Tool

def check_auth(allowed_ip):
    if cherrypy.request.remote.ip not in allowed_ip:
        raise cherrypy.HTTPError(401)

cherrypy.tools.auth = Tool('on_start_resource', check_auth)
