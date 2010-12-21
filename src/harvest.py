# This is to be launched over tzdata source directory.  It harvests
# all the zone names and other translatable strings in that release.
# For timezone names, it does the context extraction, too.

from zonetab import ZoneTab, TZID, Zone
import sys
import os

tzdir, = sys.argv[1:]

# The following is adapted from tzcode's makefile
PRIMARY_YDATA = ["africa", "antarctica", "asia", "australasia",
                 "europe", "northamerica", "southamerica"]
YDATA = PRIMARY_YDATA + ["pacificnew", "etcetera", "factory", "backward"]
NDATA = ["systemv"]
SDATA = ["solar87", "solar88", "solar89"]
TDATA = YDATA + NDATA + SDATA

class ZoneId (object):
    def __init__ (self, tzid):
        self._tzid = tzid
        self.comments = ""

    def link_p (self):
        return False

    def tzid (self):
        return self._tzid

    def __str__ (self):
        return str (self._tzid)

class ZoneLink (ZoneId):
    def __init__ (self, tzid, ref_tzid, comment):
        ZoneId.__init__ (self, tzid)
        self._ref_tzid = ref_tzid
        self.comments = comment

    def __str__ (self):
        return "link from %s to %s" % (self._ref_tzid, self._tzid)

    def link_p (self):
        return True

def get_zones (fns):
    """Yields pairs (zn, real), where zn is a zone name, and real
    signifies whether it's a real zone (True) or a link (False)."""
    for fn in fns:
        for l in file (fn):
            if l.startswith ("Zone"):
                yield ZoneId (TZID (l.split ()[1]))
            elif l.startswith ("Link"):
                if "#" in l:
                    l, comment = l.split ("#", 1)
                    comment = comment.strip ().strip ("#")
                else:
                    comment = ""
                ref_name, my_name = l.split ()[1:3]
                yield ZoneLink (TZID (my_name), TZID (ref_name), comment)

# List of all zones and links defined in any tzdata source file.
# That's map TZID->ZoneId.
all_zone_ids =  dict ((zone_id.tzid (), zone_id)
                      for zone_id
                      in get_zones (tzdir + os.sep + data for data in TDATA))

zone_tab = ZoneTab (tzdir + os.sep + "zone.tab")
zones = dict ((zone.tzid, zone) for zone in zone_tab.zones ())

# Make sure that zone.tab isn't making stuff up.
assert all (tzid in all_zone_ids for tzid in zones)

# Add zones not mentioned in zone.tab.  That means that the "zones"
# table contains either Zone, ZoneLink or ZoneId in place of values.
for tzid, zone_id in all_zone_ids.iteritems ():
    if tzid not in zones:
        zones[tzid] = zone_id

def output (message, context=None):
    if not message:
        return
    if not context:
        print "N_(\"%s\");\n" % message
    else:
        print "C_(\"%s\", \"%s\");\n" % (context, message)

messages = set ()
def output_zone (components, zone):
    global context_messages
    if len (components) == 0:
        return
    ctx = components[:-1]
    output_zone (ctx, None)
    ctxstr = "/".join (ctx)
    msgstr = components[-1]
    message = (msgstr, ctxstr)
    if message not in messages:
        messages.add (message)
        if zone is None:
            print "/* time zone prefix */"
        else:
            print "/* name of time zone %s */" % zone
        output (*message)

for tzid, zone in sorted (zones.iteritems ()):
    output_zone (tzid.components, zone)
    if zone is not None:
        if zone.comments:
            print "/* comment for time zone %s */" % tzid
            output (zone.comments)
