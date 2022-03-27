"""Predefined dataflows."""

refresh_ts = """switch ( 
    case has(event_ts) => yield this | put ts := now()
    case has(ts) => put event_ts := ts | put ts := now() 
    default => put ts := now() | put event_ts := ts
) 
"""
