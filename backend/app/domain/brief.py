from pydantic import BaseModel


class BriefItem(BaseModel):
    title: str
    detail: str


class DailyBrief(BaseModel):
    summary: str
    items: list[BriefItem] = []
