from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    LargeBinary,
    MetaData,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

cache_table = Table(
    "cache",
    metadata,
    Column("cache_key", Text, primary_key=True),
    Column("status_code", Integer, nullable=False),
    Column("headers", JSONB, nullable=False),
    Column("body", LargeBinary, nullable=False),
    Column(
        "created_at", DateTime(timezone=True), server_default=func.now(), nullable=False
    ),
    CheckConstraint("status_code BETWEEN 100 AND 599", name="valid_status_code"),
)
