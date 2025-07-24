from sqlalchemy import create_engine
from models import Base, User, UploadedReport  # ✅ Add UploadedReport
from routers.auth import get_password_hash


# Use a single database for users and reports (recommended)
engine = create_engine("sqlite:///./kpi_users.db")

# Recreate tables — ⚠️ drop_all only for development
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Create initial admin user
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()



admin_user = User(
    username="admin",
    hashed_password=get_password_hash("admin"),  # ✅ correct field name
    role="admin"
)


db.add(admin_user)
db.commit()
db.close()

print("✅ User and report tables initialized.")
