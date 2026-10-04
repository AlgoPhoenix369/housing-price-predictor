import re

from fastapi import Header, HTTPException

CLIENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


# Reads the visitor's anonymous ID from the X-Client-Id header and rejects bad values
def get_client_id(x_client_id: str | None = Header(default=None)) -> str:
    if not x_client_id or not CLIENT_ID_PATTERN.match(x_client_id):
        raise HTTPException(status_code=400, detail="Missing or invalid X-Client-Id header")
    return x_client_id