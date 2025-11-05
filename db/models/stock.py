


from sqlalchemy import TEXT, Column, ForeignKey, Integer, String
from .base import Base


class Stock(Base):

    __tablename__ = 'stock'

    id = Column(Integer, primary_key=True, index=True)

    asset_id = Column(
        Integer,
        ForeignKey("assets.id", ondelete = "CASCADE"),
        nullable = False,
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

    