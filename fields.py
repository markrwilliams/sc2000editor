import struct
import itertools

# Utility funcs

def _lchr_to_lint(loc):
    return [ord(c) for c in loc]

def _lint_to_lchr(loi):
    return [chr(i) for i in loi]

# Utility classes

class FileRecord(object):
    __slots__ = ['attr', 'start', 'end', 'format', 'infilter', 'outfilter']
    def __init__(self, **kwargs):
        self.attr = kwargs['attr']
        self.start = kwargs['start']
        self.end = kwargs['end']
        self.format = kwargs['format']
        self.infilter = kwargs.get('infilter', None)
        self.outfilter = kwargs.get('outfilter', None)
    

class Field(object):
    HEADER_FORM = '>4si'
    
    def __init__(self, length, field):
        self.field = field
        self.length = length
        self.data = self.extract_data(self.field)
        self.set_attributes(self.data)

    def set_attributes(self, data):
        for record in self.records:
            segement = data[record.start:record.end]
            unpacked = struct.unpack(record.format, ''.join(segement))

            if len(unpacked) == 1:
                unpacked, = unpacked
            else:
                unpacked = list(unpacked)

            if record.infilter:
                unpacked = record.infilter(unpacked)
                
            setattr(self, record.attr, unpacked)

    def set_fields(self, data):
        for record in self.records:
            value = getattr(self, record.attr)
            if record.outfilter:
                value = record.outfilter(value)

            if isinstance(value, list):
                packed = list(struct.pack(record.format, *value))
            else:
                packed = list(struct.pack(record.format, value))
    
            data[record.start:record.end] = packed
        return data
        
    def extract_data(self, field):
        header_len = struct.calcsize(self.HEADER_FORM)
        name, length = struct.unpack(self.HEADER_FORM,
                                          self.field[:header_len])
        if name != self.name:
            raise IOError('Field name in file does not match expected field name: %s vs. %s'
                          % (name, self.name))

        if length != self.length:
            raise IOError('Field length in file does not match expected field length: %d vs. %d'
                          % (length, self.length))

        return list(self.field[header_len:])

    def pack_data(self):
        data = ''.join(self.set_fields(self.data))
        length = len(data)
        header = struct.pack(self.HEADER_FORM, self.name, length)
        return ''.join((header, data))


class CompressedField(Field):
    def __init__(self, length, field):
        self.field = field
        self.length = length
        self.raw_data = self.extract_data(self.field)
        self.data = self.decompress(self.raw_data)
        self.set_attributes(self.data)
        
    def decompress(self, compressed):
        """Decompress a field using SimCity 2000's version of RLE.  Takes
        any iterable sequence that represents the compressed data and
        returns the decompressed data as a list."""

        ci = iter(compressed)
        decompressed = []
        
        for n in ci:
            if ord(n) > 128:
                times = ord(n) - 127
                repeated = next(ci)
                decompressed += [repeated] * times
            else:
                until = ord(n)
                decompressed += [next(ci) for _ in xrange(until)]

        return decompressed
    
    def compress(self, decompressed):
        """Compress a field using SimCity 2000's version of RLE.
        Takes a list of decompressed data and returns a string of
        compressed data."""
        
        compressed = []
        uniq = []

        def get_reset_uniq():
            if uniq:
                compressed.extend([chr(len(uniq))] + uniq)
                del uniq[:]

        for value, run in itertools.groupby(decompressed):
            runlen = sum(1 for _ in run)
            if runlen > 1:
                get_reset_uniq()

                while runlen > 128:
                    runlen -= 128
                    compressed += [chr(255), value]

                compressed += [chr(127 + runlen), value]
            else:
                if len(uniq) == 127: # make sure we don't overflow
                    get_reset_uniq()
                uniq.append(value)

        # catch any remainder
        get_reset_uniq()
        return ''.join(compressed)

    def pack_data(self):
        data = self.compress(self.set_fields(self.data))
        length = len(data)
        header = struct.pack(self.HEADER_FORM, self.name, length)
        return ''.join((header, data))

    
# Actual fields
class UnknownField(object):
    def __init__(self, length, field):
        self.raw_data = field
        self.length = field

    def pack_data(self):
        return self.raw_data
    

class CityName(Field):
    name = 'CNAM'
    verbose_name = 'City Name'

    records = (FileRecord(attr='cname_len',
                          start=0,
                          end=1,
                          format='>c'),
               FileRecord(attr='cityname', 
                          start=1, 
                          end=32, 
                          format='>31s',
                          infilter=lambda s: s.partition('\x00')[0]))
    
    def __init__(self, field, length):
        super(CityName, self).__init__(field, length)
        self.cname_length = len(self.cityname)

    def pack_data(self):
        return super(CityName, self).pack_data()
        
        
class Misc(CompressedField):
    name = 'MISC'
    verbose_name = 'Miscellaneous'
    records = (FileRecord(attr='year_started',
                          start=12,
                          end=16,
                          format='>i'),
               FileRecord(attr='days_elapsed',
                          start=16,
                          end=20,
                          format='>i'),
               FileRecord(attr='money',
                          start=20,
                          end=24,
                          format='>i'),
               FileRecord(attr='national_pop',
                          start=80,
                          end=84,
                          format='>i'))
    
class AltitudeMap(Field):
    name = 'ALTM'
    verbose_name = 'Altitude Map'

    records = (FileRecord(attr='map',
                         start=0,
                         end=32768,
                         format='>16384h'),)
    
    def __init__(self, length, field):
        super(AltitudeMap, self).__init__(length, field)
        self.get_altitude_maps(self.map)

    def get_altitude_maps(self, map):
        self.hmap = []
        self._smap0 = []
        self.wmap = []
        self._smap1 = []
        
        for tile in map:
            # lower 4 bits are tile height
            self.hmap.append(tile & 0x0F)
            # bits 5-6 are unknown special attributes
            self._smap0.append((tile & 0x3f) >> 3)
            # bit 7 marked if there's water            
            self.wmap.append((tile & 0x07) >> 6)
            # bits 8-16 are unknown special attributes        
            self._smap1.append(tile & ~0x7f)

    def set_altitude_maps(self, hmap, smap0, wmap, smap1):
        self.map = [c | (smap0[i] << 3) | (wmap[i] << 6) | smap1[i]
                    for i, c in enumerate(hmap)]

    def pack_data(self):
        self.set_altitude_maps(self.hmap,
                               self._smap0,
                               self.wmap,
                               self._smap1)
        return super(AltitudeMap, self).pack_data()


class TerrainMap(CompressedField):
    name = 'XTER'
    verbose_name = 'Terrain Map'

    records = (FileRecord(attr='map',
                          start=0,
                          end=16384,
                          format='>16384c',
                          infilter=_lchr_to_lint,
                          outfilter=_lint_to_lchr),)


class BuildingMap(CompressedField):
    name = 'XBLD'
    verbose_name = 'Building Map'
    
    records = (FileRecord(attr='map',
                          start=0,
                          end=16384,
                          format='>16384c',
                          infilter=_lchr_to_lint,
                          outfilter=_lint_to_lchr),)
