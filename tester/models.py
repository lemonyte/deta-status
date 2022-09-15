from pydantic import BaseModel


class Result(BaseModel):
    service: str
    region: str
    passed: bool
    timestamp: int
    duration: float
    details: dict = {}
