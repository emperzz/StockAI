from typing import Any, Dict

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Sector(Base):
    """
    Sector model representing a sector/industry which can contain many stocks (assets).
    """

    __tablename__ = "sectors"

    id = Column(Integer, primary_key=True, index=True)

    code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Sector code (e.g., SWL1-801010)"
    )

    name = Column(
        String(200),
        nullable=False,
        comment="Sector name"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Optional description of the sector"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Many-to-many to Asset via association table SectorStockMapping
    assets = relationship(
        "Asset",
        secondary="sector_stock_mapping",
        back_populates="sectors",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Sector(id={self.id}, code='{self.code}', name='{self.name}')>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SectorStockMapping(Base):
    """
    Association object mapping between Sector and Asset (many-to-many).
    You can add optional attributes like weight, source, etc.
    """

    __tablename__ = "sector_stock_mapping"

    id = Column(Integer, primary_key=True, index=True)

    sector_id = Column(
        Integer,
        ForeignKey("sectors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    asset_id = Column(
        Integer,
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional extra attributes for the mapping
    weight = Column(Numeric(precision=10, scale=4), nullable=True, comment="Optional weight of asset within sector")
    source = Column(String(50), nullable=True, comment="Data source tag")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("sector_id", "asset_id", name="uq_sector_asset"),
    )

    # Relationships back to entities (optional; not necessary for basic use)
    sector = relationship("Sector", lazy="joined")
    asset = relationship("Asset", lazy="joined")

    def __repr__(self):
        return f"<SectorStockMapping(id={self.id}, sector_id={self.sector_id}, asset_id={self.asset_id}, weight={self.weight})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sector_id": self.sector_id,
            "asset_id": self.asset_id,
            "weight": float(self.weight) if self.weight is not None else None,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


