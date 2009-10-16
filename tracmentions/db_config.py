# (c) James Aylett 2009

from trac.db import Table, Column, Index

system_key = 'mentions' # used in the system table to store our db version
version = 2
tables = [
    Table('mentions', key=('id'))[
        Column('id', auto_increment=True),
        Column('mentioned'),
        Column('location'),
        Column('uri'),
        Column('text'),
        Column('at', type='int'),
        Index(['at']),
        Index(['uri']),
    ],
    Table('mentions_feeds', key=('uri'))[
        Column('uri'),
        Column('last_modified'),
        Column('etag'),
    ],
]
