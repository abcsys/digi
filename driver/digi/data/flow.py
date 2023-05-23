"""A collection of predefined dataflows."""

from digi.data.de_id import de_id
from digi.data.link import link
from digi.data.de_id.util import PII_Fields

refresh_ts = """switch ( 
    case has(event_ts) => yield this | put ts := now()
    case has(ts) => put event_ts := ts | put ts := now() 
    default => put event_ts := now() | put ts := event_ts
)"""

patch_ts = "switch ( case has(ts) => yield this " \
           "default => put ts := now() )"

drop_meta = "not __meta"

de_id = de_id.De_id(exceptions=PII_Fields["date"]).gen()

link = link.link_flow
