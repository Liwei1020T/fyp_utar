from typing import Annotated

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import StringConstraints

from app.core.constants import PASSWORD_RESET_CODE_LENGTH
from app.core.constants import UserRole
from app.schemas.common import PasswordString
from app.schemas.common import PhoneNumber
from app.schemas.common import TrimmedString


class DevLoginPayload(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    role: UserRole


class RegisterPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: TrimmedString
    phone_number: PhoneNumber
    password: PasswordString


class LoginPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: PhoneNumber
    password: Annotated[str, StringConstraints(min_length=1)]


class ForgotPasswordRequestPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: PhoneNumber


class ForgotPasswordResetPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: PhoneNumber
    verification_code: Annotated[
        str,
        StringConstraints(pattern=rf"^\d{{{PASSWORD_RESET_CODE_LENGTH}}}$"),
    ]
    new_password: PasswordString
