from typing import Any, Dict
from sqlalchemy import TEXT, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from ..utils import parse_timestamp


class Stock(Base):

    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True, index=True)

    ticker = Column(
        String(50), 
        ForeignKey("assets.ticker", ondelete = "CASCADE"),
        index = True,
        unique = True
    )

    name = Column(
        String(20),
        nullable = False
    )

    business = Column(
        TEXT,
        nullable = True,
        comment = "main business"
    )

    business_scope = Column(
        TEXT,
        nullable = True,
        comment = "detailed business desctiption "
    )

    listed_date = Column(
        DateTime(timezone = True),
        nullable = True,
        comment = "Date when stock listed in the exchange market"
    )

    trade_n = Column(
        Integer,
        nullable = False,
        default = 1
    )
    
    created_at = Column(
        DateTime(timezone = True),
        server_default = func.now(),
        nullable = False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    asset = relationship(
        "Asset",
        back_populates = "stock",
        lazy = 'joined',
        uselist = False
    )

    belong_to_sectors = relationship(
        "SectorStockMapping",
        back_populates = "stock",
        lazy = 'selectin'
    )

    def __repr__(self):
        return f"<Stock(id={self.id}, ticker='{self.ticker}', name='{self.name}', business ='{self.business}')>"

    def to_dict(self):

        return {
            'id': self.id,
            'ticker': self.ticker,
            'name': self.name,
            'business': self.business,
            'busihness_scope': self.business_scope,
            'listed_date': self.listed_date,
            'trade_n': self.trade_n,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_config(cls, config_data: Dict[str, Any]) -> "Stock":

        return cls(
            ticker=config_data.get("ticker") or config_data.get("symbol"),
            asset_id = config_data.get('asset_id'),
            name=config_data.get("name"),
            business=config_data.get("business"),
            business_scope=config_data.get("business_scope"),
            listed_date=parse_timestamp(config_data.get("parse_timestamp")),
            trade_n = int(str(config_data.get('trade_n')))
        )