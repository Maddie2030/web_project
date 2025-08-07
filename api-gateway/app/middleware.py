# api-gateway/app/middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import HTTPException, status
from .dependencies import validate_token

class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, public_routes: list = None):
        super().__init__(app)
        self.public_routes = public_routes or []

    async def dispatch(self, request: Request, call_next):
        # 1. Allow OPTIONS requests to pass without authentication
        if request.method == "OPTIONS":
            return await call_next(request)

        # 2. Check if the path is a public route
        is_public = any(
            request.url.path.startswith(route.split('{')[0])
            for route in self.public_routes
        )

        if is_public:
            response = await call_next(request)
            return response

        # Get the Authorization header
        authorization = request.headers.get("Authorization")

        # Handle missing Authorization header
        if not authorization:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authorization header is missing"}
            )
        
        try:
            # Attempt to extract and validate the token
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"}
                )

            user_id = validate_token(token=token)
            request.state.user_id = user_id
            response = await call_next(request)
            return response
        except (ValueError, HTTPException) as e:
            # Handle split errors (ValueError) and validation errors (HTTPException)
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Invalid token or credentials"})