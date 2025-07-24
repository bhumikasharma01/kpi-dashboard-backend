from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User as UserModel
from schemas import LoginInput, UserCreate
from core.security import verify_password, create_access_token, get_password_hash, get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/login")
def login_user(login_input: LoginInput, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == login_input.username).first()
    if not user or not verify_password(login_input.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Include user's role in the JWT token
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

# ✅ Add this function below login_user
@router.post("/create-user")
def create_user(
    new_user: UserCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)  # Uses JWT token
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create users")

    existing_user = db.query(UserModel).filter(UserModel.username == new_user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = get_password_hash(new_user.password)
    user = UserModel(
        username=new_user.username,
        hashed_password=hashed_password,
        role=new_user.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created successfully"}

@router.delete("/delete-user")
def delete_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete users")

    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"message": f"User '{username}' deleted successfully"}
@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view users")

    users = db.query(UserModel).all()
    return [{"username": user.username, "role": user.role} for user in users]

