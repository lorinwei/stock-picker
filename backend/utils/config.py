"""
统一配置模块 — 解决所有硬编码路径 + 平台自适应
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict

import yaml


class Settings:
    """全局配置 — 所有路径相对于项目根目录自动解析"""

    def __init__(self):
        # ── 项目根目录 ──────────────────────────────
        # 向上找到 backend/ 所在目录 = 项目根
        self.PROJECT_ROOT = self._find_project_root()
        self.BACKEND_DIR = self.PROJECT_ROOT / "backend"
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.LOGS_DIR = self.DATA_DIR / "logs"
        self.BACKTEST_DIR = self.DATA_DIR / "backtest_results"

        # ── 加载 yaml 配置 ──────────────────────────
        cfg_path = self.BACKEND_DIR / "config.yaml"
        self._cfg: Dict[str, Any] = {}
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                self._cfg = yaml.safe_load(f) or {}

        # 确保目录存在
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.BACKTEST_DIR.mkdir(parents=True, exist_ok=True)

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @staticmethod
    def _find_project_root() -> Path:
        """向上查找包含 backend/ 的目录作为项目根"""
        # 期望位置: <root>/backend/utils/config.py
        guess = Path(__file__).resolve().parent.parent.parent
        if (guess / "backend").is_dir() or (guess / "data").is_dir():
            return guess
        # fallback: CWD
        return Path.cwd().resolve()

    # ── 数据库 ────────────────────────────────────
    @property
    def DB_PATH(self) -> str:
        return str(self.DATA_DIR / "stockmind.db")

    # ── 日志 ──────────────────────────────────────
    @property
    def LOG_FILE(self) -> str:
        return str(self.LOGS_DIR / "app.log")

    # ── App ───────────────────────────────────────
    @property
    def APP_NAME(self) -> str:
        return self._cfg.get("app", {}).get("name", "StockMind")

    @property
    def APP_VERSION(self) -> str:
        return self._cfg.get("app", {}).get("version", "3.0.0")

    @property
    def DEBUG(self) -> bool:
        return self._cfg.get("app", {}).get("debug", True)

    @property
    def HOST(self) -> str:
        return self._cfg.get("app", {}).get("host", "0.0.0.0")

    @property
    def PORT(self) -> int:
        return self._cfg.get("app", {}).get("port", 8000)

    # ── 组合配置 ────────────────────────────────
    @property
    def PICKER(self) -> dict:
        return self._cfg.get("picker", {})

    @property
    def RISK(self) -> dict:
        return self._cfg.get("risk", {})

    @property
    def PORTFOLIO_CFG(self) -> dict:
        return self._cfg.get("portfolio", {})

    @property
    def BACKTEST(self) -> dict:
        return self._cfg.get("backtest", {})

    @property
    def AI_CFG(self) -> dict:
        return self._cfg.get("ai", {})

    @property
    def FEISHU(self) -> dict:
        return self._cfg.get("feishu", {})

    @property
    def CACHE(self) -> dict:
        return self._cfg.get("cache", {})

    @property
    def LOG_LEVEL(self) -> str:
        return self._cfg.get("logging", {}).get("level", "INFO")

    def get(self, key: str, default=None):
        """通用取值，支持点号路径如 'ai.minimax.api_key' """
        parts = key.split(".")
        val = self._cfg
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                return default
        return val if val is not None else default


settings = Settings()
