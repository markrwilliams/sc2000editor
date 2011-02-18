import cityfile
import itertools

MAX_MONEY = 0x7f7f0000
WATER_TILES = range(0x10,0x1e) + range(0x20, 0x2e) +\
    range(0x30, 0x3e) + [0x3e] + range(0x40, 0x46)



class MapTile(object):
    __slots__ = ['height', 'type', 'w']
    def __init__(self, height, type, w):
        self.height = height
        self.type = type
        self.w = w

    def __repr__(self):
        return '<MapTile: height: %d, type: %d>' % (self.height,
                                                     self.type)


class City(object):
    # self.attr, self.fields[key] (self.fields[key].attr == self.attr)
    ATTR_TO_FILE = (('money'       , 'MISC'),
                    ('national_pop', 'MISC'),
                    ('days_elapsed', 'MISC'),
                    ('national_pop', 'MISC'),
                    ('year_started', 'MISC'),
                    ('cityname'    , 'CNAM'))
    
    def __init__(self, filename=None):
        self.cityfile = cityfile.CityFile()
        if filename:
            self.load(filename)
        else:
            self._set_attributes()

    def load(self, filename):
        self.filename = filename
        self.cityfile.load(filename)
        self._set_attributes()
    
    def _set_attributes(self):
        for attr, field_name in self.ATTR_TO_FILE:
            field = self.cityfile.fields.get(field_name)
            val = getattr(field, attr, None)
            setattr(self, attr, val)
        if self.cityfile.fields:
            self.map = self._setup_map()

    def _set_fields(self):
        for attr, field_name in self.ATTR_TO_FILE:
            field = self.cityfile.fields.get(field_name)
            if field:
                val = getattr(self, attr)
                setattr(field, attr, val)

        if self.cityfile.fields:
            self._save_map(self.map)

    def _setup_map(self):
        hmap = self.cityfile.fields['ALTM'].hmap
        wmap = self.cityfile.fields['ALTM'].wmap
        xmap = self.cityfile.fields['XTER'].map
        self.map = []
        
        i = 0
        rows = [iter(hmap)] * 128
        for r in itertools.izip_longest(*rows):
            row = []
            for c in r:
                row.append(MapTile(c, xmap[i], wmap[i]))
                i += 1
            self.map.append(row)

        return self.map

    def _save_map(self, map):
        hmap = self.cityfile.fields['ALTM'].hmap
        wmap = self.cityfile.fields['ALTM'].wmap
        xmap = self.cityfile.fields['XTER'].map

        i = 0
        for row in map:
            for tile in row:
                hmap[i] = tile.height
                xmap[i] = tile.type
                wmap[i] = tile.w
                i += 1

    def save(self, filename=None):
        if not filename:
            filename = self.filename
        self._set_fields()
        self.cityfile.save(filename)
    
    
