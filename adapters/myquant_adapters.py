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

from typing import Any, Dict, List, Optional, Union
from .types import AdapterMethod, Asset, AssetPrice, AssetSearchQuery, AssetSearchResult, Exchange, AssetType,DataSource, Interval, LocalizedName, MarketInfo, MarketStatus

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
            'BK': Exchange.BK.value
        }

        self.exchange_prefix_mapping = {
            Exchange.SSE.value: "SHSE",
            Exchange.SZSE.value: "SZSE",
            Exchange.BK.value : 'BK'
        }

        self.sector_mapping = {
            AssetType.STOCK: 1010,
            AssetType.INDEX: 1060,
            AssetType.BK: 1070
        }

        self.field_mappings = {
                "code": ["代码", "symbol", "ts_code"],
                "name": ["名称", "name", "short_name"],
                "price": ["最新价", "close", "price"],
                "open": ["今开", "开盘", "open"],
                "high": ["最高", "high"],
                "low": ["最低", "low"],
                "close": ["收盘", "close", "price"],
                "pre_close": ["pre_close"],
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
                methods = {
                    AdapterMethod.GET_HISTORICAL_PRICES,
                    AdapterMethod.GET_REAL_TIME_PRICE,
                },
                method_priorities= {
                    AdapterMethod.GET_HISTORICAL_PRICES: 1,
                    AdapterMethod.GET_REAL_TIME_PRICE: 2
                }
            ),
            AdapterCapability(
                asset_type=AssetType.INDEX,
                exchanges={
                    Exchange.SSE,
                    Exchange.SZSE,
                    # Exchange.BSE
                },
                methods = {
                    AdapterMethod.GET_HISTORICAL_PRICES,
                    AdapterMethod.GET_REAL_TIME_PRICE,
                },
                method_priorities= {
                    AdapterMethod.GET_HISTORICAL_PRICES: 1,
                    AdapterMethod.GET_REAL_TIME_PRICE: 2
                }
            ),
        ]


    def get_supported_asset_types(self) -> List[AssetType]:
        """Get asset types supported by Yahoo Finance."""
        return [
            AssetType.STOCK,
            AssetType.INDEX,
            AssetType.BK
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
            # df = gm.get_symbol_infos(
            #     sec_type1 = self.sector_mapping[asset_type],
            #     symbols = self.convert_to_source_ticker(ticker)
            # )
            
            # if len(df) == 0 or df is None:
            #     logger.warning(f"No data found for ticker: {ticker}")
            #     return None

            # return self._create_asset_from_info(ticker, asset_type, df[0])
            return self._get_symbol_list(
                sec_type1 = self.sector_mapping[asset_type],
                symbols = self.convert_to_source_ticker(ticker)
            )[0]
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
                f"15{Interval.MINUTE.value}": "15m",
                f"30{Interval.MINUTE.value}": "30m",
                f"60{Interval.MINUTE.value}": "60m",
                f"1{Interval.MONTH.value}": "1m",
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
                df = gm.history_n(symbol, frequency='1d', count = 1, df = True)
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
            
            # manually calculate change fields 
            if field_names['change_field'] is None or field_names['change_pct_field'] is None:
                if field_names['pre_close_field']:
                    df['change_field'] = round(df[field_names['close_field']] - df[field_names['pre_close_field']],2)
                    df['change_percent'] = round(df.change_field/df[field_names['pre_close_field']]*100,2)
                    
                    field_names['change_field'] = 'change_field'
                    field_names['change_pct_field'] = 'change_percent'

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

    

    def get_bk_list(self) -> List[Asset]:
        """Get list of BK 
        """

        return self._get_symbol_list(sec_type1 = 1070)

    def get_index_list(self) -> List[Asset]:

        return self._get_symbol_list(sec_type1 = 1060, sec_type2 = 106001)

    def _get_symbol_list(
        self, 
        sec_type1: Optional[int], 
        sec_type2: Optional[int] = None,
        symbols: Optional[Union[List, str]] = None,
        exchanges: Optional[Union[List, str]] = None,
        df: bool = True
    ) -> List[Asset]:
        """Get list of indexs according to exchange

        Args:
            sec_type1: 1010: 股票， 1020: 基金， 1030: 债券 ， 1040: 期货， 1050: 期权， 1060: 指数，1070：板块.
            sec_type2: 股票 101001:A 股，101002:B 股，101003:存托凭证 - 基金 102001:ETF，102002:LOF，102005:FOF，102009:基础设施REITs - 债券 103001:可转债，103008:回购 - 期货 104001:股指期货，104003:商品期货，104006:国债期货 - 期权 105001:股票期权，105002:指数期权，105003:商品期权 - 指数 106001:股票指数，106002:基金指数，106003:债券指数，106004:期货指数 - 板块：107001:概念板块
            symbols: e.g. 'SHSE.600008' or 'SHSE.600008,SZSE.000002' or ['SHSE.600008', 'SZSE.000002']
            exchange: SHSE:上海证券交易所，SZSE:深圳证券交易所 ， CFFEX:中金所，SHFE:上期所，DCE:大商所， CZCE:郑商所， INE:上海国际能源交易中心 ，GFEX:广期所. e.g ['SHSE', 'SZSE'] or 'SHSE,SZSE'
            df: whether return dataframe or list
        Returns:

        """
        if sec_type2:
            if str(sec_type2)[:4] != str(sec_type1):
                logger.warning('first 4 digts of sec_type2 must equal sec_type1, current inputs are sec_type1 = {sec_type1} and sec_type2 = {sec_type2}')
                return []

        try:
            df = gm.get_symbol_infos(sec_type1 = sec_type1, sec_type2=sec_type2,  symbols=symbols, df=df, exchanges = exchanges)
        except Exception as e:
            logger.error(f'Error fetching list of sec_type1 = {sec_type1} and sec_type2 = {sec_type2}')
            return []

        assets = []
        for _, row in df.iterrows():
            ticker = self.convert_to_internal_ticker(row.symbol)
            assets.append(self._create_asset_from_info(ticker, AssetType.BK, row))

        if assets:
            return assets
        else:
            logger.warning(f"Got empty data from sec_type1:{sec_type1}, sec_type2:{sec_type2}, symbols:{symbols}, exchanges:{exchanges}")
            return []

    