import hashlib

def link_flow(id):
    token = hashlib.md5(id.encode()).hexdigest()
    return f"put _token:='{token[:5]}'"
