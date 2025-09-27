from fastapi import APIRouter
from routes.settings.s_service import router as ServiceRouter
from routes.settings.s_session_handler import router as SessionHandler

SettingsRouter = APIRouter(prefix="/api/settings")

SettingsRouter.include_router(ServiceRouter)
SettingsRouter.include_router(SessionHandler)