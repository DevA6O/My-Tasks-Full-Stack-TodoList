import jwt
import uuid
from datetime import datetime, timezone
from security.jwt import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, 
    create_token
)

def test_create_token():
    data: dict = {"sub": str(uuid.uuid4())}
    token = create_token(data=data)

    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    # Test whether the data is correct set
    assert decoded_token["sub"] == data["sub"]
    assert "exp" in decoded_token

    # Check that the expiry date is correct.
    expire = datetime.fromtimestamp(decoded_token["exp"], tz=timezone.utc)
    assert expire > datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)
    delta = expire - now

    assert 0 < delta.total_seconds() <= ACCESS_TOKEN_EXPIRE_MINUTES * 60 + 5

