"""Predefined dataflows."""

refresh_ts = """switch ( 
    case has(event_ts) => yield this | put ts := now()
    case has(ts) => put event_ts := ts | put ts := now() 
    default => put ts := now() | put event_ts := ts
)"""

patch_ts = "switch ( case has(ts) => yield this " \
           "default => put ts := now() )"
