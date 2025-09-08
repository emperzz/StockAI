import os
import threading
from pathlib import Path
from typing import Dict, Optional

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    import tomli as tomllib  # type: ignore

from pydantic import BaseModel, Field


def get_project_root() -> Path:
    """获取项目根目录（当前文件所在目录的上级）。"""
    return Path(__file__).resolve().parent


class LLMSettings(BaseModel):
    """LLM 配置项。只保留必须字段，简化管理。"""
    model: str = Field(..., description="模型名称")
    base_url: Optional[str] = Field(None, description="API Base URL")
    api_key: Optional[str] = Field(None, description="API Key（可为空，走本地/无鉴权方案）")
    max_tokens: int = Field(4096, description="最大输出tokens")
    temperature: float = Field(1.0, description="采样温度")
    api_type: str = Field("openai", description="后端类型: openai/azure/ollama")
    api_version: Optional[str] = Field(None, description="Azure OpenAI 版本（仅azure需要）")

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 数据库配置
    # 使用相对路径，让 Flask 自动管理 instance 目录
    SQLALCHEMY_DATABASE_URI = 'sqlite:///summa.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 文件上传配置
    UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB最大文件大小
    ALLOWED_EXTENSIONS = {'txt', 'md', 'pdf', 'jpg', 'jpeg', 'png', 'gif'}
    
    # 确保上传目录存在
    UPLOAD_FOLDER.mkdir(exist_ok=True)

    # 配置 DeepSeek API 密钥
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
    DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')
    MAX_TEXT_LENGTH = int(os.environ.get('MAX_TEXT_LENGTH', 4000))
    DEEPSEEK_URL = os.environ.get('DEEPSEEK_URL', 'https://api.deepseek.com')
    
    # 配置豆包视觉模型
    ARK_API_KEY = os.environ.get('ARK_API_KEY')
    DOUBAO_MODEL = os.environ.get('DOUBAO_MODEL', '')
    DOUBAO_URL = os.environ.get('DOUBAO_URL', '')
    
    # RAG系统配置
    # Ollama服务配置
    EMBEDDING_URL = os.environ.get('EMBEDDING_URL', 'http://localhost:11434')
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'bge-large:335m')
    EMBEDDING_TIMEOUT = int(os.environ.get('EMBEDDING_TIMEOUT', 30))
    
    # 文档处理配置
    RAG_CHUNK_SIZE = int(os.environ.get('RAG_CHUNK_SIZE', 1000))  # 文本块大小
    RAG_CHUNK_OVERLAP = int(os.environ.get('RAG_CHUNK_OVERLAP', 200))  # 文本块重叠
    
    # 检索配置
    RAG_TOP_K = int(os.environ.get('RAG_TOP_K', 5))  # 默认检索数量
    RAG_SCORE_THRESHOLD = float(os.environ.get('RAG_SCORE_THRESHOLD', 0.1))  # 相似度阈值
    
    
    TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')
    BAIDU_API_KEY = os.environ.get('BAIDU_API_KEY')
    
    
    # -------------------- LLM 配置（新增） --------------------
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    _llm: Optional[Dict[str, LLMSettings]] = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    # 延迟加载 LLM 配置
                    try:
                        self._llm = self._load_llm_config()
                    except Exception:
                        self._llm = {}
                    self._initialized = True

    @staticmethod
    def _get_config_path() -> Path:
        """优先使用根目录 config.toml，不存在则使用 config_example.toml。"""
        root = get_project_root()
        primary = root / "config.toml"
        example = root / "config_example.toml"
        if primary.exists():
            return primary
        if example.exists():
            return example
        # 都不存在则返回一个无效路径，上层捕获异常
        return primary

    def _load_llm_config(self) -> Dict[str, LLMSettings]:
        path = self._get_config_path()
        if not path.exists():
            return {}
        with path.open("rb") as f:
            raw = tomllib.load(f)

        # 读取 llm 根配置（default）与命名覆盖
        llm_root = raw.get("llm", {})
        base = {
            "model": llm_root.get("model"),
            "base_url": llm_root.get("base_url"),
            "api_key": llm_root.get("api_key"),
            "max_tokens": llm_root.get("max_tokens", 4096),
            "temperature": llm_root.get("temperature", 1.0),
            "api_type": llm_root.get("api_type", "openai"),
            "api_version": llm_root.get("api_version"),
        }

        # 收集命名配置（default 以及其他 profile）
        result: Dict[str, LLMSettings] = {}
        # default 作为基础 profile
        if base.get("model"):
            result["default"] = LLMSettings(**base)

        # 其余覆盖项（llm 下的子字典）
        for name, value in llm_root.items():
            if isinstance(value, dict):
                merged = {**base, **value}
                # 需要至少包含 model 才认为有效
                if merged.get("model"):
                    result[name] = LLMSettings(**merged)

        return result

    @property
    def llm(self) -> Dict[str, LLMSettings]:
        """返回所有可用的 LLM 配置（按名称索引）。"""
        return self._llm or {}
