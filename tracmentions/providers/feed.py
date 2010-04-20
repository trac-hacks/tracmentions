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

import calendar
import feedparser
import time

from providers import user_agent_string, MySanitizer, Mention

class FeedProvider:
    # Register a feed as:
    #
    # [tracmentions]
    # feed.shortname = <uri>
    def __init__(self, config):
        self.config = config

    def url_from_config(self, key, value):
        return value

    def auth_handlers(self, config):
        # config is the config that is currently being processed (which may not be laid out in any way
        # that's useful; eg for basic feeds it's just the URL).
        #
        # auth = urllib2.HTTPBasicAuthHandler()
        # auth.add_password(<realm>, <host>, <user>, <password>)
        # return [auth, ]
        return []
    
    def sleep(self):
        # In case you have rate limiting on your endpoints (useful in subclasses)
        return

    def get_mentions(self, cursor):
        mentions = []
        # keys here describe what we're searching for
        for key in self.config.keys():
            feed = self.url_from_config(key, self.config[key])
            #print key, '=', feed, '/', str(self.config[key])
            kwargs = {}
            cursor.execute("SELECT last_modified, etag FROM mentions_feeds WHERE uri=%s", (feed,))
            row = cursor.fetchone()
            feed_seen=False
            if row!=None:
                kwargs['etag'] = row[1]
                kwargs['modified'] = row[0]
                feed_seen=True
            kwargs['agent'] = user_agent_string
            kwargs['handlers'] = self.auth_handlers(self.config[key])
            f = feedparser.parse(feed, **kwargs)
            #print "Got feed length %i" % (len(f.entries),)
            for mentry in f.entries:
                # body/summary detection taken from toreadless.com (newspan)
                # but was written by me in the first place ;-)
                #
                # note that we're looking for the shortest thing that works
                # rather than the most content
                p = MySanitizer(f.encoding)
                body = None
                try:
                    content = mentry.content
                except AttributeError:
                    content = None
                try:
                    summary = mentry.summary
                except AttributeError:
                    summary = None
                if content:
                    body1 = content[0].value
                else:
                    body1 = ''
                if summary:
                    body2 = summary
                else:
                    body2 = ''
                if len(body1) > len(body2) and len(body2)>0:
                    body = body2
                else:
                    body = body1
                p.feed(body)
                m = Mention(
                    key,
                    mentry.link,
                    unicode(p.output(), f.encoding),
                    calendar.timegm(mentry.date_parsed))
                #print m
                mentions.append(m)
            
            etag = None
            last_modified = None
            if hasattr(f, 'etag') and f.etag:
                etag = f.etag
            if hasattr(f, 'last_modified') and f.last_modified:
                last_modified = time.strftime("%Y-%m-%d %H:%M:%S", f.modified)
            if etag or last_modified:
                if feed_seen:
                    cursor.execute(
                        "UPDATE mentions_feeds SET etag=%s, last_modified=%s WHERE uri=%s",
                        (etag, last_modified, feed,)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO mentions_feeds (uri, etag, last_modified) VALUES (%s, %s, %s)",
                        (feed, etag, last_modified,)
                    )
            self.sleep()

        return mentions
