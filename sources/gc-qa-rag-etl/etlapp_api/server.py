from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os


from etlapp_api.routers.das import das_router
from etlapp_api.routers.etl import etl_router
from etlapp_api.routers.file_status import file_status_router
from etlapp_api.routers.publish import publish_router
from etlapp_api.routers.config import config_router
from etlapp_api.routers.log import log_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(das_router)
app.include_router(etl_router)
app.include_router(file_status_router)
app.include_router(publish_router)
app.include_router(config_router)
app.include_router(log_router)

# --- Static files ---

# Mount static files
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    # Mount assets directory separately to handle JS/CSS files
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(static_path, "assets")),
        name="assets",
    )
    # Mount root path for HTML files
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
