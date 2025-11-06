from typing import Any, Dict

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

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

    stock_id = Column(
        Integer,
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    is_removed = Column(
        bool,
        nullable = False,
        default = False
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

    __table_args__ = (
        UniqueConstraint("sector_id", "stock_id", name="uq_sector_stock"),
    )

    # Relationships back to entities (optional; not necessary for basic use)
    sector = relationship("Sector", lazy="joined", back_populates = "include_stocks")
    stock = relationship("Stock", lazy="joined", back_populates = "belong_to_sectors")

    def __repr__(self):
        return f"<SectorStockMapping(id={self.id}, sector_id={self.sector_id}, asset_id={self.stock_id}, is_removed={self.is_removed})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sector_id": self.sector_id,
            "asset_id": self.stock_id,
            "is_removed": self.is_removed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    