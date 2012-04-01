"""
Access tools for CherryPy.
"""
import cherrypy

from cherrypy import Tool

def check_auth(allowed_ip):
    ip = cherrypy.request.remote.ip

    cherrypy.log.error_log.info("Checking IP %s." % ip)
    
    if ip not in allowed_ip:
        cherrypy.log.error_log.error("IP %s denied." % ip)

        raise cherrypy.HTTPError(401)

cherrypy.tools.auth = Tool('on_start_resource', check_auth)
