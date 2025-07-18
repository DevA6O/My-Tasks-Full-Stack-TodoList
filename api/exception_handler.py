import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# NOTE: Validation message could be more user-friendly - maybe change later

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """ Handler for validation errors (as from pydantic) """
    errors = exc.errors()

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": {
                "message": errors[0].get("msg", "Unknown error occurred."),
                "field": errors[0].get("loc", (None, None))[1]
            },
            "errors": errors
        }
    )