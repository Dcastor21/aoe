from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import vapi, jobs, routes, qa, jobber

app = FastAPI(
    title="AOE API",
    description="API for the AOE cleaning company management system",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(vapi.router, prefix="/vapi", tags=["vapi"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(routes.router, prefix="/api/v1/routes", tags=["routes"])
app.include_router(qa.router, prefix="/api/v1/qa", tags=["qa"])
app.include_router(jobber.router, prefix="/intergrations", tags=["jobber"])


@app.get("/")
async def health_check():
        return {"status": "ok", "service": "AOE API"}