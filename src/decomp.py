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

def extract_context (tzid, str_comps, top_context, top_flags, message=None):
    if len (str_comps) != len (tzid.components):
        return

    translation = str_comps[-1]
    if message is None:
        name = tzid.name ()

        # Pair (comment, dict of candidate translations)
        candidates_pair = new_messages.setdefault (name,
                                                   ["Prefix of", {}])
        (_, candidates) = candidates_pair

        # Pair (use counter, translation)
        candidate = candidates.setdefault (translation,
                                           [0, 0, polib.POEntry ()])
        (_, _, message) = candidate

        candidates_pair[0] = candidates_pair[0] + " " + top_context.name ()
        candidate[int (u"fuzzy" in top_flags)] += 1
        if candidate[0] + candidate[1] > 1: # already seen
            return

    message.msgid = tzid.components[-1]
    message.msgstr = translation
    if len (tzid.components) > 1:
        message.msgctxt = "/".join (tzid.components[:-1])
        extract_context (TZID (message.msgctxt), str_comps[:-1],
                         top_context, top_flags)

po = polib.pofile (input_fn)
for message in po:
    try:
        tzid = TZID (message.msgid)
    except ParseError, e:
        continue

    if len (tzid.components) > 1:
        extract_context (tzid, message.msgstr.split ("/"), tzid,
                         message.flags, message)

def filter_candidates (candidates):
    # Here we try to got rid of obvious mistakes.

    # Look for the strongest candidate.  Sorting is done by number of
    # uses.  In case of tie, the one without underscores wins.
    candidate_list = list ((list (item) for item in candidates.items ()))
    def candidate_sorting_key ((translation,(uses,fuzzy_uses,message))):
        return (uses, "_" not in translation)
    candidate_list.sort (key=candidate_sorting_key, reverse=True)
    if len (candidate_list) == 1:
        return candidate_list

    # Project fuzzy candidate counts if there is evidence that the
    # translation is correct.
    for i, candidate in enumerate (candidate_list):
        (translation, (uses, fuzzy_uses, message)) = candidate
        if fuzzy_uses > 0:
            sys.stderr.write ((u"Note: %s: %s %s->%s.\n"
                               % (input_fn,
                                  ("not counting purely fuzzy"
                                   if uses == 0 else "counting fuzzy"),
                                  message.msgid, translation))
                              .encode ("utf-8"))
            if uses != 0:
                candidate[1][0] += candidate[1][1]

    # Normalize use of " " and "_".  Pick whatever the strongest
    # candidate uses.
    strongest = candidate_list[0]
    strongest_translation, (strongest_uses, _, strongest_message) = strongest
    use_underscores = "_" in strongest_translation
    new_candidates = [strongest]
    for i, candidate in enumerate (candidate_list[1:]):
        (translation, (uses, fuzzy_uses, message)) = candidate
        if ((use_underscores
             and (translation.replace (" ", "_") == strongest_translation))
            or ((not use_underscores)
                and (translation.replace ("_", " ") \
                         == strongest_translation))):
            # update uses
            strongest[1][0] += candidate[1][0]
            sys.stderr.write ((u"Note: %s: ignoring \"%s\" due to underscore normalization.\n" \
                                  % (input_fn, translation)).encode ("utf-8"))
            continue
        new_candidates.append (candidate)
    candidate_list = new_candidates
    if len (candidate_list) == 1:
        return candidate_list

    # Drop all candidates that are essentially unused, compared to the
    # strongest one.
    strongest_translation, (strongest_uses, _, strongest_message) = strongest
    deleted = 0
    for i, (_, (uses, _, _)) in enumerate (candidate_list[1:]):
        if uses <= strongest_uses / 10:
            del candidate_list[i+1-deleted]
            deleted += 1
    if len (candidate_list) == 1:
        return candidate_list

    # Case 1: forgotten letter.  If one candidate has minor usage in
    # comparison to other, and it's missing a single letter, drop it.
    return candidate_list

added_messages = []
for msgid, (comment, candidates) in new_messages.iteritems ():
    candidate_list = filter_candidates (candidates)
    if len (candidate_list) > 1:
        sys.stderr.write ("Warning: %s: ambiguous translation of %s.\n" % (input_fn, msgid))
        for translation, (uses, fuzzy_uses, message) in candidate_list:
            sys.stderr.write ((u" candidate: %s used %s times%s\n"
                               % (translation, uses,
                                  ((" (%s fuzzy)" % fuzzy_uses)
                                   if fuzzy_uses != 0 else "")))
                              .encode ("utf-8"))
    (_, (_, _, message)) = candidate_list[0]
    message.comment = comment
    added_messages.append ((msgid, message))

added_messages.sort (key=(lambda (msgid,message):msgid))
added_messages = list (message for _,message in added_messages)
po[:0] = added_messages
print unicode (po).encode ("utf-8")
