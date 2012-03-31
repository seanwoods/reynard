"""
A set of utilities that sets up sane defaults for databases

"""

import logging
import os.path
import sys

from functools import wraps
from logging.handlers import TimedRotatingFileHandler

import cherrypy
import zmq

from mako.lookup import TemplateLookup
from mako.exceptions import html_error_template

import reynard.access

from connection import ConnectionKeeper
from db import Database

from pprint import pprint # TODO take this out

try:
    import json
except ImportError:
    import simplejson as json

def filter_internal(values):
    """Remove keys that start with '__' from dictionary `values`."""

    return dict([(k, v) for k, v in values.items() if k[0:2] != '__'])

def make_connection():
    conf = cherrypy.config
    ctx = zmq.Context(1)

    if 'database' in conf and conf['database'].get('perflog'):
        logger = cherrypy.log.error_log
    else:
        logger = None
    
    if 'database' in conf and 'topology' in conf['database']:
        return Database(ctx, conf['database']['topology'], logger)
    else:
        return Database(ctx, logger=logger)

ConnectionKeeper(cherrypy.engine,
                 make_connection,
                 "Reynard DB Server").subscribe()

def add_template_to_config(basefile, config={}, tpldir='templates'):
    basedir = os.path.dirname(os.path.abspath(basefile))

    config['templates'] = os.path.join(basedir, tpldir)
    
    return config

def mount(app, mount_point="/", config={}, auto_template=True):

    if auto_template and 'templates' not in config:
        filename = sys.modules[app.__module__].__file__
        config = add_template_to_config(filename, config)
    
    config = {mount_point: config}

    cherrypy.tree.mount(app, mount_point, config)

def emit_template(template_name=None, autoexpose=True, useattr=None):
    def decorator(f):
        if autoexpose:
            f.exposed = True
        
        # Kludge to get around some odd scope issue.
        f.template_name = template_name

        @wraps(f)
        def decorated(*args, **kwargs):
            path = cherrypy.request.app.script_name + "/"
            tpl_dir = cherrypy.request.app.config[path].get('templates')
            template_name = f.template_name
            
            if tpl_dir is None:
                tpl_dir = args[0].templates
            
            try:
                values = f(*args, **kwargs)
                
                if useattr is not None:
                    template_name = values[useattr]
                
                lookup = TemplateLookup([tpl_dir])
                template = lookup.get_template(template_name)
                
                if not values.get('js'):
                    values['js'] = []

                if not values.get('css'):
                    values['css'] = []

                values['url'] = cherrypy.url

                return template.render(**values)
            
            except cherrypy.HTTPRedirect as e:
                raise e
            except cherrypy.HTTPError as e:
                raise e
            except cherrypy.NotFound as e:
                raise e
            except:
                return html_error_template().render()

        return decorated

    return decorator

def emit_json(f):
    f.exposed = True

    @wraps(f)
    def decorated(*args, **kwargs):
        cherrypy.response.headers['Content-Type'] = 'application/json'

        return json.dumps(f(*args, **kwargs))

    return decorated

def setup_rotating_logs(when='D', interval=1):
    if 'access_file' in cherrypy.config:
        handler = TimedRotatingFileHandler(cherrypy.config['access_file'],
                                           when,
                                           interval)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(cherrypy._cplogging.logfmt)

        cherrypy.log.access_log.addHandler(handler)

    if 'error_file' in cherrypy.config:
        handler = TimedRotatingFileHandler(cherrypy.config['error_file'],
                                           when,
                                           interval)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(cherrypy._cplogging.logfmt)

        cherrypy.log.error_log.addHandler(handler)

