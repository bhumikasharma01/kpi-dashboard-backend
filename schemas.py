# backend/schemas.py
from pydantic import BaseModel,Field



# Input schema for login
class LoginInput(BaseModel):
   username: str = Field(..., min_length=1)
   password: str = Field(..., min_length=1)

# Input schema for user creation
class UserCreate(BaseModel):
    username: str
    password: str
    role: str

# Output schema for user (excluding password)
class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True  # ✅ Pydantic v2

       
