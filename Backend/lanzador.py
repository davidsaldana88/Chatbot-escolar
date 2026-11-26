from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as ExcepcionStarlette

from app.main import app as api


class AplicacionWeb(StaticFiles):
    """Sirve el frontend y, ante rutas de React como /admin/login, devuelve index.html."""

    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except ExcepcionStarlette as error:
            if error.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


carpeta_web = Path(__file__).resolve().parent.parent / "frontend" / "dist"

principal = FastAPI(lifespan=api.router.lifespan_context)
principal.mount("/api", api)
principal.mount("/", AplicacionWeb(directory=carpeta_web, html=True))

if __name__ == "__main__":
    uvicorn.run(principal, host="127.0.0.1", port=8000)