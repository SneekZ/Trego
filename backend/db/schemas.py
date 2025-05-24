from weakref import ReferenceType
from click import Option
from pydantic import BaseModel
from typing import Optional

class UserModel(BaseModel):
    email: str
    lastName: Optional[str]
    firstName: Optional[str]
    refreshToken: Optional[str]
    sessionToken: Optional[str]