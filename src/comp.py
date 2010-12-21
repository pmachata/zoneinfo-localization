# This script takes the contextualized .po file and composes the
# final .po, where context is added before the messages themselves.

import sys
import polib
from zonetab import TZID, ParseError
from flags import *

input_fn,output_fn = sys.argv[1:]
po = polib.pofile (input_fn)

def full_msgid (message):
    if message.msgctxt:
        return message.msgctxt + "/" + message.msgid
    else:
        return message.msgid

# We don't know which messages will end up being prefixes, so we just
# extract everything to a dictionary to make lookups easy in the
# following.
messages = dict ((full_msgid (message), message) for message in po)

# This is where we track messages that turn out to be prefixes.
prefixes = set ()

# This is where we track translations.  We cannot modify them in
# place, because we don't know yet what will be a prefix.
translations = {}

for message in po:
    ctx = message.msgctxt.split ("/") if message.msgctxt is not None else []
    context_translations = []
    for i in range (1, len (ctx) + 1):
        subctx = ctx[:i]
        subctx_message = messages["/".join (subctx)]
        prefixes.add (subctx_message)
        subctx_translation = subctx_message.msgstr or subctx_message.msgid
        context_translations.append (subctx_translation)
    context_translations.append (message.msgstr or message.msgid)

    translations[message] = ("/".join (ctx + [message.msgid]),
                             "/".join (context_translations))

# Now we remove everything that turned out to be a prefix.
deleted = 0
for i, message in enumerate (list (po)):
    try:
        tzid = TZID (message.msgid)
    except ParseError, e:
        continue

    if message in prefixes:
        del po[i - deleted]
        deleted += 1

# Now we project the translations.
for message, (msgid, msgstr) in translations.iteritems ():
    message.msgctxt = None
    message.msgid = msgid
    message.msgstr = msgstr

# Now young man, onto the nice file.
with file (output_fn, "wt") as outf:
    outf.write (unicode (po).encode ("utf-8"))
