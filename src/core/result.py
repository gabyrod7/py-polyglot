from dataclasses import dataclass

@dataclass
class Result:
    value: str | None = None
    message: str | None = None
    error_code: str | None = None

    @property
    def ok(self) -> bool:
        return self.error_code is None
