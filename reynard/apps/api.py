import cherrypy

from reynard.web import emit_json

class ReynardAPI(object):
    @emit_json
    def objects(self, class_=None, ident=None):
        db = cherrypy.request.db
        
        if cherrypy.request.method == 'GET':
            if class_ is None:
                return db.list_objects()
            elif ident is None:
                return db.list(class_)
            else:
                return db.get(class_, ident)
    
    @emit_json
    def views(self, view):
        db = cherrypy.request.db

        if cherrypy.request.method == 'GET':
            return db.view(view)

    @emit_json
    def schemas(self, class_):
        db = cherrypy.request.db

        if cherrypy.request.method == 'GET':
            return db.schema(class_)
    
    @emit_json
    def pointers(self, class_):
        db = cherrypy.request.db

        if cherrypy.request.method == 'GET':
            return db.pointers(class_)
