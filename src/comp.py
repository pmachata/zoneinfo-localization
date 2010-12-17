# This script takes the contextualized .po file and composes the
# final .po, where context is added before the messages themselves.

import sys
import polib
from zonetab import TZID, ParseError
from flags import *

input_fn, = sys.argv[1:]

prefixes = {}

po = polib.pofile (input_fn)
deleted = 0
for i, message in enumerate (list (po)):
    try:
        tzid = TZID (message.msgid)
    except ParseError, e:
        continue

    if prefix_flag in message.flags:
        ctx = (message.msgctxt + "/") if message.msgctxt is not None else ""
        prefixes[ctx + message.msgid] = message
        del po[i - deleted]
        deleted += 1

for message in po:
    assert prefix_flag not in message.flags
    ctx = message.msgctxt.split ("/") if message.msgctxt is not None else []
    context_translations = []
    for i in range (1, len (ctx) + 1):
        subctx = ctx[:i]
        subctx_message = prefixes["/".join (subctx)]
        subctx_translation = subctx_message.msgstr or subctx_message.msgid
        context_translations.append (subctx_translation)
    context_translations.append (message.msgstr or message.msgid)

    message.msgctxt = None
    message.msgid = "/".join (ctx + [message.msgid])
    message.msgstr = "/".join (context_translations)

print unicode (po).encode ("utf-8")
