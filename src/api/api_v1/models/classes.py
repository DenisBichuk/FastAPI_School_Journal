from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from . import Base
from .mixins.int_id_pk import IntIdPkMixin

if TYPE_CHECKING:
    from . import Student
    from . import Teacher


class Class(IntIdPkMixin, Base):
    __tablename__ = "classes"

    class_num: Mapped[int] = mapped_column(unique=True)

    students: Mapped[list["Student"]] = relationship(back_populates="class_")
    teacher: Mapped["Teacher"] = relationship(back_populates="class_")

    __table_args__ = (UniqueConstraint("class_num"),)
