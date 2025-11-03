import json
import logging
import os
import threading
from typing import Dict, List, Optional
from .akshare_adapter import AKShareAdapter
from .myquant_adapters import MyQuantAdapter
from .base import BaseDataAdapter
from .types import DataSource, Exchange, AssetType


logger = logging.getLogger(__name__)

class AdapterManager:
    """Manager for coordinating multiple asset data adapters."""

    def __init__(self):
        self.adapters: Dict[DataSource, BaseDataAdapter] = {}

        # Keys are Exchange.value strings for efficient lookup
        self.exchange_routing: Dict[str, List[BaseDataAdapter]] = {}

        # Ticker -> Adapter cache for fast lookup
        self._ticker_cache: Dict[str, BaseDataAdapter] = {}
        self._cache_lock = threading.Lock()
        self.lock = threading.RLock()

        logger.info("Asset adapter manager initialized")
    

    def _rebuild_routing_table(self) -> None:
        """Rebuild routing table based on registered adapters' capabilities.

        Simplified: Only use exchange to determine adapter routing.
        """

        with self.lock:
            self.exchange_routing.clear()

            # Build routing table: Exchange -> List[Adapters]
            for adapter in self.adapters.values():
                capabilities = adapter.get_capabilities()

                # Get all exchanges supported by this adapter(across all asset types)
                supported_exchanges = set() 
                # Note: Adaptercapability(asset type, exchanges)
                for cap in capabilities:
                    for exchange in cap.exchanges:
                        exchange_key = (
                            exchange.value 
                            if isinstance(exchange, Exchange)
                            else exchange
                        )
                        supported_exchanges.add(exchange_key)

                # Register adapter for each supported exchange
                for exchange_key in supported_exchanges:
                    if exchange_key not in self.exchange_routing:
                        self.exchange_routing[exchange_key] = []
                    self.exchange_routing[exchange_key].append(adapter)

            # Clear ticker cache when routing table changes
            with self._cache_lock:
                self._ticker_cache.clear()

            logger.debug(
                f"Routing table rebuilt with {len(self.exchange_routing)} exchanges"
            )

    def register_adapter(self, adapter: BaseDataAdapter) -> None:
        """Register a data adapter and rebuild routing table.

        Args:
            adapter: Data adapter instance to register
        """

        with self.lock:
            self.adapters[adapter.source] = adapter
            self._rebuild_routing_table()
            logger.info(f"Registered adapter: {adapter.source.value}")

    def config_akshare(self, **kwargs) -> None:
        """Configure and register AKShare adapter.

        Args:
            **kwargs: Additional configuration
        """
        try:
            adapter = AKShareAdapter(**kwargs)
            self.register_adapter(adapter)
        except Exception as e:
            logger.error(f"Failed to configure AKShare adapter: {e}")

    def config_myquant(self, **kwargs) -> None:
        """Configure and register myquant adapter.

        Args:
            **kwargs: Additional configuration
        """
        try:
            adapter = MyQuantAdapter(**kwargs)
            self.register_adapter(adapter)
        except Exception as e:
            logger.error(f"Failed to configure MyQuant adapter: {e}")

    def get_available_adapters(self) -> List[DataSource]:
        """Get list of available data adapters."""
        with self.lock:
            return list(self.adapters.keys())
    
    def get_adapters_for_exchange(self, exchange: str) -> List[BaseDataAdapter]:
        """Get list of adapters for a specific exchange.

        Args:
            exchange: Exchange identifier (e.g., "NASDAQ", "SSE")

        Returns:
            List of adapters that support the exchange
        """
        with self.lock:
            return self.exchange_routing.get(exchange, [])

    def get_adapters_for_asset_type(self, asset_type: AssetType) -> List[BaseDataAdapter]:
        """Get list of adapters that support a specific asset type.

        Note: This collects adapters across all exchanges. Consider using
        get_adapters_for_exchange() for more specific routing.

        Args:
            asset_type: Type of asset

        Returns:
            List of adapters that support this asset type
        """

        with self.lock:
            supporting_adapters = set()
            for adapter in self.adapters.values():
                supported_types = adapter.get_supported_asset_types()
                if asset_type in supported_types:
                    supporting_adapters.add(adapter)

            return list(supporting_adapters)

    def get_adapter_for_ticker(self, ticker: str) -> Optional[BaseDataAdapter]:
        """Get the best adapter for a specific ticker (with caching).

        Simplified: Only based on exchange, first adapter that validates wins.

        Args:
            ticker: Asset ticker in internal format (e.g., "NASDAQ:AAPL")

        Returns:
            Best available adapter for the ticker or None if not found
        """

        with self._cache_lock:
            if ticker in self._ticker_cache:
                return self._ticker_cache[ticker]

        exchange, symbol = ticker.split(':', 1)

        adapters = self.get_adapters_for_exchange(exchange)

        if not adapters:
            logger.debug(f"No adapters registered for exchange: {exchange}")
            return None

        # Find first adapter that validates this ticker
        for adapter in adapters:
            if adapter.validate_ticker(ticker):
                with self._cache_lock:
                    self._ticker_cache[ticker] = adapter
                logger.debug(f"Matched adapter {adapter.source.value} for {ticker}")
                return adapter

        logger.warning(f"No suitable adapter found for ticker: {ticker}")
        return None
