from sqlalchemy.orm import Mapped

from src.users import Base


class Class(Base):
    __tablename__ = "classes"

    class_num: Mapped[int]
