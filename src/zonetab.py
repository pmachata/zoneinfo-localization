#!/usr/bin/env python

# This file is taken from tzdiff.
#
# tzdiff is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# tzdiff is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with tzdiff.  If not, see <http://www.gnu.org/licenses/>.

import re
import os

class ParseError (ValueError):
    pass

class Coordinate:
    def __init__ (self, sign, degrees, minutes, seconds, deg_width = 2):
        assert sign in [-1, 1]
        assert degrees >= 0
        assert minutes >= 0
        assert seconds >= 0

        self.sig = sign
        self.deg = degrees
        self.min = minutes
        self.sec = seconds
        self._dw = deg_width

    def __str__ (self):
        return (("+" if self.sig > 0 else "-")
                + str (abs (self.deg)).zfill (self._dw)
                + str (self.min).zfill (2)
                + (str (self.sec).zfill (2) if self.sec != 0 else ""))

    def __repr__ (self):
        return "Coordinate(%s, %s, %s, %s, %s)" \
            % (repr (self.sig), repr (self.deg), repr (self.min),
               repr (self.sec), repr (self._dw))

class Coordinates:
    def __init__ (self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def __str__ (self):
        return str (self.latitude) + str (self.longitude)

    def __repr__ (self):
        return "Coordinates(%s, %s)" % (repr (self.latitude),
                                        repr (self.longitude))

class TZID:
    comp_pat = re.compile ("^[a-zA-Z_.0-9+-]+$")

    def __init__ (self, zonename):
        self.components = tuple (zonename.split ("/"))
        for c in self.components:
            if TZID.comp_pat.match (c) is None:
                raise ParseError ("invalid tzid component " + c)
        self.zonename = zonename

    def __str__ (self):
        return self.zonename

    def __hash__ (self):
        return hash(self.zonename)

    def __cmp__ (self, other):
        return cmp (self.zonename, other.zonename)

    def name (self):
        return self.zonename

    def __repr__ (self):
        return "TZID(%s)" % repr (self.zonename)

class Zone:
    def __init__ (self, country, coordinates, tzid, comments):
        self.country = country
        self.coordinates = coordinates
        self.tzid = tzid
        self.comments = comments

    def __str__ (self):
        fmt = [str (self.country if self.country is not None else "??"),
               str (self.coordinates if self.coordinates is not None else ""),
               str (self.tzid)]
        if self.comments != "":
            fmt.append (self.comments)
        return "\t".join (fmt)

    def __repr__ (self):
        return "Zone(%s, %s, %s, %s)" \
            % (repr (self.country), repr (self.coordinates),
               repr (self.tzid), repr (self.comments))

    def _key (self):
        return (self.tzid, )

    def __hash__ (self):
        return hash (self._key ())

    def __cmp__ (self, other):
        return cmp (self._key (), other._key ())

class ZoneTab:
    default_pathname = "/usr/share/zoneinfo/zone.tab"
    default_filename = os.path.basename(default_pathname)

    _coord_pat = re.compile ('^([+-][0-9]+)([+-][0-9]+)$')

    @classmethod
    def _parse_line (cls, line):
        fields = line.split ("\t")

        try:
            country_code = fields.pop (0)
            coordinates = fields.pop (0)
            tz = fields.pop (0)
            comments = fields.pop (0) if len (fields) > 0 else ""
        except IndexError:
            raise ParseError ("cannot split the line into columns")

        match = ZoneTab._coord_pat.match (coordinates)
        if match is None:
            raise ParseError ("cannot match latitude and longitue")
        groups = match.groups ()
        if len (groups) != 2:
            raise ParseError ("cannot match latitude and longitude")

        def parse_coord (c):
            sign = c[0]
            if sign == "+":
                sign = 1
            elif sign == "-":
                sign = -1
            else:
                raise ParseError ("coordinate has a wrong sign")

            # possible formats: DDMM, DDDMM, DDMMSS, DDDMMSS
            rest = c[1:]
            l = len (rest)
            if l < 4 or l > 7:
                raise ParseError ("unrecognized format of coordinate")

            deg_len = 2 + l % 2
            degrees = int (rest[:deg_len], 10)
            rest = rest[deg_len:]

            minutes = int (rest[:2], 10)
            if l > 5:
                seconds = int (rest[2:], 10)
            else:
                seconds = 0
            return (sign, degrees, minutes, seconds)

        lat_str, lon_str = groups
        latitude = Coordinate (*parse_coord (lat_str))
        longitude = Coordinate (*(parse_coord (lon_str) + (3,)))
        coordinates = Coordinates (latitude, longitude)

        tzid = TZID (tz)
        return Zone (country_code, coordinates, tzid, comments)

    def __init__ (self, f):
        if isinstance (f, str) or isinstance (f, unicode):
            f = file (f, "rt")

        errors = []
        all_zones = []
        per_country = {}
        tzid_map = {}

        for line in f:
            line = line.strip ()
            c = line.find ("#")
            if c != -1:
                line = line[:c]
            if line == "":
                continue

            try:
                zone = ZoneTab._parse_line (line)
                if zone.tzid in tzid_map:
                    raise ParseError ("duplicate tzid")
                all_zones.append (zone)
                per_country.setdefault (zone.country, []).append (zone)
                tzid_map[zone.tzid] = zone
            except ParseError, e:
                errors.append ((line, e))

        self._per_country = per_country
        self._all_zones = all_zones
        self._tzid_map = tzid_map
        self._errors = errors

    def errors (self):
        return list (self._errors)

    def zones (self, country = None):
        """Raises KeyError if country is not found.
        Returns all zones if country is None."""
        if country is None:
            return list (self._all_zones)
        else:
            return self._per_country[country]

    def country(self, zonename):
        """Raises KeyError if zonename is not found."""
        return self._tzid_map[TZID(zonename)].country

    def countries (self):
        return list (self._per_country.keys ())

    def __str__ (self):
        return "\n".join ("\n".join (str (z) for z in self.zones (country))
                          for country in sorted (self.countries ()))

if __name__ == "__main__":
    import sys
    if len (sys.argv) > 1:
        n = sys.argv[1]
    else:
        n = ZoneTab.default_pathname
    zone_tab = ZoneTab(open(n, "rt"))
    assert len (zone_tab.errors ()) == 0, str (zone_tab.errors ())
    print str (zone_tab)
