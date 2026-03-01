from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from .routers import post, user, auth, vote
from .config import settings
from .limiter import limiter

app = FastAPI()

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": f"Rate limit exceeded: {exc.detail}"},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    if "rate limit" in str(exc).lower():
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": f"Rate limit exceeded: {str(exc)}"},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": str(exc)},
    )

app.add_middleware(SlowAPIMiddleware)

origins = settings.allow_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        error_copy = error.copy()
        if 'password' in str(error.get('loc', [])):
            error_copy['input'] = '[REDACTED]'
        # Remove non-serializable objects
        if 'ctx' in error_copy and 'error' in error_copy['ctx']:
            error_copy['ctx']['error'] = str(error_copy['ctx']['error'])
        errors.append(error_copy)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": errors},
    )

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(vote.router)


@app.get("/")
def root():
    return {"message": "Welcome to my API"}
