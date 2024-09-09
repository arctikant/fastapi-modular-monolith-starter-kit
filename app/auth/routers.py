from fastapi import APIRouter

from app.auth.routes.v1 import auth, profile, users

router_v1 = APIRouter()
router_v1.include_router(auth.router, prefix='/auth', tags=['auth'])
router_v1.include_router(users.router, prefix='/users', tags=['users'])
router_v1.include_router(profile.router, prefix='/profile', tags=['profile'])
