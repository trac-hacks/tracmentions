# (c) James Aylett 2009
# Database schema management based on MasterTicketPlugin, (c) Noah Kantrowitz 2007
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

from trac.core import *
from trac.timeline.api import ITimelineEventProvider
from trac.env import IEnvironmentSetupParticipant
from trac.db import DatabaseManager
from genshi.builder import tag
from trac.wiki.formatter import format_to_html
from trac.util.datefmt import to_timestamp, utc
from datetime import datetime
from time import time

# mentions = [
#     ('tweet', 'Twitter', 'http://twitter.com/jaylett', 'A little tweet', time(), ),
#     ('tweet', 'Twitter', 'http://twitter.com/devfort', 'A longer tweet, just about', time(), ),
#     ('aylett', 'Google', 'http://tartarus.org/james/', 'The online home of James Aylett', time(), )
# ]

import db_config

class TracMentionsPlugin(Component):
    implements(ITimelineEventProvider, IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.found_db_version = 0
        self.upgrade_environment(self.env.get_db_cnx())
    
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (db_config.system_key,))
        value = cursor.fetchone()
        if not value:
            self.found_db_version = 0
            return True
        else:
            self.found_db_version = int(value[0])
            if self.found_db_version < db_config.version:
                return True
        # else all is well
        return False
        
    def upgrade_environment(self, db):
        db_manager, _ = DatabaseManager(self.env)._get_connector()

        # Upgrade our tables
        old_data = {} # {table_name: (col_names, [row, ...]), ...}
        cursor = db.cursor()
        if not self.found_db_version:
            # no previous tables, just mark where we're going
            cursor.execute("INSERT INTO system (name, value) VALUES (%s, %s)",(db_config.system_key, db_config.version))
        else:
            # previous tables, stash the data & drop them
            cursor.execute("UPDATE system SET value=%s WHERE name=%s",(db_config.version, db_config.system_key))
            for tbl in db_config.tables:
                try:
                    cursor.execute('SELECT * FROM %s' % tbl.name)
                    old_data[tbl.name] = ([d[0] for d in cursor.description], cursor.fetchall())
                    cursor.execute('DROP TABLE %s' % tbl.name)
                except Exception, e:
                    if 'OperationalError' not in e.__class__.__name__:
                        raise e # If it is an OperationalError, just move on to the next table

        # create the new tables, and push in any stashed data
        # note that you can't rename or drop columns using this method
        for tbl in db_config.tables:
            for sql in db_manager.to_sql(tbl):
                cursor.execute(sql)

            # Try to reinsert any old data
            if tbl.name in old_data:
                data = old_data[tbl.name]
                sql = 'INSERT INTO %s (%s) VALUES (%s)' % \
                      (tbl.name, ','.join(data[0]), ','.join(['%s'] * len(data[0])))
                for row in data[1]:
                    try:
                        cursor.execute(sql, row)
                    except Exception, e:
                        if 'OperationalError' not in e.__class__.__name__:
                            raise e


    # ITimelineEventProvider methods
    def get_timeline_filters(self, req):
        return [ ( 'mentions', 'Mentions', False ), ]

    def get_timeline_events(self, req, start, stop, filters):
        if 'mentions' not in filters:
            return
        ts_start = to_timestamp(start)
        ts_stop = to_timestamp(stop)

        def make_event(mention):
            ts = mention[4]
            return (
                'mention-%s' % mention[1],
                datetime.fromtimestamp(ts, utc),
                None,
                mention,
            )

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT mentioned, location, uri, text, at FROM mentions WHERE at>=%s AND at<=%s",
                           (ts_start, ts_stop,))
            for r in cursor:
                yield make_event(r)
        except sqlite.OperationalError, e:
            # db lock, table doesn't exist, or something else that's hopefully transient
            self.env.log.info("Failed to fetch mentions: %s" % str(e))
        
    def render_timeline_event(self, context, field, event):
        ev = event[3]

        if field=='title':
            return tag(tag.em(ev[0]), ' found on ', ev[1])
        elif field=='description':
            return format_to_html(self.env, context, ev[3])
        elif field=='url':
            return ev[2]
