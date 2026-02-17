from server.api.models._base import Model


class User(Model):
    _id: str | None
    name: str
    email: str
    grade: str
    concentration: str | None
    certificates: list[str]
    past_courses: dict[str, str] = {}