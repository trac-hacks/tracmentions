# (c) James Aylett 2009, 2010
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software. 
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import re
import os
import sys
import time
from datetime import datetime 
from optparse import OptionParser

import providers

def update():
    parser = OptionParser()
    parser.add_option('-p', '--project', dest='project',
                      help='Path to the Trac project.')
    (options, args) = parser.parse_args(sys.argv[1:])

    if not options.project:
        print "Must specify path to Trac project (environment)."
        return 1

    if not 'PYTHON_EGG_CACHE' in os.environ:
        os.environ['PYTHON_EGG_CACHE'] = os.path.join(options.project, '.egg-cache')

    from trac.env import open_environment
    env = open_environment(options.project)
    config = {}
    ttl = 7 # only show a mention again after 7 days
    for i in env.config.options('tracmentions'):
        if i[0]=='ttl':
            ttl = int(i[1])
        bits = i[0].split('.')
        if bits[0]=='provider':
            if len(bits)==2:
                __import__(i[1])
                providers.register_provider(bits[1], sys.modules[i[1]].Provider)
        else:
            cur = config
            last = None
            for b in bits:
                if not cur.has_key(b):
                    cur[b] = {}
                last = cur
                cur = cur[b]
            last[b] = i[1]
            
    db = env.get_db_cnx()
    cursor = db.cursor()

    for pname in config.keys():
        try:
            conf = config[pname]
            provider = providers.get_provider(pname)
            if provider==None:
                print "%s doesn't match a provider; skipping." % pname
            else:
                p = provider(conf)
                mentions = p.get_mentions(cursor)
                for mention in mentions:
                    # if the uri is new or hasn't been seen in <ttl> days
                    print unicode(mention).encode('utf-8')
                    cursor.execute("SELECT at FROM mentions WHERE uri=%s", (mention.uri,))
                    row = cursor.fetchone()
                    if row!=None:
                        # when did we see it before?
                        #then = datetime.fromtimestamp(row[0])
                        then = row[0]
                        if (mention.at - then) < 86400 * ttl or mention.at==then:
                            # either identical (ie we've already go this), or
                            # not long enough ago to repost, so skip this
                            #
                            # (note that the or leg of that conditional will never be evaluated,
                            # because it's true only if the first leg is true. however this makes
                            # intent clearer)
                            print "(Skipping.)"
                            continue
                    cursor.execute(
                        "INSERT INTO mentions (mentioned, location, uri, text, at) VALUES (%s, %s, %s, %s, %s)",
                        (
                            mention.mentioned,
                            pname,
                            mention.uri,
                            mention.text,
                            mention.at,
                        )
                    )
        except:
            print "%s failed, skipping. Backtrace:" % pname
            import traceback
            traceback.print_exc()
    db.commit()
    return 0

if __name__ == "__main__":
    sys.exit(update())
