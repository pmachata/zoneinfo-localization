# This script takes the final .po file and extracts the context out of
# TZID string (i.e. moves A/B/C to C in context of A/B.  It also adds
# necessary messages for TZID prefixes as necessary.
#
# This script was used for initial seeding of tzdata translation repo.

import sys
import polib
from zonetab import TZID, ParseError
input_fn, = sys.argv[1:]

new_messages = {}

def extract_context (tzid, str_comps, top_context, message=None):
    if len (str_comps) != len (tzid.components):
        return

    if message is None:
        n = tzid.name ()
        has = n in new_messages
        message = new_messages.setdefault (n, polib.POEntry ())
        if not message.comment:
            message.comment = "Prefix of"
        message.comment = message.comment + " " + top_context.name ()
        if has:
            return

    message.msgid = tzid.components[-1]
    message.msgstr = str_comps[-1]
    if len (tzid.components) > 1:
        message.msgctxt = "/".join (tzid.components[:-1])
        extract_context (TZID (message.msgctxt), str_comps[:-1], top_context)

po = polib.pofile (input_fn)
for message in po:
    try:
        tzid = TZID (message.msgid)
    except ParseError, e:
        continue

    if len (tzid.components) > 1:
        extract_context (tzid, message.msgstr.split ("/"), tzid, message)

added_messages = list (new_messages[msgid] for msgid in sorted (new_messages))
po[:0] = added_messages
print unicode (po).encode ("utf-8")
