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
import simplejson
import time
import urllib
import urllib2

# Provider API
_providers = {}

def register_provider(name, provider):
    _providers[name] = provider

def get_provider(name):
    return _providers.get(name, None)

class Mention:
    def __init__(self, mentioned, uri, text, at):
        """Please make text unicode or an ascii-only str."""
        self.mentioned = mentioned
        self.uri = uri
        self.text = text
        self.at = at

    def __unicode__(self):
        return u"Mention on %s: %s @ %s\n%s" % (
            self.uri,
            self.mentioned,
            time.strftime(
                "%Y-%m-%dT%H:%M:%S%z",
                time.gmtime(self.at)
            ),
            self.text
        )

    def __str__(self):
        return unicode(self).encode('utf-8')

# Utility pieces
user_agent_string = 'tracmentions/0.1 (http://tartarus.org/james/computers/tracmentions/)'

# Ouch. The parent class isn't really exposed by feedparser, so this may break.
class MySanitizer(feedparser._HTMLSanitizer):
    acceptable_elements = []

from twitter import *
#from google import *
from feed import *
from googlealert import *

# Some useful defaults; you can happily override these if you want to use
# the names for something else.
register_provider('twitter', TwitterProvider)
#register_provider('twittersearch', TwitterSearchProvider) ## not needed (use TwitterProvider)
#register_provider('google', GoogleProvider) # don't register this, because you shouldn't use it
register_provider('googlealert', GoogleAlertProvider)
register_provider('feed', FeedProvider)
