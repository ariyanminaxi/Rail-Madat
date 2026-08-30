"""
RailMaintain — Authentication Schemas
"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    user_id: str
    role: str
    display_name: str
