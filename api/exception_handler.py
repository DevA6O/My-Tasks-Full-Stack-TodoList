from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Dict

ERROR_MAPPING: Dict[str, str] = {
    "email": "Email must be a valid email address."
}
DEFAULT_ERROR_MSG: str = "Server error: The server was unable to verify the action. Please try again later."

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """ Handler for validation errors (as from pydantic) """
    errors = exc.errors()

    # Fetches the field (where the error is occurred) and tries to fetch an error message
    # from the error mapping, if available
    field: str = errors[0].get("loc", (None, None))[1]
    error_msg: str = ERROR_MAPPING.get(field, "")

    # Fetches the default error message from pydantic
    # if an error message couldn't found in the error mapping
    if not error_msg:
        error_msg: set = errors[0].get("msg", DEFAULT_ERROR_MSG)
        error_msg = error_msg.replace("String", field.capitalize())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": {
                "message": error_msg,
                "field": field
            },
            "errors": errors
        }
    )