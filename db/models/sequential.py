
from langchain_core.language_models.fake import FakeListLLMError
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class DailyPrice(Base):

    __tablename__ = 'daily_price'

    id = Column(Integer, primary_key=True)

    ticker = Column(
        String(50), 
        ForeignKey("assets.ticker", ondelete = "CASCADE"),
        index = True
    )
    
    is_suspended = Column(
        Boolean,
        nullable = False,
        default = False
    )

    is_st = Column(
        Boolean,
        nullable = False,
        default = False
    )

    timestamp = Column(
        DateTime(timezone = True),
        nullable = False
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

    open = Column(Numeric(precision = 20, scale = 8), nullable = True)
    close = Column(Numeric(precision = 20, scale = 8), nullable = True)
    high = Column(Numeric(precision = 20, scale = 8), nullable = True)
    low = Column(Numeric(precision = 20, scale = 8), nullable = True)
    pre_close = Column(Numeric(precision = 20, scale = 8), nullable = True)
    amount = Column(Numeric(precision = 20, scale = 8), nullable = True)
    volume = Column(Numeric(precision = 20, scale = 8), nullable = True)
    change = Column(Numeric(precision = 20, scale = 8), nullable = True)
    change_percent = Column(Numeric(precision = 20, scale = 8), nullable = True)
    upper_limit = Column(Numeric(precision = 20, scale = 8), nullable = True)
    lower_limit = Column(Numeric(precision = 20, scale = 8), nullable = True)
    turn_rate = Column(Numeric(precision = 20, scale = 8), nullable = True)
    adj_factor = Column(Numeric(precision = 20, scale = 8), nullable = True)

    def __repr__(self):
        return (
            f"DailyPrice(id={self.id}, ticker={self.ticker}, timestamp={self.timestamp}, is_suspended={self.is_suspended}, is_st={self.is_st}"
            f"open={self.open}, close={self.close}, high={self.high}, low={self.low} )>"
        )


class MinutePrice(Base):
    
    __tablename = "minite_price"

    id = Column(Integer, primary_key=True)

    ticker = Column(
        String(50), 
        ForeignKey("assets.ticker", ondelete = "CASCADE"),
        index = True
    )

    timestamp = Column(
        DateTime(timezone = True),
        nullable = False
    )

    frequency = Column(
        String(10),
        nullable = False,
        default = '1m',
        comment = "1m, 15m, 30m, 60m"
    )

    adjust = Column(
        String(10),
        nullable = False,
        comment = "qfq, hfq, bfq"
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

    open = Column(Numeric(precision = 20, scale = 8), nullable = False)
    close = Column(Numeric(precision = 20, scale = 8), nullable = False)
    high = Column(Numeric(precision = 20, scale = 8), nullable = False)
    low = Column(Numeric(precision = 20, scale = 8), nullable = False)
    pre_close = Column(Numeric(precision = 20, scale = 8), nullable = True)
    amount = Column(Numeric(precision = 20, scale = 8), nullable = False)
    volume = Column(Numeric(precision = 20, scale = 8), nullable = False)

    def __repr__(self):
        return (
            f"MinutePrice(id={self.id}, ticker={self.ticker}, timestamp={self.timestamp}, frequency={self.frequency}, adjust={self.adjust}"
            f"open={self.open}, close={self.close}, high={self.high}, low={self.low} )>"
        )

