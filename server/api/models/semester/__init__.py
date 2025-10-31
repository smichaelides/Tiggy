from bson import ObjectId
from server.api.models._base import Model


class Semester(Model):
    _id: ObjectId  # 1262
    code: str  # "1262"
    name: str  # "F25-26"
    cal_name: str  # "Fall 2025"
    reg_name: str  # "25-26 Fall"
    start_date: str
    end_date: str
