import fields
import fileutils
import struct
import sys

city = sys.argv[1]

FILE_HEADER=('FORM', 'SCDH')

field_classes = dict(((field.name, field) for field in
              [fields.CityName,
               fields.Misc])
               # fields.AltitudeMap,
               # fields.TerrainMap,
               # fields.BuildingMap])
                     )


with open(city) as f:
    read = f.read(12)
    
    form, file_length, ftype = struct.unpack('>4si4s', read)
    
    if (form, ftype) != FILE_HEADER:
        raise IOError('Not an SC2 file')
    
    ordered_fields = []
    field_objects = {}
    rest = []


    while f.tell() < file_length:
        raw_header = f.read(8)
        name, length = struct.unpack('>4si', raw_header)
        data = f.read(length)
        complete_data = ''.join((raw_header, data))

        if field_classes.get(name):
            cls = field_classes[name]
            field_obj = cls(length, complete_data)
            ordered_fields.append(field_obj)
            field_objects[field_obj.name] = field_obj
        else:
            rest.append(complete_data)
            break
    rest.append(f.read())

d = field_objects['MISC'].data

field_objects['MISC'].money = 1234

new_config = []
change = 0

for obj in ordered_fields:
    data = obj.pack_data()
    change += (len(data) - len(obj.field))
    print change
    new_config.append(data)
    
new_config += rest
    
with open(city, 'w') as f:
    f.write(struct.pack('>4si4s', FILE_HEADER[0], file_length - change, FILE_HEADER[1]))
    f.write(''.join(new_config))
        
