# (c) James Aylett 2009
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

import simplejson
import urllib
import urllib2

from providers import user_agent_string, MySanitizer, Mention

# Note: this is a rubbish provider, but is fairly simple to follow.
# Please, don't actually use it. The GoogleAlertProvider is almost
# certainly what you want.
class GoogleProvider:
    api_endpoint = 'http://ajax.googleapis.com/ajax/services/search/web'
    def __init__(self, config):
        self.config = config

    def get_mentions(self, cursor):
        # ignore the keys here, they're just for show
        at = time.time()
        mentions = []
        for query in self.config.values():
            uri = "%s?%s" % (
                self.api_endpoint,
                urllib.urlencode({
                    'v': '1.0',
                    'q': query,
                }),
            )
            rq = urllib2.Request(
                uri,
                headers = { 'User-Agent': user_agent_string },
            )
            f = urllib2.urlopen(rq)
            obj = simplejson.loads(f.read())
            f.close()
            for result in obj['responseData']['results']:
                p = MySanitizer('utf-8')
                p.feed(result['content'])
                m = Mention(
                    query,
                    result['unescapedUrl'],
                    p.output(),
                    at,
                )
                mentions.append(m)
        return mentions
