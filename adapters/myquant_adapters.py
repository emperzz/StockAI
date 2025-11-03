from datetime import datetime
from decimal import Decimal
from .base import AdapterCapability, BaseDataAdapter
from dotenv import load_dotenv
import os
import logging
import pandas as pd
try:
    from gm import api as gm
except ImportError:
    gm = None

from typing import Any, Dict, List, Optional
from .types import Asset, AssetPrice, AssetSearchQuery, AssetSearchResult, Exchange, AssetType,DataSource, Interval, LocalizedName, MarketInfo, MarketStatus

logger = logging.getLogger(__name__)
load_dotenv()

class MyQuantAdapter(BaseDataAdapter):

    def __init__(self, **kwargs):
        """Initialize AKShare adapter.

        Args:
            **kwargs: Additional configuration parameters
        """
        super().__init__(DataSource.MYQUANT, **kwargs)
        
        if gm is None:
            raise ImportError(
                "myquant is required. Install with: pip install gm"
            )
        
        token = os.getenv('MYQUANT_TOKEN')
        if token is None:
            raise ImportError(
                "myquant token is required. please register myquant's account and set token in .env"
            )
        
        gm.set_token(token) 

        self._initialize()
    
    def _initialize(self) -> None:
        self.exchange_mapping = {
            "SHSE": Exchange.SSE.value,  # Shanghai Stock Exchange
            "SZSE": Exchange.SZSE.value,  # Shenzhen Stock Exchange
            # "BJ": Exchange.BSE.value,  # Beijing Stock Exchange
        }

        self.exchange_prefix_mapping = {
            Exchange.SSE.value: "SHSE",
            Exchange.SZSE.value: "SZSE"
        }

        self.sector_mapping = {
            AssetType.STOCK: 1010,
            AssetType.INDEX: 1060
        }

        self.field_mappings = {
                "code": ["代码", "symbol", "ts_code"],
                "name": ["名称", "name", "short_name"],
                "price": ["最新价", "close", "price"],
                "open": ["今开", "开盘", "open"],
                "high": ["最高", "high"],
                "low": ["最低", "low"],
                "close": ["收盘", "close", "price"],
                "volume": ["成交量", "volume", "vol"],
                "amount": ["amount"],
                "market_cap": ["总市值", "total_mv"],
                "change": ["涨跌额", "change"],
                "change_percent": ["涨跌幅", "change_percent", "pct_chg"],
                "date": ["eob", "date", "created_at"],
                "time": ["eob", "time", "created_at"],
        }

    def _get_field_name(
        self, df: pd.DataFrame, field: str
    ) -> Optional[str]:
        """Get the actual field name from DataFrame based on exchange type.

        Args:
            df: DataFrame to search for field
            field: Standard field name (e.g., 'open', 'close', 'high')


        Returns:
            Actual field name found in DataFrame, or None if not found
        """
        # Get market type for field mapping
        # market = self._get_market_type(exchange)

        # Get possible field names for this field
        possible_names = self.field_mappings.get(field, [])

        # Check which field name exists in the DataFrame
        for name in possible_names:
            if name in df.columns:
                return name

        # If not found, try the standard field name directly
        if field in df.columns:
            return field

        return None

    def _get_field_names(self, df: pd.DataFrame) -> Dict[str, str]:

        return {
            'ticker' : self._get_field_name(df, "code"),
            # Use field mapping helper to get actual field names
            'time_field' : self._get_field_name(df, 'time'),
            'date_field' : self._get_field_name(df, 'date'),
            'pre_close_field' : self._get_field_name(df, 'pre_close'),
            'price_field' : self._get_field_name(df, 'price'),
            'open_field' : self._get_field_name(df, "open"),
            'close_field' : self._get_field_name(df, "close"),
            'high_field' : self._get_field_name(df, "high"),
            'low_field' : self._get_field_name(df, "low"),
            'volume_field' : self._get_field_name(df, "volume"),
            'amount_field' : self._get_field_name(df, "amount"),
            'change_field' : self._get_field_name(df, "change"),
            'change_pct_field' : self._get_field_name(df, "change_percent")
        }


    def get_capabilities(self) -> List[AdapterCapability]:
        """Get detailed capabilities of AKShare adapter.

        AKShare primarily supports Chinese and Hong Kong markets.

        Returns:
            List of capabilities describing supported asset types and exchanges
        """
        return [
            AdapterCapability(
                asset_type=AssetType.STOCK,
                exchanges={
                    Exchange.SSE,
                    Exchange.SZSE,
                    # Exchange.BSE
                },
            ),
            AdapterCapability(
                asset_type=AssetType.ETF,
                exchanges={
                    Exchange.SSE,
                    Exchange.SZSE,
                    # Exchange.BSE
                },
            ),
            AdapterCapability(
                asset_type=AssetType.INDEX,
                exchanges={
                    Exchange.SSE,
                    Exchange.SZSE,
                    # Exchange.BSE
                },
            ),
        ]


    def get_supported_asset_types(self) -> List[AssetType]:
        """Get asset types supported by Yahoo Finance."""
        return [
            AssetType.STOCK,
            AssetType.INDEX
        ]

    def search_assets(self, query: AssetSearchQuery) -> List[AssetSearchResult]:
        return []

    def convert_to_source_ticker(self, internal_ticker: str) -> str:
        try:
            exchange_enum, symbol = self._parse_internal_ticker(internal_ticker)
            if exchange_enum is None:
                return symbol

            # For both Index and Stock
            return f"{self.exchange_prefix_mapping[exchange_enum.value]}.{symbol}"
            
        except Exception as e:
            logger.error(
                f"Error: {e}'"
            )
            return internal_ticker

    def convert_to_internal_ticker(self, source_ticker: str, default_exchange: Optional[str] = None) -> str:
        """Convert data source ticker to internal format.
        Args:
            source_ticker: Ticker in data source format (e.g., "SZSE.000001", "SHSE.000001")
            default_exchange: Default exchange if cannot be determined from ticker
        Returns:
            Ticker in internal format (e.g., "NASDAQ:AAPL", "HKEX:00700", "SSE:600519")
        """
        # Handle Myquant prefixed formats like SZSE.000001, SHSE.000001
        if '.' in source_ticker:
            parts = source_ticker.split(".", 1)
            if len(parts) == 2:
                exchange_code, symbol = parts
                exchange = self.exchange_mapping[exchange_code]
                if exchange:
                    return f"{exchange}:{symbol}"

        # If default exchange is provided, use it
        if default_exchange:
            # Normalize default_exchange if it's an Exchange enum
            if isinstance(default_exchange, Exchange):
                exchange_value = default_exchange.value
            else:
                exchange_value = default_exchange
            return f"{exchange_value}:{source_ticker}"

         # Fallback: return with AKSHARE prefix if cannot determine exchange
        logger.warning(
            f"Cannot determine exchange for ticker '{source_ticker}', using MYQUANT as prefix"
        )
        return f"MYQUANT:{source_ticker}"

    def get_asset_info(self, ticker: str) -> Optional[Asset]:
        """Get detailed information about a specific asset.
        Args:
            ticker: Asset ticker in internal format (e.g., "SSE:601127", "HKEX:02097", "NASDAQ:NVDA")
        Returns:
            Asset information or None if not found
        """

        try:
            asset_type = self._check_asset_type(ticker)
            df = gm.get_symbol_infos(
                sec_type1 = self.sector_mapping[asset_type],
                symbols = self.convert_to_source_ticker(ticker)
            )
            
            if len(df) == 0 or df is None:
                logger.warning(f"No data found for ticker: {ticker}")
                return None

            return self._create_asset_from_info(ticker, asset_type, df[0])
        except Exception as e:
            logger.error(f"Error getting asset info for {ticker}: {e}", exc_info=True)
            return None

    def _create_asset_from_info(
        self, ticker: str, asset_type: AssetType, info_dict: Dict[str, Any]
    ) -> Optional[Asset]:
        """Create Asset object from info dictionary.
        Args:
            ticker: Asset ticker in internal format
            exchange: Exchange enum
            info_dict: Dictionary containing asset information
        Returns:
            Asset object or None if creation fails
        """
        try:
            # Create localized names
            localized_names = LocalizedName()
            country = "CN"
            currency = info_dict.get("currency", "CNY")
            timezone = "Asia/Shanghai"

            # Set Chinese and English names
            cn_name = info_dict.get(
                "sec_name", ""
            )
            en_name = info_dict.get(
                "sec_abbr", ""
            )

            if cn_name:
                localized_names.set_name("zh-Hans", cn_name)
                localized_names.set_name("zh-CN", cn_name)
            if en_name:
                localized_names.set_name("en-US", en_name)
                localized_names.set_name("en", en_name)

            # Use Chinese name as fallback if no English name
            if not en_name and cn_name:
                localized_names.set_name("en-US", cn_name)

            exchange, _ = self._parse_internal_ticker(ticker)

            # Create market info
            market_info = MarketInfo(
                exchange=exchange.value,
                country=country,
                currency=currency,
                timezone=timezone,
                market_status=MarketStatus.UNKNOWN,
            )

            # Create Asset object
            asset = Asset(
                ticker=ticker,
                asset_type=asset_type, 
                names=localized_names,
                market_info=market_info,
            )

            # Add source mapping for AKShare
            asset.set_source_ticker(
                DataSource.AKSHARE, self.convert_to_source_ticker(ticker)
            )

            #TODO: Save asset metadata to database
            return asset
        except Exception as e:
            logger.error(
                f"Error creating asset from info for {ticker}: {e}", exc_info=True
            )
            return None

    def get_historical_prices(
        self, 
        ticker: str, 
        start_date: datetime,
        end_date: datetime,
        interval: str = '1d'
    ) -> List[AssetPrice]:
        try:
            symbol = self.convert_to_source_ticker(ticker)
            
            interval_mapping = {
                # Minute intervals (intraday)
                f"1{Interval.MINUTE.value}": "60s",
                f"1{Interval.DAY.value}": "1d",
                f"{Interval.TICK.value}": "tick",
            }

            # Get the period value from mapping
            period = interval_mapping.get(interval)
            if not period:
                logger.warning(
                    f"Unsupported interval: {interval}. "
                    f"Supported intervals: {', '.join(interval_mapping.keys())}"
                )
                return []
            
            try:
                df = gm.history(
                    symbol = symbol,
                    frequency = period,
                    start_time = start_date,
                    end_time = end_date,
                    adjust = 1, # 0:bfq, 2:hfq
                    df = True

                )
            except Exception as e:
                    logger.error(
                        f"Error fetching myquant historical data for {symbol} with period {period}: {e}"
                    )
                    return []

            if df is None or df.empty:
                logger.warning(f"No historical data found for {ticker}")
                return []

            return self._convert_df_to_prices(df, ticker)


        except Exception as e:
            logger.error(
                f"Error getting historical prices for {ticker}: {e}", exc_info=True
            )
            return []
            

    def get_real_time_price(self, ticker: str) -> Optional[AssetPrice]:
        try:
            symbol = self.convert_to_source_ticker(ticker)
            try:
                df = gm.history_n(symbol, '60s', count = 1, df = True)
            except Exception as e:
                    logger.error(
                        f"Error fetching myquant stock real-time data for {symbol}: {e}"
                    )
                    return None
            
            if df is None or df.empty:
                logger.warning(f"No real-time data found for {ticker}")
                return None
            
            prices = self._convert_df_to_prices(df, ticker)
            if prices:
                return prices
            else:
                logger.warning(f"Failed to convert real-time data for {ticker}")
                return None
        
        except Exception as e:
            logger.error(
                f"Error getting real-time prices for {ticker}: {e}", exc_info=True
            )
            return None


    def _convert_df_to_prices(self, df, ticker: str) -> List[AssetPrice]:
        """Convert historical price DataFrame to list of AssetPrice objects.

        Args:
            df: DataFrame containing historical price data
            ticker: Asset ticker in internal format
            exchange: Exchange enum

        Returns:
            List of AssetPrice objects
        """

        prices = []

        try:
            currency = "CNY"
            field_names = self._get_field_names(df)

            # if not datetime_field or not close_field :
            #     logger.error(
            #         f"Missing required fields in DataFrame. date_field={date_field} or time_field={time_field}, close_field={close_field}"
            #     )
            #     return []
            
            for _, row in df.iterrows():
                try:
                    price = self._convert_row_to_price(row, field_names, currency = currency)
                    prices.append(price)

                except Exception as e:
                    logger.warning(f"Error converting row to AssetPrice: {e}")
                    continue
            return prices
        except Exception as e:
            logger.error(f"Error converting DataFrame to prices: {e}", exc_info=True)
            return []

