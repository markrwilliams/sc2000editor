import struct
import fields

class CityFile(object):
    FILE_HEADER=('FORM', 'SCDH')
    
    field_classes = dict(((field.name, field) for field in
                          [fields.CityName,
                           fields.Misc,
                           fields.AltitudeMap,
                           fields.TerrainMap,
                           fields.BuildingMap]))

    def __init__(self, filename=None):
        self.ordered_fields = []
        self.fields = {}
        self.filename = None
        if filename:
            self.load(filename)
    
        
    def load(self, filename):
        self.filename = filename
        
        with open(filename) as f:
            read = f.read(12)

            form, file_length, ftype = struct.unpack('>4si4s', read)
            self.length = file_length

            if (form, ftype) != self.FILE_HEADER:
                raise IOError('Not a SimCity 2000 city file!')

            while f.tell() < file_length:
                raw_header = f.read(8)
                name, length = struct.unpack('>4si', raw_header)
                data = f.read(length)
                complete_data = ''.join((raw_header, data))

                if self.field_classes.get(name):
                    cls = self.field_classes[name]
                    field_obj = cls(length, complete_data)
                    self.ordered_fields.append(field_obj)
                    self.fields[field_obj.name] = field_obj
                else:
                    self.ordered_fields.append(fields.UnknownField(length,
                                                                   complete_data))

    def save(self, filename=None):
        if not filename:
            filename = self.filename

        config = []
        length = 0

        for obj in self.ordered_fields:
            data = obj.pack_data()
            length += len(data)
            config.append(data)
            
        with open(filename, 'w') as f:
            f.write(struct.pack('>4si4s',
                                self.FILE_HEADER[0],
                                length,
                                self.FILE_HEADER[1]))
            f.write(''.join(config))
        
