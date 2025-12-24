"""
スタートアップマネージャー
Windowsのスタートアップ登録を管理
"""
import sys
import os
import winreg
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# レジストリキー
STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "PowerPlanAI"


class StartupManager:
    """Windowsスタートアップ管理クラス"""

    def __init__(self):
        self._exe_path = self._get_exe_path()

    def _get_exe_path(self) -> str:
        """実行ファイルのパスを取得"""
        if getattr(sys, 'frozen', False):
            # PyInstallerでビルドされた場合
            return sys.executable
        else:
            # 開発環境
            return str(Path(__file__).parent / "main.py")

    def is_registered(self) -> bool:
        """スタートアップに登録されているか確認"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                STARTUP_KEY,
                0,
                winreg.KEY_READ
            )
            try:
                value, _ = winreg.QueryValueEx(key, APP_NAME)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception as e:
            logger.error(f"スタートアップ確認エラー: {e}")
            return False

    def register(self) -> bool:
        """スタートアップに登録"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                STARTUP_KEY,
                0,
                winreg.KEY_SET_VALUE
            )
            # EXEの場合はそのまま、Pythonスクリプトの場合はpythonwを使用
            if self._exe_path.endswith('.exe'):
                value = f'"{self._exe_path}"'
            else:
                value = f'pythonw "{self._exe_path}"'
            
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, value)
            winreg.CloseKey(key)
            logger.info(f"スタートアップに登録: {value}")
            return True
        except Exception as e:
            logger.error(f"スタートアップ登録エラー: {e}")
            return False

    def unregister(self) -> bool:
        """スタートアップから削除"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                STARTUP_KEY,
                0,
                winreg.KEY_SET_VALUE
            )
            try:
                winreg.DeleteValue(key, APP_NAME)
                logger.info("スタートアップから削除")
            except FileNotFoundError:
                pass  # 既に削除されている
            winreg.CloseKey(key)
            return True
        except Exception as e:
            logger.error(f"スタートアップ削除エラー: {e}")
            return False

    def set_startup(self, enabled: bool) -> bool:
        """スタートアップ設定を変更"""
        if enabled:
            return self.register()
        else:
            return self.unregister()
