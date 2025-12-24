"""
システム監視モジュール
CPU、バッテリー、アクティブプロセスを監視
"""
import psutil
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class SystemStatus:
    """システム状態"""
    cpu_percent: float
    memory_percent: float
    battery_percent: Optional[int]
    is_charging: bool
    active_app: str
    timestamp: datetime


class SystemMonitor:
    """システム監視クラス"""
    
    def __init__(self):
        self._user32 = ctypes.windll.user32
        self._kernel32 = ctypes.windll.kernel32
    
    def get_cpu_usage(self) -> float:
        """CPU使用率を取得（%）"""
        return psutil.cpu_percent(interval=0.1)
    
    def get_memory_usage(self) -> float:
        """メモリ使用率を取得（%）"""
        return psutil.virtual_memory().percent
    
    def get_battery_info(self) -> tuple[Optional[int], bool]:
        """バッテリー情報を取得
        
        Returns:
            (バッテリー残量%, AC接続中か)
            デスクトップPCの場合は (None, True)
        """
        battery = psutil.sensors_battery()
        if battery is None:
            return None, True  # デスクトップPC
        return int(battery.percent), battery.power_plugged
    
    def get_foreground_window_process(self) -> str:
        """フォアグラウンドウィンドウのプロセス名を取得"""
        try:
            hwnd = self._user32.GetForegroundWindow()
            if not hwnd:
                return "unknown"
            
            # プロセスIDを取得
            pid = wintypes.DWORD()
            self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            
            if pid.value == 0:
                return "unknown"
            
            # プロセス名を取得
            try:
                process = psutil.Process(pid.value)
                return process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return "unknown"
                
        except Exception as e:
            logger.debug(f"フォアグラウンドプロセス取得エラー: {e}")
            return "unknown"
    
    def get_running_apps(self) -> list[str]:
        """実行中のアプリケーション一覧を取得"""
        apps = set()
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info["name"]
                if name and not name.startswith("svc"):
                    apps.add(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return sorted(apps)
    
    def get_system_status(self) -> SystemStatus:
        """現在のシステム状態を取得"""
        cpu = self.get_cpu_usage()
        memory = self.get_memory_usage()
        battery, charging = self.get_battery_info()
        active_app = self.get_foreground_window_process()
        
        return SystemStatus(
            cpu_percent=cpu,
            memory_percent=memory,
            battery_percent=battery,
            is_charging=charging,
            active_app=active_app,
            timestamp=datetime.now()
        )
    
    def is_heavy_load(self) -> bool:
        """高負荷状態かどうか判定"""
        cpu = self.get_cpu_usage()
        return cpu > 70.0
    
    def is_idle(self) -> bool:
        """アイドル状態かどうか判定"""
        cpu = self.get_cpu_usage()
        return cpu < 10.0


# 負荷の高いアプリのパターン
HEAVY_APPS = {
    # ゲーム
    "steam.exe", "steamwebhelper.exe",
    "epicgameslauncher.exe", "FortniteClient-Win64-Shipping.exe",
    # 動画編集
    "Premiere Pro.exe", "AfterFX.exe", "DaVinci Resolve.exe",
    # 3D/レンダリング
    "blender.exe", "maya.exe", "3dsmax.exe",
    # 開発
    "devenv.exe", "Code.exe", "rider64.exe",
    # ブラウザ（多タブ）
    "chrome.exe", "firefox.exe", "msedge.exe",
}

LIGHT_APPS = {
    # テキスト
    "notepad.exe", "notepad++.exe", "WINWORD.EXE",
    # メディア再生
    "wmplayer.exe", "vlc.exe",
    # システム
    "explorer.exe", "SearchHost.exe",
}


def categorize_app(app_name: str) -> str:
    """アプリをカテゴリ分類"""
    app_lower = app_name.lower()
    
    if app_lower in {a.lower() for a in HEAVY_APPS}:
        return "heavy"
    elif app_lower in {a.lower() for a in LIGHT_APPS}:
        return "light"
    else:
        return "normal"


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    monitor = SystemMonitor()
    
    status = monitor.get_system_status()
    print(f"CPU: {status.cpu_percent:.1f}%")
    print(f"メモリ: {status.memory_percent:.1f}%")
    print(f"バッテリー: {status.battery_percent}%" if status.battery_percent else "AC電源")
    print(f"充電中: {status.is_charging}")
    print(f"アクティブアプリ: {status.active_app}")
