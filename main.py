from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi



from routers import dashboard, report, auth, upload, users
from models import Base
from database import engine
from fastapi.middleware.cors import CORSMiddleware
import os



origins = os.getenv("ALLOWED_ORIGINS", "").split(",")







app = FastAPI(title="KPI Dashboard Backend")
# @app.on_event("startup")
# def show_routes():
#     for route in app.routes:
#         print(f"✅ {route.path} - {route.name}")
# ✅ Create DB tables
Base.metadata.create_all(bind=engine)

# ✅ CORS Middleware (optional, for frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kpi-dashboard-frontend-lw9pbtncappdcrarder8mis.streamlit.app"],  # Set to frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register routers
app.include_router(users.router, tags=["users"])
app.include_router(upload.router, tags=["upload"])
app.include_router(report.router, tags=["report"])
app.include_router(auth.router, tags=["auth"])



app.include_router(dashboard.router)
# ✅ Root route
@app.get("/")
def read_root():
    return {"message": "KPI Backend is running"}

# ✅ Swagger security customization (JWT Bearer Auth)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="KPI Dashboard API",
        version="1.0.0",
        description="This is the backend API for the KPI dashboard project.",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation.setdefault("security", []).append({"BearerAuth": []})
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
