from pydantic import BaseModel


class TestResult(BaseModel):
    name: str
    passed: bool
    duration: float
    details: dict = {}


class TestResults(BaseModel):
    results: list[TestResult]
    service: str
    region: str
    timestamp: int
    duration: float
