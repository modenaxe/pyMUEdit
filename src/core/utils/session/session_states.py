
SESSION_ID = None

def set_sessionid(sessionid: int):
    global SESSION_ID
    SESSION_ID = sessionid

def get_sessionid() -> int:
    return SESSION_ID