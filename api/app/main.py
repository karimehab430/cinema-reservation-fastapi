from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import auth, bookings, cinemas, movies, screenings
from app.core.logging import configure_logging
from app.exceptions import DomainError

configure_logging()

app = FastAPI(title="Cinema Reservation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(cinemas.router)
app.include_router(screenings.router)
app.include_router(bookings.router)


@app.exception_handler(DomainError)
async def domain_exception_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/health")
async def health():
    return {"status": "ok"}
