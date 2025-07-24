from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from schemas import UserOut, UserCreate
from core.security import get_password_hash, get_current_user
from typing import List

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# ✅ Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Get currently logged-in user
@router.get("/me", response_model=UserOut, operation_id="get_current_user_profile")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ✅ Get all users (typically for admin use)
@router.get("/", response_model=List[UserOut], operation_id="get_all_users")
def get_all_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# ✅ Create a new user
@router.post("/", response_model=UserOut, operation_id="register_new_user")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pw = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        hashed_password=hashed_pw,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from database import SessionLocal
# from models import User
# from schemas import UserOut, UserCreate
# from core.security import get_password_hash, get_current_user
# from typing import List

# router = APIRouter(
#     prefix="/users",
#     tags=["users"]
# )


# # Depefrom fastapi import APIRouter, Depends, HTTPException


# # ✅ Dependency to get DB session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # ✅ Get all users (optional, typically for admin)
# @router.get("/me")
# def get_me(current_user: User = Depends(get_current_user)):
#     return {"username": current_user.username, "role": current_user.role}

# @router.get("/", response_model=List[UserOut])
# def get_users(db: Session = Depends(get_db)):
#     return db.query(User).all()

# # ✅ Create a new user
# @router.post("/", response_model=UserOut)
# def create_user(user: UserCreate, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.username == user.username).first()
#     if db_user:
#         raise HTTPException(status_code=400, detail="Username already registered")
    
#     hashed_pw = get_password_hash(user.password)
#     new_user = User(
#         username=user.username,
#         hashed_password=hashed_pw,
#         role=user.role
#     )
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return new_user

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # Get all users (optional, typically admin only)
# @router.get("/", response_model=List[UserOut])
# def get_users(db: Session = Depends(get_db)):
#     return db.query(User).all()

# # Create new user (optionally restricted to admin only)
# @router.post("/", response_model=UserOut)
# def create_user(user: UserCreate, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.username == user.username).first()
#     if db_user:
#         raise HTTPException(status_code=400, detail="Username already registered")
    
#     hashed_pw = get_password_hash(user.password)
#     new_user = User(username=user.username, hashed_password=hashed_pw, role=user.role)
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return new_user
