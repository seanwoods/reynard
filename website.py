import cherrypy

from reynard.apps import ReynardAPI
from reynard.apps import AdminApp
from reynard.web import mount

root = AdminApp()
root.api = ReynardAPI()

mount(root, "/")
