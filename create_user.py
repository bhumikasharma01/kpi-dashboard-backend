# backend/create_user.py

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from models import User, Base
# from auth import get_password_hash

# DATABASE_URL = "sqlite:///./users.db"

# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # ✅ Create tables if they don't exist
# Base.metadata.create_all(bind=engine)

# db = SessionLocal()

# # Create a new user (change values as needed)
# new_user = User(
#     username="admin",
#     hashed_password=get_password_hash("admin123"),
#     role="admin"
# )

# db.add(new_user)
# db.commit()
# db.close()

# print("✅ User created: admin / admin123")
