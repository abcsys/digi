import uuid

def link_flow():
    return f"put _token:='{str(uuid.uuid4())[:5]}'"
