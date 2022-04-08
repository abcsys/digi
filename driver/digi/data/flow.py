"""Predefined dataflows."""

refresh_ts = """switch ( 
    case has(event_ts) => yield this | put ts := now()
    case has(ts) => put event_ts := ts | put ts := now() 
    default => put event_ts := now() | put ts := event_ts
)"""

patch_ts = "switch ( case has(ts) => yield this " \
           "default => put ts := now() )"

drop_meta = "not __meta"
