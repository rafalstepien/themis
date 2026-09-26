from typing import Self

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.bootstrap.exceptions import MissingEnvironmentError

LLM_TOKEN_ENV_VAR = "LLM_API_TOKEN"


class _EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    @classmethod
    def load(cls) -> Self:
        try:
            return cls()
        except ValidationError as exc:
            missing = [
                str(location)
                for error in exc.errors()
                if error["type"] == "missing"
                for location in error["loc"]
            ]
            raise MissingEnvironmentError(missing) from exc
