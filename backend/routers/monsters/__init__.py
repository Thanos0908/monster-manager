"""
Monsters router package.
Purpose:
    Split monster routes into small, focused modules (SSR + future API),
    per frozen project contract.
Modules:
    - list.py   : GET /monsters
    - detail.py : GET /monsters/{id}
    - create.py : GET/POST /monsters/new
    - edit.py   : GET/POST /monsters/{id}/edit (admin)
    - delete.py : GET/POST /monsters/{id}/delete (admin)
This package exports:
    router: APIRouter including all monster sub-routers.
"""

from fastapi import APIRouter
from .list import router as list_router
from .create import router as create_router
from .detail import router as detail_router
from .edit import router as edit_router
from .delete import router as delete_router

router = APIRouter(tags=["monsters"])
router.include_router(list_router)
router.include_router(create_router)
router.include_router(detail_router)
router.include_router(edit_router)
router.include_router(delete_router)