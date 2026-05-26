from fastapi import FastAPI
from models import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from routers.auth_router import router as auth_router
from routers.profile_router import router as profile_router
from routers.resource_router import router as resource_router
from routers.learning_router import router as learning_router

app = FastAPI(title="Personalized Learning System", version="1.0.0")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(resource_router)
app.include_router(learning_router)


@app.get("/")
async def root():
    return {"message": "Personalized Learning System API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    print("Registered routes:")
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            print(f"  {list(route.methods)} {route.path}")
    uvicorn.run(app, host="0.0.0.0", port=8000)