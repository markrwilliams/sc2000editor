import Tkinter
import fields
import struct
import sys
root = Tkinter.Tk(  )
w = Tkinter.Canvas(root, width=512, height=512)
city = sys.argv[1]

FILE_HEADER=('FORM', 'SCDH')

field_classes = dict(((field.name, field) for field in
                      [fields.CityName,
                       fields.Misc,
                       fields.AltitudeMap,
                       fields.TerrainMap]))

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

    
altm = field_objects['ALTM']
xter = field_objects['XTER']
print xter == ordered_fields[-1]
scale = 255 / 15

def watch_tile(t):
    altm += 1
    
# if 0 < t < 128:


def raise_terrain(e):
    c = e.widget
    x = int(c.canvasx(e.x))
    y = int(c.canvasy(e.y))

    id = c.find_closest(x, y)[0]
    altm.hmap[id - 1] += 1
    xter.map[id] = 2
    xter.map[id - 2] = 4
    c.itemconfig(id, fill=gen_hexcolor(altm.hmap[id - 1]))


    
    
def write_out():
    new_config = [struct.pack('>4si4s', FILE_HEADER[0], file_length, FILE_HEADER[1])]
    
    for obj in ordered_fields:
        new_config.append(obj.pack_data())
        
    new_config += rest

    with open(city, 'w') as f:
        f.write(''.join(new_config))
        
    sys.exit(0)

def gen_hexcolor(c):
    c *= scale
    return '#%02x%02x%02x' % (c, c, c)

i = 0
for y in xrange(0, 512, 4):
    for x in xrange(0, 512, 4):
        c = altm.hmap[i]
        w.create_rectangle(x + 4, y, x + 8, y + 4,
                           fill=gen_hexcolor(c),
                           outline='',
                           activefill='red')
        i += 1
w.bind('<Button-1>', raise_terrain)
w.pack()


root.protocol("WM_DELETE_WINDOW", write_out)

root.mainloop()

