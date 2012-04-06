"""
Database Administration App
"""
import cProfile  # TODO take out
import re

import cherrypy

from reynard.web import emit_json, emit_template, filter_internal

from pprint import pprint  # TODO take out

def default_page(page=None):
    if page is None:
        page = {}
    
    page['classes'] = cherrypy.request.db.list_objects()
    
    page['views'] = cherrypy.request.db.list_views()
    page['view'] = ''

    page['current_class'] = None
    
    return page

def mk_crit(crit_in):
    for c in sorted(crit_in):
        for f in ('andor', 'field', 'op', 'val'):
            if f == 'val':
                yield '"%s"' % crit_in[c][f].replace('"', '""')
            elif not (f == 'andor' and c == 0):
                yield crit_in[c][f]

def mk_args(args_in):
    for c in sorted(args_in):
        yield args_in[c]['name'] + " " + args_in[c]['desc']

def mk_sort(sort_in):
    for c in sorted(sort_in):
        yield sort_in[c]['field']

def hyphenated_to_camel(string):
    out = []
    up_next = False

    for idx, char in enumerate(string):

        if idx == 0:
            out.append(char.upper())
        elif char == '-':
            up_next = True
        elif up_next:
            out.append(char.upper())
            up_next = False
        else:
            out.append(char)

    return ''.join(out)

def camel_to_hyphenated(string):
    out = []

    for idx, char in enumerate(string):
        if idx == 0:
            out.append(char.lower())
        elif char.isupper():
            out.append("-" + char.lower())
        else:
            out.append(char)

    return ''.join(out)

class AdminApp(object):
    @emit_template("index.html")
    def index(self):
        db = cherrypy.request.db
        
        page = default_page()
        page['current_class'] = 'roles'
        
        return page

    @emit_template(useattr="template")
    def objects(self, class_=None, ident=None, **kwargs):
        db = cherrypy.request.db
        page = default_page()
        
        if class_ is None:
            page['template'] = 'objects.html'
            page['objects'] = db.list_objects()

            return page

        elif ident is None:
            if cherrypy.request.method == 'POST':
                url = cherrypy.url('/objects/%s' % class_)
                
                if kwargs.get('action') == 'del':
                    if isinstance(kwargs['select'], basestring):
                        records_to_delete = [kwargs['select']]
                    else:
                        records_to_delete = kwargs['select']
                    
                    cherrypy.request.db.delete(class_, *records_to_delete)

                raise cherrypy.HTTPRedirect(url)
            
            page['template'] = 'object-list.html'
            page['js'] = ('list-objects.js',)
            
            page['current_class'] = class_

            page['mode'] = 'object'
            page['class_'] = class_
            
            page['schema'] = db.schema(class_)
            
            page['pointers'] = db.pointers(class_)
            
            if 'slice' in kwargs:
                if re.match(r'^(\d+):(\d+)$', kwargs['slice']):
                    page['slice'] = kwargs['slice']
                else:
                    page['slice'] = '1:20'
            else:
                page['slice'] = '1:20'

            page['data'] = db.list(class_, slice_=page['slice'])
            page['objects_in_db'] = db.objects_in_db
            page['objects_in_result'] = db.objects_in_result
            
            return page

        else:
            if cherrypy.request.method == 'POST':
                # Save new object data.
                
                data = filter_internal(kwargs)
                
                if ident != 'new':
                    data['id'] = ident
                
                for key, value in data.items():
                    if not isinstance(value, basestring):
                        data[key] = ' '.join([v for v in value if v != ''])

                db.set(class_, data)

                # Validate entries against schema so that we don't have
                # any rogue data injection (mass assignment vulnerability).

                # TODO
                
                # Generate URL based on flavor of save button pressed..

                if '__save_ret' in kwargs:
                    url = cherrypy.url('/objects/%s' % class_)
                elif '__save_new' in kwargs:
                    url = cherrypy.url('/objects/%s/new' % class_)
                else:
                    url = cherrypy.url('/objects/%s/%s' % (class_, ident))

                raise cherrypy.HTTPRedirect(url)

            page['template'] = 'object-editor.html'

            page['current_class'] = None
            
            page['mode'] = 'object'
            page['class_'] = class_
            page['pointers'] = db.pointers(class_)

            if ident.lower() == 'new':
                page['identifier'] = 'new'
                page['schema'] = db.schema(class_)
                page['data'] = {}
            else:
                page['identifier'] = ident
                page['schema'] = db.schema(class_)
                page['data'] = db.get(class_, ident)
            
            return page

    @emit_template("schema-editor.tpl")
    def schemas(self, class_, **kwargs):
        db = cherrypy.request.db
        #class_ = hyphenated_to_camel(class_)
        
        if cherrypy.request.method == 'POST':
            order = {}

            if isinstance(kwargs['order'], basestring):
                temp_order = [kwargs['order'].split('.')]
            else:
                temp_order = [i.split('.') for i in kwargs['order']]
            
            for k, v in temp_order:
                if v == '':
                    order[k] = k
                else:
                    order[int(v)] = k
            
            fields = ('caption', 'datatype', 'extra')
            
            for offset in sorted(order):  # loop through data fields
                if re.match(r'^[0-9]+', str(offset)):
                    rec = {'id': str(offset)}
                else:
                    rec = {}
                
                rec['object'] = class_
                rec['short_name'] = order[offset]

                for field in fields:
                    rec[field] = kwargs["%s.%s" % (order[offset], field)]
                
                if rec['datatype'] not in ('P', 'PM', 'SL'):
                    del(rec['extra'])
                
                db.set('sysSchema', rec, multipart=True)
            
            db.execute()

            raise cherrypy.HTTPRedirect(cherrypy.url('/schemas/%s' % class_))

        page = default_page()
        page['class_'] = class_
        page['schema'] = db.schema(class_)

        return page
    
    @emit_template(useattr="template")
    def views(self, ident=None, **kwargs):
        
        db = cherrypy.request.db
        #ident = hyphenated_to_camel(ident)
        
        if cherrypy.request.method == 'POST':
            multi_fields = {}

            for key, value in kwargs.items():
                if '-' in key:
                    field, slot, num = key.split('-')

                    num = int(num)
                    
                    if field not in multi_fields:
                        multi_fields[field] = {}

                    if num not in multi_fields[field]:
                        multi_fields[field][num] = {}

                    multi_fields[field][num][slot] = value
            
            view = {
                'fields': ' '.join(kwargs['choices']),
                'name': kwargs['mnemonic'],
                'description': kwargs['description'],
                'class': 'pets',
                'crit': ' '.join(mk_crit(multi_fields['crit'])),
                'args': '^'.join(mk_args(multi_fields['arg'])),
                'sort': ' '.join(mk_sort(multi_fields['sort']))
            }

            db.set('sysView', view)

            raise cherrypy.HTTPRedirect("/views")
        
        page = default_page()
        
        if ident is None:
            pass
        elif ident == 'new':
            page['template'] = 'view.html'
            page['js'] = ['view.js']

            page['class_'] = 'pets'
            page['ident'] = 10
            
            page['ops'] = (
                ('eq', 'Equals'),
                ('neq', 'Does not equal'),
                ('gt', 'Greater than'),
                ('lt', 'Less than'),
                ('gte', 'Greater than or equal to'),
                ('lte', 'Less than or equal to'),
                ('sw', 'Starts with'),
                ('ew', 'Ends with'),
                ('in', 'In'),
                ('lin', 'Not In')
            )

            page['schema'] = (('id','ID'),('name','Name'),('breed','Breed'))

            page['view'] = {
                'args': (('foo','Foo'),('bar','Bar')),
                'criteria': [
                    ('AND', ('name', 'sw', 'Wo'))
                ],
                'description': 'A Test View',
                'fields': ['name', 'breed'],
                'mnemonic': 'TestView',
                'sort': ["+breed", "-name"]
            }

        else:
            page['template'] = 'object-list.html'
            page['js'] = ('list-objects.js',)
            
            _, view = db.find("SysView", dict(name=ident))

            if 'slice' in kwargs:
                if re.match(r'^(\d+):(\d+)$', kwargs['slice']):
                    page['slice'] = kwargs['slice']
                else:
                    page['slice'] = '1:20'
            else:
                page['slice'] = '1:20'
            
            if len(view) > 0:
                page['current_view'] = view[0]['name']
                page['schema'], page['data'] = \
                    db.view(view[0]['name'], slice_=page['slice'])
                page['objects_in_db'] = db.objects_in_db
                page['objects_in_result'] = db.objects_in_result
            else:
                raise cherrypy.HTTPError(404)

            page['current_class'] = view[0]['class']

            page['mode'] = 'view'
            page['class_'] = view[0]['class']
            
            for idx, field in enumerate(page['schema']):
                sch = [None, None, field, field, "text", None]
                page['schema'][idx] = sch

        return page
