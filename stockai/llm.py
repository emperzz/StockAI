import logging
from typing import Dict, Optional

from langchain_core.language_models import BaseChatModel

from config import LLMSettings, Config


logger = logging.getLogger(__name__)


class LLM:
    """LLM 管理器：根据配置名称返回 LangChain 的 ChatModel 实例。

    约定：
    - 只负责模型实例化与缓存，不提供 ask/工具调用等封装
    - 使用 langchain_core.messages 体系（由上层节点自行构建消息）
    - 支持 openai / azure(openai 兼容) / ollama
    """

    _instances: Dict[str, "LLM"] = {}

    def __new__(cls, config_name: str = "default"):
        if config_name not in cls._instances:
            instance = super().__new__(cls)
            instance.__init__(config_name)
            cls._instances[config_name] = instance
        return cls._instances[config_name]

    def __init__(self, config_name: str = "default"):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        all_llm: Dict[str, LLMSettings] = Config().llm
        if not all_llm or config_name not in all_llm:
            # 回退到 default
            settings = all_llm.get("default") if all_llm else None
            if not settings:
                raise ValueError("未找到有效的 LLM 配置，请检查 config.toml 或环境变量。")
        else:
            settings = all_llm[config_name]

        self.settings: LLMSettings = settings
        self.model = None
        self._embeddings = None
        self.model = self._build_model_or_embeddings(settings)

    def _build_model_or_embeddings(self, s: LLMSettings):
        """根据配置构造对应的 LangChain ChatModel 或 Embeddings。"""
        api_type = (s.api_type or "openai").lower()

        # Ollama - 对话模型
        if api_type == "ollama":
            logger.info("使用 Ollama Chat 模型: %s", s.model)
            try:
                from langchain_ollama import ChatOllama
            except ModuleNotFoundError as e:
                raise ModuleNotFoundError(
                    "未安装 langchain-ollama，请安装以使用 Ollama: pip install langchain-ollama"
                ) from e
            return ChatOllama(model=s.model, temperature=s.temperature)

        # DeepSeek - 对话模型
        if api_type == "deepseek":
            logger.info("使用 DeepSeek Chat 模型: %s", s.model)
            try:
                from langchain_deepseek import ChatDeepSeek
            except ModuleNotFoundError as e:
                raise ModuleNotFoundError(
                    "未安装 langchain-deepseek，请安装: pip install langchain-deepseek"
                ) from e
            params = {"model": s.model, "temperature": s.temperature}
            if s.api_key:
                params["api_key"] = s.api_key
            if s.base_url:
                params["base_url"] = s.base_url
            return ChatDeepSeek(**params)

        # Kimi (Moonshot) - 对话模型
        if api_type == "kimi":
            logger.info("使用 Moonshot(Kimi) Chat 模型: %s", s.model)
            try:
                from langchain_community.chat_models.moonshot import MoonshotChat
            except ModuleNotFoundError as e:
                raise ModuleNotFoundError(
                    "未安装 langchain-community，请安装以使用 Kimi: pip install langchain-community"
                ) from e
            params = {"model": s.model, "temperature": s.temperature}
            if s.api_key:
                params["api_key"] = s.api_key
            if s.base_url:
                params["base_url"] = s.base_url
            return MoonshotChat(**params)

        # Embedding - 仅构建向量模型
        if api_type == "embedding":
            logger.info("使用 Ollama Embeddings 模型: %s", s.model)
            try:
                from langchain_ollama import OllamaEmbeddings
            except ModuleNotFoundError as e:
                raise ModuleNotFoundError(
                    "未安装 langchain-ollama，请安装以使用 Embeddings: pip install langchain-ollama"
                ) from e
            self._embeddings = OllamaEmbeddings(model=s.model)
            return None

        # OpenAI / Azure 统一用 ChatOpenAI，Azure 通过 base_url 和 api_version 兼容
        params = {
            "model": s.model,
            "temperature": s.temperature,
            "max_tokens": s.max_tokens,
        }
        if s.base_url:
            params["base_url"] = s.base_url
        if s.api_key:
            params["api_key"] = s.api_key
        if s.api_version:
            params["api_version"] = s.api_version

        logger.info("使用 OpenAI/Azure Chat 模型: %s (type=%s)", s.model, api_type)
        try:
            from langchain_openai import ChatOpenAI
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "未安装 langchain-openai，请安装以使用 OpenAI/Azure: pip install langchain-openai"
            ) from e
        return ChatOpenAI(**params)

    def get_model(self):
        """返回底层 LangChain ChatModel。"""
        if self.model is None:
            raise RuntimeError("当前 api_type 非对话模型或模型未初始化")
        return self.model

    def get_embeddings(self):
        """返回底层 Embeddings 模型。"""
        if self._embeddings is None:
            raise RuntimeError("当前 api_type 非 embedding 或向量模型未初始化")
        return self._embeddings

