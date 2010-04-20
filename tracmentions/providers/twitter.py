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

import random
import time
import urllib
import urllib2
from feed import FeedProvider

class TwitterSearchProvider(FeedProvider):
    def __init__(self, config):
        self.config = config
        
    def sleep(self):
        time.sleep(1)

    def url_from_config(self, key, value):
        return "http://search.twitter.com/search.atom?q=%s&rpp=100&show_user=true&result_type=recent" % (urllib.quote_plus(value), )

# Abstracty. Don't try to make one!
class TwitterApiProvider(FeedProvider):
    def sleep(self):
        time.sleep(1)

    def auth_handlers(self, config):
        auth = urllib2.HTTPBasicAuthHandler()
        #print 'Twitter auth', config['user'], config['password']
        auth.add_password('Twitter API', 'api.twitter.com', config['user'], config['password'])
        return [auth, ]

class TwitterRepliesProvider(TwitterApiProvider):
    def __init__(self, config):
        self.config = config

    def url_from_config(self, key, value):
        return "http://api.twitter.com/1/statuses/mentions.atom?count=200"

class TwitterTimelineProvider(TwitterApiProvider):
    def __init__(self, config):
        self.config = config

    def url_from_config(self, key, value):
        return "http://api.twitter.com/1/home_timeline.atom?count=200"

class TwitterProvider:
    # twitter.searches.shortname = search terms
    # twitter.replies.shortname.user = username
    # twitter.replies.shortname.password = password
    # twitter.timeline.shortname.user = username
    # twitter.timeline.shortname.password = password
    def __init__(self, config):
        self.config = config
        
    def get_mentions(self, cursor):
        random.seed()
        #for k in self.config.keys():
        #    print ">>%s = %s" % (k, self.config[k])

        # do mentions, replies, friends_timeline in a random order
        # for each, do the sublabels in a random order
        # and sleep a short time (1s) between each request
        #
        # the combination is intended to ensure that even after
        # ip address throttling, we'll periodically get them all
        #
        # but since you really only need to run this once an hour at most
        # that really isn't going to be an issue
        types = {
            'searches': TwitterSearchProvider,
            'replies': TwitterRepliesProvider,
            'timeline': TwitterTimelineProvider,
        }
        keys = types.keys()
        keys.sort(lambda x,y: random.randint(0, 2)-1)
        result = []
        for key in keys:
            try:
                p = types[key](self.config[key])
                result.extend(p.get_mentions(cursor))
            except KeyError:
                pass # so you don't have to configure all of searches, replies, timeline -- which would be weird
        return result
