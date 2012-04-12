import cStringIO
import time

import zmq

from pprint import pprint

SEGMENT_DELIM = '\x1D'
RECORD_DELIM = '\x1E'
FIELD_DELIM = '\x1F'

def encode_records(rec):
    "Transform a sequence of sequences into a packed list of records."

    return RECORD_DELIM.join([FIELD_DELIM.join([str(j) for j in i])\
        for i in rec])

def internal_to_external(string):
    return string.replace(SEGMENT_DELIM, '|')\
                 .replace(RECORD_DELIM, '^')\
                 .replace(FIELD_DELIM, ',')

class Connection(object):
    
    topology = "tcp://127.0.0.1:1841"
    connected = False

    def __init__(self, ctx, topology=None):
        if topology is not None:
            self.ctx = ctx
            self.connect(topology)
    
    def connect(self, topology):
        #self.ctx = zmq.Context(1)
        self.socket = self.ctx.socket(zmq.REQ)
        self.socket.connect(topology)

        self.connected = True
    
    def disconnect(self):
        # - close socket?  TODO

        self.connected = False
    
    def shutdown(self):
        self.socket.send("QUIT")

    def send_msg(self, msg):
        msg = msg.encode("utf-8")
        self.socket.send(msg)

        return self.socket.recv_multipart()

class Message(object):
    def __init__(self):
        self.buf = cStringIO.StringIO()
        self.segno = 0
        self.recno = 0
        self.fldno = 0

    def __str__(self):
        return self.buf.getvalue()
    
    def new_segment(self):
        self.buf.write(SEGMENT_DELIM)
        self.segno += 1
        self.recno = 0
        self.fldno = 0

    def new_record(self):
        self.buf.write(RECORD_DELIM)
        self.recno += 1
        self.fldno = 0

    def new_field(self):
        self.buf.write(FIELD_DELIM)
        self.fldno += 1
    
    def add_segment(self, segment):
        if self.segno > 0:
            self.new_segment()

        if isinstance(segment, basestring):
            self.buf.write(segment)
        elif isinstance(segment, int):
            self.buf.write(str(segment))
        else:
            for record in segment:
                self.add_record(record)
            #self.buf.write(RECORD_DELIM.join([str(i) for i in segment]))
        
        self.segno += 1

    def add_record(self, record):
        if self.recno > 0:
            self.new_record()
        
        if isinstance(record, basestring):
            self.buf.write(record)
        elif isinstance(record, int):
            self.buf.write(str(record))
        else:
            self.buf.write(FIELD_DELIM.join([str(i) for i in record]))

        self.recno += 1

def set_list(dict_, key, val):
    if key in dict_:
        dict_[key].append(val)
    else:
        dict_[key] = [val]

def set_dict_list(dict_, key, subkey, val):
    if key in dict_:
        set_list(dict_[key], subkey, val)
    else:
        dict_[key] = {subkey: [val]}


def obj_pack_dict(id_, schema, data):
    obj_packed = [id_]
    obj_packed.extend([data.get(i, '') for i in schema if i is not 'id'])
    
    return obj_packed

class Database(object):
    def __init__(self, ctx, topology=None, logger=None):
        if topology is not None:
            self.cxn = Connection(ctx, topology)

        self.cache = {}
        self.logger = logger
        self.schemas = {}
        self.state = None
        self.msg = Message()
    
    def set(self, class_, *args, **kwargs):
        # args = either (id, value) or just value.  value is dict-like
        if self.state != 'setobj':
            self.flush()
            self.state = 'setobj'
            
        if len(args) == 1:
            data = args[0]
        else:
            id_, data = args[0:2]
            data['id'] = id_
        
        if class_ in self.schemas:
            for i in data:
                if i not in self.schemas[class_]:
                    self.schemas[class_].append(i)
        else:
            sch = ['id']
            sch.extend([i for i in data if i != 'id'])
            self.schemas[class_] = sch
        
        set_list(self.cache, class_, data)

        if 'multipart' not in kwargs:
            return self.execute()
    
    def delete(self, class_, *args, **kwargs):
        # args = list of object IDs for class
        if self.state != 'delobj':
            self.flush()
            self.state = 'delobj'

        for id_ in args:
            set_list(self.cache, class_, id_)

        if 'multipart' not in kwargs:
            return self.execute()
    
    def get(self, class_, *args, **kwargs):
        # args = list of object IDs for class
        if self.state != 'getobj':
            self.flush()
            self.state = 'getobj'

        for id_ in args:
            set_list(self.cache, class_, id_)
        
        if 'multipart' not in kwargs:
            # TODO what if len(args) > 1?
            fields, data = self.execute()
            
            return dict(zip(fields, data))
    
    def schema(self, *args, **kwargs):
        # args = list of classes
        if self.state != 'schema':
            self.flush()
            self.state = 'schema'
        
        self.cache = []

        for class_ in args:
            self.cache.append(class_)

        if 'multipart' not in kwargs:
            result = [[j.split("^") for j in i] for i in self.execute()]
            
            schemas = {}

            for definitions in result:
                class_ = definitions[0][0]
                fields = definitions[1:]
                
                schemas[class_] = fields

            if len(result) > 1:
                return dict([(i[0], i[1:]) for i in result])
            else:
                return result[0][1:]
    
    def view(self, view_name, arguments=None, index_by=None, slice_=None):
        if self.state != 'view':
            self.flush()
            self.state = 'view'
        
        arg_keys = []
        arg_values = []

        if arguments:
            arg_keys = [i for i in arguments]
            arg_values = [arguments.get(i) for i in arg_keys]
            
            # TODO better escaping, should only need to replace delimeters
            arg_keys = ' '.join(arg_keys)
            arg_values = ' '.join(
                ['"%s"' % i.replace('"','""') for i in arg_values]
            )
        
        if slice_:
            self.cache = [(view_name, slice_), arg_keys, arg_values]
        else:
            self.cache = [view_name, arg_keys, arg_values]

        response = self.execute()

        length, fields, data = (response[0], response[1], response[2:])
        
        length = int(length[0])

        self.objects_in_result = len(data)
        self.objects_in_db = length

        if index_by:
            output = {}

            for dat in data:
                obj = dict(zip(fields, dat))
                set_list(output, obj.get(index_by), obj)
                
        else:
            output = [dict(zip(fields, dat)) for dat in data]

        return (fields, output)
    
    # TODO much duplication between view and find

    def find(self, class_, arguments=None, index_by=None):
        if self.state != 'find':
            self.flush()
            self.state = 'find'
        
        arg_keys = []
        arg_values = []

        if arguments:
            arg_keys = [i for i in arguments]
            arg_values = [arguments.get(i) for i in arg_keys]

            arg_keys = ' '.join(arg_keys)
            arg_values = ' '.join(
                ['"%s"' % i.replace('"','""') for i in arg_values]
            )
        
        self.cache = [class_, arg_keys, arg_values]
        
        response = self.execute()

        fields, data = (response[0], response[1:])

        if index_by:
            output = {}

            for dat in data:
                obj = dict(zip(fields, dat))
                set_list(output, obj.get(index_by), obj)
                
        else:
            output = [dict(zip(fields, dat)) for dat in data]

        return (fields, output)

    def list(self, *args, **kwargs):
        if self.state != 'listobj':
            self.flush()
            self.state = 'listobj'
        
        if 'slice_' in kwargs:
            # TODO right now one slice -> many args
            self.cache = [(i, kwargs['slice_']) for i in args]
        else:
            self.cache = args
        
        if 'multipart' not in kwargs:
            data = self.execute()
            output = {}
            
            if len(args) == 1:
                data = [data]
            
            for datum in data:
                class_ = datum[0][0]
                objects_in_db = int(datum[0][1])
                schema = datum[1]
                
                if objects_in_db < 0:
                    self.objects_in_db = None
                else:
                    self.objects_in_db = objects_in_db
                
                self.objects_in_result = 0

                for row in datum[2:]:
                    dif = len(schema) - len(row)

                    if dif > 0:
                        row.extend(["" for i in range(dif)])
                    
                    obj = dict(zip(schema, row))

                    if 'index_by' in kwargs:
                        set_dict_list(output,
                                      class_,
                                      obj.get(kwargs['index_by']),
                                      obj)
                    else:
                        set_list(output, class_, obj)
                        self.objects_in_result += 1
            
            if len(args) == 1:
                return output[args[0]]
            else:
                return output

    def list_objects(self):
        if self.state != 'listobjs':
            self.flush()
            self.state = 'listobjs'
        
        self.cache = True
        objects = self.execute()

        return dict([i[0].split('^') for i in objects])

    def list_views(self):
        if self.state != 'listviews':
            self.flush()
            self.state = 'listviews'

        self.cache = True
        objects = self.execute()
        
        if objects == [['OK']]:  # TODO ugly
            return []
        else:
            return objects
    
    def pointers(self, class_):
        if self.state != 'pointers':
            self.flush()
            self.state = 'pointers'

        self.cache = class_
        
        data = {}
        
        for record in self.execute():
            if len(record) == 1:
                current_class = record[0]
                data[current_class] = {}
            else:
                data[current_class][record[0]] = record[1]

        return data

    # -

    def flush(self):
        if self.cache == {}:
            return None

        flush_fn = getattr(self, 'flush_%s' % self.state, None)
        
        if not flush_fn:
            raise Exception('Illegal object state: %s' % self.state)
        
        out = flush_fn()
        
        self.cache = {}
        self.schemas = {}
        self.state = None

        return out

    def flush_setobj(self):
        classes = [class_ for class_ in self.schemas]
        
        self.msg.add_segment(["SETOBJ", len(classes) + 1])
        self.msg.add_segment(classes)

        for class_ in classes:
            fields = self.schemas[class_]
            
            self.msg.new_segment()
            self.msg.add_record(fields)

            for record in self.cache[class_]:
                self.msg.add_record([str(record.get(i, '')) for i in fields])
        
        return self.msg
    
    def flush_getobj(self):
        classes = [class_ for class_ in self.cache]

        self.msg.add_segment(["GETOBJ", len(classes) + 1])
        self.msg.add_segment(classes)

        for class_ in classes:
            self.msg.new_segment()
            
            for id_ in self.cache[class_]:
                self.msg.add_record(str(id_))
        
        return self.msg

    def flush_delobj(self):
        classes = [class_ for class_ in self.cache]

        self.msg.add_segment(["DELOBJ", len(classes) + 1])
        self.msg.add_segment(classes)

        for class_ in classes:
            self.msg.new_segment()
            self.msg.add_record(self.cache[class_])

        return self.msg
    
    def flush_listobj(self):
        self.msg.add_segment(["LISTOBJ", len(self.cache) + 1])
        self.msg.add_segment(self.cache)

        return self.msg
    
    def flush_view(self):
        self.msg.add_segment(["VIEW", 2])
        self.msg.add_segment(self.cache)

        return self.msg

    def flush_find(self):
        self.msg.add_segment(["FINDOBJ", 2])
        self.msg.add_segment(self.cache)

        return self.msg

    def flush_listobjs(self):
        self.msg.add_segment(["LISTOBJS", 1])
        # TODO delete? self.msg.add_segment([1,2,3])
        
        return self.msg
    
    def flush_listviews(self):
        self.msg.add_segment(["LISTVIEWS", 1])
        # TODO delete? self.msg.add_segment([1,2,3])
        
        return self.msg
    
    def flush_schema(self):
        self.msg.add_segment(["ENHSCHEMA", 1])
        self.msg.add_segment(self.cache)

        return self.msg

    def flush_pointers(self):
        self.msg.add_segment(["POINTERS", 1])
        self.msg.add_segment(self.cache)

        return self.msg

    # -

    def execute(self):
        self.flush()
        
        msg = str(self.msg)
        
        self.msg = Message()
        
        # The server gives us a ZeroMQ multipart message.  Each part
        # is a message record.  Segments are separated by a message part
        # whose only data is the segment delimeter character.

        message = []
        rec_cur = []
        
        start_time = time.time()

        records = self.cxn.send_msg(msg)

        self.elapsed_time = time.time() - start_time
        self.elapsed_time_ms = int(round(self.elapsed_time, 3) * 1000)
        
        if self.logger:
            operation = msg[0:msg.find(RECORD_DELIM)]

            self.logger.info("Database response for %-20s %s ms" %
                (operation, self.elapsed_time_ms))

        for rec in records:
            if rec == SEGMENT_DELIM:
                # Flush the buffer and start a new segment.
                message.append(rec_cur)
                rec_cur = []
            else:
                rec_cur.append(rec.split(FIELD_DELIM))

        message.append(rec_cur)
        
        if len(message) > 1:
            return message
        else:
            return message[0]

if __name__ == '__main__':
    import time

    t = time.time()
    
    db = Database("tcp://192.168.56.2:1841")
    db.set("Pets", 1, {"type": "Golden", "name": "Troy"})
    db.set("Pets", 2, {"type": "Mutt", "name": "Pepper"})
    db.set("Pets", 3, {"name": "Rusty", "fictitious": 1})
    db.set("Pets", {"name": "Gabe", "breed": "fish"})

    db.set("Cars", {"year": 1995, "make": "Chevrolet", "model": "Lumina"})
    db.set("Cars", {"year": 1990, "make": "Oldsmobile", "model": "Woody"})
    
    db.get("Cars", 1)
    db.get("Pets", 3)

    db.delete("Pets", 5)
    
    # print repr(str(db.msg))

    from pprint import pprint
    
    print db.execute()
    
    db.msg.add_segment(["QUERY", 5])
    db.msg.add_segment("TestPets1")
    db.msg.add_segment("Pets")
    db.msg.add_segment("name type")
    db.msg.add_segment("")
    db.msg.add_segment("name")

    print db.execute()

    print time.time() - t

