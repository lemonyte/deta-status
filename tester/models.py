from pydantic import BaseModel


class TestResult(BaseModel):
    name: str
    passed: bool
    duration: float
    details: dict = {}


class TestResults(BaseModel):
    tests: dict[str, TestResult]
    service: str
    region: str
    timestamp: int
    duration: float
