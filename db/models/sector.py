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

    ticker = Column(
        String(50), 
        ForeignKey("assets.ticker", ondelete = "CASCADE"),
        index = True,
        unique = True
    )
    
    ticker = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Sector code (e.g., BK:801010)"
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

    source = Column(
        String(50),
        nullable = True,
        comment = "Sector defined by which security"
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
    asset = relationship(
        "Asset",
        back_populates="sectors",
        lazy="joined",
        uselist = False
    )

    include_stocks = relationship(
        "SectorStockMapping",
        back_populates='sector',
        lazy = 'selectin'
    )




    def __repr__(self):
        return f"<Sector(id={self.id}, ticker='{self.ticker}', name='{self.name}, source ='{self.source}')>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "ticker": self.ticker,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_config(cls, config_data: Dict[str, Any]) -> "Sector":

        return cls(
            ticker=config_data.get("ticker") or config_data.get("symbol"),
            name=config_data.get("name"),
            asset_id = config_data.get('asset_id'),
            source=config_data.get("source"),
            description=config_data.get("description")
        )


