"""Base classes and interfaces for asset data adapters.

This module defines the abstract base classes that all data source adapters
must implement to ensure consistent behavior across different providers.
"""

from decimal import Decimal
import logging
import pandas as pd
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .types import (
    AdapterMethod,
    Asset,
    AssetPrice,
    AssetSearchQuery,
    AssetSearchResult,
    AssetType,
    DataSource,
    Exchange,
)

logger = logging.getLogger(__name__)


@dataclass
class AdapterCapability:
    """Describes the asset types and exchanges supported by an adapter.

    This provides fine-grained control over adapter routing based on
    specific exchange and asset type combinations.
    """

    asset_type: AssetType
    exchanges: Set[Exchange]  # Supported exchanges
    methods: Set[AdapterMethod]
    method_priorities: Dict[AdapterMethod, int] = field(default_factory = dict)

    def supports_exchange(self, exchange: Exchange) -> bool:
        """Check if this capability supports the given exchange."""
        return exchange in self.exchanges

    def supports_method(self, method: AdapterMethod) ->bool:
        """Check if this capability supports the given method."""
        return method in self.methods

    def method_priority(self, method: AdapterMethod) -> int:
        """Get priority of method, if not set, default to 10"""

        if self.supports_method(method):
            return self.method_priorities.get(method, 10)

        logger.warning('Adapter got unspported method: {method}')
        return None
    


class BaseDataAdapter(ABC):
    """Abstract base class for all data source adapters."""

    def __init__(self, source: DataSource, api_key: Optional[str] = None, **kwargs):
        """Initialize adapter with data source and configuration.

        Args:
            source: Data source identifier
            api_key: API key for the data source (if required)
            **kwargs: Additional configuration parameters
        """
        self.source = source
        self.api_key = api_key
        self.config = kwargs
        self.logger = logging.getLogger(f"{__name__}.{source.value}")

        # Initialize adapter-specific configuration
        self._initialize()

    @abstractmethod
    def _initialize(self) -> None:
        """Initialize adapter-specific configuration and connections."""
        pass

    @abstractmethod
    def search_assets(self, query: AssetSearchQuery) -> List[AssetSearchResult]:
        """Search for assets matching the query criteria.

        Args:
            query: Search query parameters

        Returns:
            List of matching assets
        """
        pass

    @abstractmethod
    def get_asset_info(self, ticker: str) -> Optional[Asset]:
        """Get detailed information about a specific asset.

        Args:
            ticker: Asset ticker in internal format

        Returns:
            Asset information or None if not found
        """
        pass

    @abstractmethod
    def get_real_time_price(self, ticker: str) -> Optional[AssetPrice]:
        """Get real-time price data for an asset.

        Args:
            ticker: Asset ticker in internal format

        Returns:
            Current price data or None if not available
        """
        pass

    @abstractmethod
    def get_historical_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> List[AssetPrice]:
        """Get historical price data for an asset.

        Args:
            ticker: Asset ticker in internal format
            start_date: Start date for historical data, format: YYYY-MM-DD, timezone: UTC
            end_date: End date for historical data, format: YYYY-MM-DD, timezone: UTC
            interval: Data interval (e.g., "1d", "1h", "5m")

        Returns:
            List of historical price data
        """
        pass

    def get_multiple_prices(
        self, tickers: List[str]
    ) -> Dict[str, Optional[AssetPrice]]:
        """Get real-time prices for multiple assets.

        Args:
            tickers: List of asset tickers in internal format

        Returns:
            Dictionary mapping tickers to price data
        """
        results = {}
        for ticker in tickers:
            try:
                results[ticker] = self.get_real_time_price(ticker)
            except Exception as e:
                self.logger.error(f"Error fetching price for {ticker}: {e}")
                results[ticker] = None
        return results

    def validate_ticker(self, ticker: str) -> bool:
        """Validate if a ticker format is supported by this adapter.

        Args:
            ticker: Ticker in internal format (e.g., "NASDAQ:AAPL")

        Returns:
            True if ticker is valid for this adapter
        """
        try:
            if ":" not in ticker:
                return False

            exchange, _ = ticker.split(":", 1)
            capabilities = self.get_capabilities()

            # Check if any capability supports this exchange
            return any(
                cap.supports_exchange(Exchange(exchange)) for cap in capabilities
            )
        except Exception:
            return False

    def _parse_internal_ticker(self, internal_ticker: str) -> tuple[Optional[Exchange], str]:
        """Parse internal ticker to exchange enum and symbol.

        Returns (exchange_enum or None, symbol). When exchange is unknown, returns (None, symbol).
        """
        exchange, symbol = internal_ticker.split(":", 1)
        try:
            exchange_enum = Exchange(exchange)
        except ValueError:
            logger.warning(
                f"Unknown exchange '{exchange}' for ticker {internal_ticker}"
            )
            return None, symbol
        return exchange_enum, symbol

    def _check_asset_type(self, ticker: str) -> AssetType:
        """check ticker's asset type
        Args:
            ticker: Ticker in internal format (e.g., "SSE:000001")
        Returns:
            AssetType or None
        """
        exchange, symbol = self._parse_internal_ticker(ticker)
        if exchange == Exchange.BK:
            return AssetType.BK
        prefix = symbol[:2]
        if exchange not in [Exchange.SSE, Exchange.SZSE, Exchange.BSE]:
            logger.debug(f"doesn't support exchange {exchange.value}, current only suport SSE, SZSE, BSE")
            return None

        if prefix == '00':
            if exchange == Exchange.SSE:
                return AssetType.INDEX
            else:
                return AssetType.STOCK
        elif prefix in ['39', '98']:
            return AssetType.INDEX
        elif prefix in ['30', '60', '68', '92']:
            return AssetType.STOCK
        else:
            logger.warning(f'undefined logic for prefix of symbol {symbol}')
            return None

    def _convert_row_to_price(
        self, row: pd.Series, field_names: Dict[str, Optional[str]], **kwargs
    ) -> AssetPrice:
        """Convert a single DataFrame row to AssetPrice object.

        This method extracts price data from a row using field mappings, with optional
        overrides from kwargs. If a field exists in kwargs and has a value, it will be
        used instead of extracting from the row.

        Args:
            row: DataFrame row (pd.Series) containing price data
            field_names: Dictionary mapping standard field names to actual DataFrame
                        column names (e.g., {'close_field': '收盘', 'ticker_field': '代码'})
            **kwargs: Optional field overrides. Supported fields:
                     - ticker: Asset ticker in internal format
                     - price: Price value (Decimal or convertible)
                     - currency: Currency code (required if not in row)
                     - timestamp: Datetime object (required if not in row)
                     - pre_close_price, open_price, high_price, low_price, close_price
                     - volume, amount, change, change_percent, market_cap
                     - source: DataSource enum

        Returns:
            AssetPrice object constructed from row data and kwargs

        Raises:
            ValueError: If required fields (ticker, price, currency) are missing
        """

        # add timestamp to kwargs
        if kwargs is None or 'timestamp' not in kwargs.keys():
            kwargs['timestamp'] = None

        # Extract values: prefer kwargs, then row data via field_names
        def get_field_value(field_name: str) -> Optional[Any]:
            """Get field value from kwargs or row."""
            # First check kwargs
            if kwargs and field_name in kwargs:
                return kwargs[field_name]

            if field_names[field_name]:
                value = row[field_names[field_name]]
                if pd.notna(value):
                    return value

            return None

        # Extract ticker (required)
        ticker = get_field_value("ticker")
        if not ticker:
            raise ValueError("ticker is required (must be provided in kwargs or row)")

        # Convert ticker from source format if it's not already in internal format
        if ":" not in str(ticker):
            ticker = self.convert_to_internal_ticker(str(ticker))

        # Extract price (required) - try price_field first, then close_field
        price = get_field_value("price_field")
        if price is None:
            price = get_field_value('close_field')
            if price is None:
                raise ValueError(
                    "price is required (must be provided in kwargs or row via price_field/close_field)"
                )

        # Extract currency (required)
        currency = get_field_value("currency")
        if not currency:
            raise ValueError(
                "currency is required (must be provided in kwargs or determined from exchange)"
            )

        timestamp = get_field_value('timestamp')
        if not timestamp:
            time_value = get_field_value('time_field')
            # elif date_field and date_field in row.index:
            date_value = get_field_value('date_field')
            timestamp = time_value if time_value else date_value

        if timestamp is None:
            raise ValueError(
                "timestamp is required (must be provided in kwargs or row via time_field/date_field)"
            )

        # Parse timestamp if it's a string
        if isinstance(timestamp, str):
            if len(timestamp) == 8:  # Format: YYYYMMDD
                timestamp = datetime.strptime(timestamp, "%Y%m%d")
            else:
                timestamp = pd.to_datetime(timestamp)

        # Extract optional fields with Decimal conversion
        def to_decimal(value: Any) -> Optional[Decimal]:
            """Convert value to Decimal, handling None and NaN."""
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return None
            try:
                return Decimal(str(value))
            except (ValueError, TypeError):
                return None

        # Build AssetPrice object
        return AssetPrice(
            ticker=str(ticker),
            price=to_decimal(price),
            currency=str(currency),
            timestamp=pd.to_datetime(timestamp),
            pre_close_price=to_decimal(get_field_value("pre_close_field")),
            open_price=to_decimal(get_field_value("open_field")),
            high_price=to_decimal(get_field_value("high_field")),
            low_price=to_decimal(get_field_value("low_field")),
            close_price=to_decimal(get_field_value("close_field")),
            volume=to_decimal(get_field_value("volume_field")),
            amount=to_decimal(get_field_value("amount_field")),
            change=to_decimal(get_field_value("change_field")),
            change_percent=to_decimal(get_field_value("change_pct_field")),
            # market_cap=to_decimal(kwargs.get("market_cap")) if kwargs else None,
            source=kwargs.get("source", self.source)
        )

    @abstractmethod
    def convert_to_source_ticker(self, internal_ticker: str) -> str:
        """Convert internal ticker to data source format.

        Args:
            internal_ticker: Ticker in internal format (e.g., "NASDAQ:AAPL")
            source: Target data source

        Returns:
            Ticker in data source specific format (e.g., "AAPL" for yfinance)
        """
        pass

    @abstractmethod
    def convert_to_internal_ticker(
        self, source_ticker: str, default_exchange: Optional[str] = None
    ) -> str:
        """Convert data source ticker to internal format.
        Args:
            source_ticker: Ticker in data source format (e.g., "000001.SZ")
            source: Source data provider
            default_exchange: Default exchange if cannot be determined from ticker

        Returns:
            Ticker in internal format (e.g., "SZSE:000001")
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[AdapterCapability]:
        """Get detailed capabilities describing supported asset types and exchanges.

        Returns:
            List of capabilities describing what this adapter can handle
        """
        pass

    def get_supported_asset_types(self) -> List[AssetType]:
        """Get list of asset types supported by this adapter.

        This method extracts asset types from capabilities.
        """
        capabilities = self.get_capabilities()
        asset_types = set()
        for cap in capabilities:
            asset_types.add(cap.asset_type)
        return list(asset_types)

    def get_supported_exchanges(self) -> Set[Exchange]:
        """Get set of all exchanges supported by this adapter.

        Returns:
            Set of Exchange enums
        """
        capabilities = self.get_capabilities()
        exchanges: Set[Exchange] = set()
        for cap in capabilities:
            exchanges.update(cap.exchanges)
        return exchanges

    def get_supported_methods(self) -> Set[AdapterMethod]:
        """Get set of all methods supported by this adapter.

        Returns:
            Set of method enums
        """

        capabilities = self.get_capabilities()
        methods: Set[AdapterMethod] = set()
        for cap in capabilities:
            methods.update(cap.methods)
        return methods