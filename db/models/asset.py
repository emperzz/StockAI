from typing import Any, Dict
from ..utils import to_decimal, parse_timestamp

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
# from sqlalchemy.sql.coercions import TruncatedLabelImpl

from .base import Base

class Asset(Base):
    """
    Asset model representing financial assets in the system.

    This table stores information about financial assets including stocks, bonds,
    cryptocurrencies, and other investment instruments.
    """

    __tablename__ = "assets"

    id = Column(Integer, primary_key = True, index = True)

    ticker = Column(
        String(50),
        unique = True,
        nullable = False,
        index = True,
        comment = "Asset symbol/ticker (e.g., NASDAQ:MSFT, SSE:000001, BK:0892)"
    )
    name = Column(
        String(200), 
        nullable = False, 
        comment = "Full name of the asset"
    )
    description = Column(
        Text, 
        nullable = True, 
        comment = "Detailed description of the asset"
    )

    asset_type = Column(
        String(50), 
        nullable = False,
        index = True,
        comment = "Type of asset (stock, index, bk, crypto, etc)"
    )

    current_price = Column(
        Numeric(precision = 20, scale = 8),
        nullable = False,
        comment = "Current market price"
    )

    is_active = Column(
        Boolean,
        default = True,
        nullable = False,
        comment = "Whether the asset is active"
    )

    asset_metadata = Column(
        JSON,
        nullable = True,
        comment = "Additional metadata (ISIN, CUSIP, fundamental data, etc.)",
    )

    config = Column(
        JSON,
        nullable=True,
        comment="Asset-specific configuration parameters",
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



    # Bidirectional relationship to AssetPrice
    prices = relationship(
        "AssetPrice",
        back_populates = "asset",
        lazy = "selectin",
    )

    stock = relationship(
        "Stock",
        back_pupulates = "asset",
        lazy = "joined",
        uselist=False
    )

    # Many-to-many to Sector via SectorStockMapping
    sector = relationship(
        "Sector",
        back_populates="asset",
        lazy = "joined",
    )

    def __repr__(self):
        return f"<Asset(id={self.id}, symbol='{self.ticker}', name='{self.name}', type='{self.asset_type}')>"

    def to_dict(self) -> Dict[str, Any]:

        return {
            'id': self.id,
            "ticker": self.ticker,
            "name": self.name,
            "description": self.description,
            "asset_type": self.asset_type,
            "current_price": float(self.current_price) if self.current_price else None,
            "is_active": self.is_active,
            "metadata": self.asset_metadata,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_config(cls, config_data: Dict[str, Any]) -> "Asset":

        return cls(
            ticker=config_data.get("ticker") or config_data.get("symbol"),
            name=config_data.get("name"),
            description=config_data.get("description"),
            asset_type=config_data.get("asset_type", "stock"),
            current_price=config_data.get("current_price"),
            is_active=config_data.get("is_active", True),
            asset_metadata=config_data.get("metadata"),
            config=config_data.get("config"),
        )


class AssetPrice(Base):
    """
    Sequential price data of asset 
    """

    __tablename__ = "asset_price"

    id = Column(Integer, primary_key = True, index = True)

    asset_id = Column(
        Integer,
        ForeignKey("assets.id", ondelete = "CASCADE"),
        index = True,
        nullable = False
    )

    # Relationship to access linked Asset row
    asset = relationship(
        "Asset",
        back_populates = "prices",
        lazy = "joined"
    )
    
    timestamp = Column(
        DateTime(timezone = True),
        nullable = False,
        comment = "Exchanging timestamp of asset price "
    )

    interval = Column(
        String(20),
        nullable = False,
        index = True,
        comment = "1d, 1m, 15m, 30m, 60m, 1m"
    )

    adjust = Column(
        String(20),
        nullable = False,
        comment = "qfq, hfq, bfq"
    )

    source = Column(
        String(50),
        nullable = True,
        comment = "Akshare, myquant, etc"
    )

    open = Column(Numeric(precision = 20, scale = 8), nullable = False,)

    high = Column(Numeric(precision = 20, scale = 8), nullable = False,)

    low  = Column(Numeric(precision = 20, scale = 8), nullable = False,)

    close = Column(Numeric(precision = 20, scale = 8), nullable = False,)

    amount = Column(Numeric(precision = 20, scale = 8), nullable = False,)

    volume = Column(Numeric(precision = 20, scale = 8), nullable = False,)

    change = Column(Numeric(precision = 20, scale = 8), nullable = False,)

    change_percent = Column(Numeric(precision = 10, scale = 10), nullable = False,)

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

    def __repr__(self):
        asset = getattr(self, "asset", None)
        asset_name = getattr(asset, "name", None) if asset else None
        asset_symbol = (getattr(asset, "ticker", None) or getattr(asset, "symbol", None)) if asset else None

        return (
            f"<AssetPrice(id={self.id}, asset_id={self.asset_id}, "
            f"asset_symbol='{asset_symbol}', asset_name='{asset_name}', "
            f"timestamp='{self.timestamp}', interval='{self.interval}', adjust='{self.adjust}', source='{self.source}', "
            f"open={self.open}, high={self.high}, low={self.low}, close={self.close}, amount={self.amount}, volume={self.volume}, "
            f"change={self.change}, change_percent={self.change_percent})>"
        )

    def to_dict(self) -> Dict[str, Any]:

        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'asset_symbol': getattr(self.asset, 'ticker', None) if getattr(self, 'asset', None) else None,
            'asset_name': getattr(self.asset, 'name', None) if getattr(self, 'asset', None) else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'interval': self.interval,
            'adjust': self.adjust,
            'source': self.source,
            'open': float(self.open) if self.open is not None else None,
            'high': float(self.high) if self.high is not None else None,
            'low': float(self.low) if self.low is not None else None,
            'close': float(self.close) if self.close is not None else None,
            'amount': float(self.amount) if self.amount is not None else None,
            'volume': float(self.volume) if self.volume is not None else None,
            'change': float(self.change) if self.change is not None else None,
            'change_percent': float(self.change_percent) if self.change_percent is not None else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_config(cls, config_data: Dict[str, Any], session=None) -> "AssetPrice":

        

        # resolve asset_id: prefer explicit asset_id; else lookup by ticker/symbol if session provided
        asset_id = config_data.get("asset_id")
        if not asset_id:
            ticker = config_data.get("ticker") or config_data.get("symbol")
            # prefer explicit session parameter; fallback to legacy keys in config_data
            session = session or config_data.get("session") or config_data.get("db_session")
            if ticker and session is not None:
                try:
                    asset_id = session.query(Asset.id).filter(Asset.ticker == ticker).scalar()
                except Exception:
                    asset_id = None

        return cls(
            asset_id = asset_id,
            timestamp = parse_timestamp(config_data.get("timestamp")),
            interval = config_data.get("interval"),
            adjust = config_data.get("adjust"),
            source = config_data.get("source"),
            open = to_decimal(config_data.get("open")),
            high = to_decimal(config_data.get("high")),
            low = to_decimal(config_data.get("low")),
            close = to_decimal(config_data.get("close")),
            amount = to_decimal(config_data.get("amount")),
            volume = to_decimal(config_data.get("volume")),
            change = to_decimal(config_data.get("change")),
            change_percent = to_decimal(config_data.get("change_percent")),
        )
