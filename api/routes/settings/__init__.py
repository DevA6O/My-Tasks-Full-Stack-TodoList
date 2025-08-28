from fastapi import APIRouter
from routes.settings.s_service import router as ServiceRouter

SettingsRouter = APIRouter()
SettingsRouter.include_router(ServiceRouter)