from trac.core import *
from trac.timeline.api import ITimelineEventProvider
from genshi.builder import tag
from trac.wiki.formatter import format_to_html
import datetime

tweets = {
    1: ('http://twitter.com/jaylett', 'A little tweet', ),
    2: ('http://twitter.com/devfort', 'A longer tweet, just about', ),
}

googles = {
    3: ('http://tartarus.org/james/', 'The online home of James Aylett', ),
}

class TracMentionsPlugin(Component):
    implements(ITimelineEventProvider)

    def get_timeline_filters(req):
        return [ ( 'mentions', 'Mentions', False ), ]
        
    def get_timeline_events(req, start, stop, filters):
        if 'mentions' not in filters:
            return []
        return [
            ( 'Twitter', datetime.datetime(), None, 1 ),
            ( 'Twitter', datetime.datetime(), None, 2 ),
            ( 'Google', datetime.datetime(), None, 3 ),
        ]
        
    def render_timeline_event(context, field, event):
        if event[0]=='Twitter':
            ev = tweets[event[3]]
        elif event[0]=='Google':
            ev = googles[event[3]]

        if field=='title':
            return tag(tag.em('Whatever'), ' mentioned on ', event[0])
        elif field=='description':
            return format_to_html(self.env, context, ev[1])
        elif field=='url':
            return ev[0]
