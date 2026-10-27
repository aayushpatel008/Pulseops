from sqlalchemy import Column, Integer, String, Text
from app.database.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(200), nullable=False)

    description = Column(Text, nullable=True)

    status = Column(
        String(50),
        default="open",
        nullable=False,
    )

    priority = Column(
        String(20),
        default="medium",
        nullable=False,
    )