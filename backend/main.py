from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.auth_router import router as auth_router
from routers.profile_router import router as profile_router
from routers.resource_router import router as resource_router
from routers.learning_router import router as learning_router

app = FastAPI(title="高等教育个性化学习智能体系统", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(resource_router)
app.include_router(learning_router)


@app.get("/")
async def root():
    return {"message": "高等教育个性化学习智能体系统 API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    print("已注册的路由：")
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            print(f"  {list(route.methods)} {route.path}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
