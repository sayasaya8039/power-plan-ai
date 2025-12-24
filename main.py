"""
Power Plan AI - メインアプリケーション
Windows電源プランをAIで自動最適化
"""
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# PyInstaller対応: モジュール検索パスを設定
if getattr(sys, 'frozen', False):
    # PyInstallerでビルドされた場合
    BASE_DIR = Path(sys._MEIPASS)
    # データファイルとして追加されたモジュールのパスを追加
    sys.path.insert(0, str(BASE_DIR))
    # 実行ファイルのディレクトリも追加
    EXE_DIR = Path(sys.executable).parent
    sys.path.insert(0, str(EXE_DIR))
else:
    # 開発環境
    BASE_DIR = Path(__file__).parent
    sys.path.insert(0, str(BASE_DIR))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from power_manager import PowerManager
from system_monitor import SystemMonitor
from database import Database, UsageRecord
from pattern_learner import SmartOptimizer
from ui.tray_icon import TrayIcon
from ui.dashboard import DashboardWindow

__version__ = "1.0.0"

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


class PowerPlanAI:
    """メインアプリケーションクラス"""

    def __init__(self):
        logger.info(f"Power Plan AI v{__version__} 起動中...")

        # Qt アプリケーション
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName("Power Plan AI")
        self.app.setApplicationVersion(__version__)

        # コンポーネント初期化
        self.power_manager = PowerManager()
        self.system_monitor = SystemMonitor()
        self.database = Database()
        self.optimizer = SmartOptimizer()

        # UI
        self.tray = TrayIcon(self.app)
        self.dashboard = DashboardWindow()

        # シグナル接続
        self._connect_signals()

        # 監視タイマー（30秒ごと）
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._on_monitor_tick)
        self.monitor_timer.start(30000)

        # 統計更新タイマー（1分ごと）
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_daily_stats)
        self.stats_timer.start(60000)

        # 初回更新
        self._on_monitor_tick()

        logger.info("初期化完了")

    def _connect_signals(self):
        """シグナルを接続"""
        # トレイアイコン
        self.tray.show_dashboard.connect(self._show_dashboard)
        self.tray.plan_changed.connect(self._on_plan_change_request)
        self.tray.quit_app.connect(self._quit)

        # ダッシュボード
        self.dashboard.plan_changed.connect(self._on_plan_change_request)

    def _show_dashboard(self):
        """ダッシュボードを表示"""
        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()

    def _on_plan_change_request(self, guid: str):
        """電源プラン変更リクエスト"""
        logger.info(f"プラン変更リクエスト: {guid}")

        # 究極のパフォーマンスは特別処理（名前でプランを検索）
        if guid == PowerManager.PLAN_ULTIMATE:
            success = self.power_manager.set_ultimate()
        else:
            success = self.power_manager.set_active_plan(guid)

        if success:
            plan = self.power_manager.get_active_plan()
            if plan:
                self.tray.show_notification(
                    "電源プラン変更",
                    f"{plan.name}に切り替えました"
                )

                # 学習に記録
                status = self.system_monitor.get_system_status()
                self.optimizer.record_choice(
                    hour=datetime.now().hour,
                    day_of_week=datetime.now().weekday(),
                    cpu_percent=status.cpu_percent,
                    memory_percent=status.memory_percent,
                    is_charging=status.is_charging,
                    active_app=status.active_app,
                    chosen_plan=plan.name
                )

            self._update_ui()

    def _on_monitor_tick(self):
        """監視タイマーのティック"""
        try:
            # システム状態取得
            status = self.system_monitor.get_system_status()
            plan = self.power_manager.get_active_plan()
            plan_name = plan.name if plan else "不明"

            # データベースに記録
            record = UsageRecord(
                id=None,
                timestamp=status.timestamp,
                hour=status.timestamp.hour,
                day_of_week=status.timestamp.weekday(),
                cpu_percent=status.cpu_percent,
                memory_percent=status.memory_percent,
                battery_percent=status.battery_percent,
                is_charging=status.is_charging,
                active_app=status.active_app,
                power_plan=plan_name
            )
            self.database.add_usage_record(record)

            # AI推奨取得
            prediction = self.optimizer.get_recommendation(
                hour=status.timestamp.hour,
                day_of_week=status.timestamp.weekday(),
                cpu_percent=status.cpu_percent,
                memory_percent=status.memory_percent,
                battery_percent=status.battery_percent,
                is_charging=status.is_charging,
                active_app=status.active_app
            )

            # 自動最適化が有効な場合
            if self.tray.is_auto_enabled():
                # 推奨プランが現在と異なり、信頼度が高い場合
                if prediction.recommended_plan != plan_name and prediction.confidence >= 0.7:
                    guid = self._plan_name_to_guid(prediction.recommended_plan)
                    if guid:
                        logger.info(f"AI自動切り替え: {prediction.recommended_plan}")
                        self.power_manager.set_active_plan(guid)
                        self.tray.show_notification(
                            "AI自動最適化",
                            f"{prediction.recommended_plan}に切り替えました\n{prediction.reason}"
                        )

            # UI更新
            self._update_ui()

        except Exception as e:
            logger.error(f"監視エラー: {e}", exc_info=True)

    def _update_ui(self):
        """UIを更新"""
        try:
            status = self.system_monitor.get_system_status()
            plan = self.power_manager.get_active_plan()
            plan_name = plan.name if plan else "不明"

            # トレイ更新
            self.tray.update_status(plan_name, status.battery_percent)

            # ダッシュボード更新
            self.dashboard.update_status(
                plan_name=plan_name,
                battery=status.battery_percent,
                cpu=status.cpu_percent,
                is_charging=status.is_charging
            )

            # AI推奨
            prediction = self.optimizer.get_recommendation(
                hour=datetime.now().hour,
                day_of_week=datetime.now().weekday(),
                cpu_percent=status.cpu_percent,
                memory_percent=status.memory_percent,
                battery_percent=status.battery_percent,
                is_charging=status.is_charging,
                active_app=status.active_app
            )
            self.dashboard.update_ai_recommendation(
                prediction.recommended_plan,
                prediction.confidence,
                prediction.reason
            )

            # 統計
            stats = self.database.get_today_stats()
            self.dashboard.update_stats(stats)

        except Exception as e:
            logger.error(f"UI更新エラー: {e}")

    def _update_daily_stats(self):
        """日次統計を更新"""
        try:
            plan = self.power_manager.get_active_plan()
            if plan:
                self.database.update_daily_stats(plan.name)
        except Exception as e:
            logger.error(f"統計更新エラー: {e}")

    def _plan_name_to_guid(self, name: str) -> str | None:
        """プラン名からGUIDを取得"""
        if "究極" in name or "Ultimate" in name:
            return PowerManager.PLAN_ULTIMATE
        elif "高パフォーマンス" in name or "High" in name:
            return PowerManager.PLAN_HIGH_PERFORMANCE
        elif "省電力" in name or "Saver" in name:
            return PowerManager.PLAN_POWER_SAVER
        elif "バランス" in name or "Balanced" in name:
            return PowerManager.PLAN_BALANCED
        return None

    def _quit(self):
        """アプリケーション終了"""
        logger.info("終了中...")
        self.monitor_timer.stop()
        self.stats_timer.stop()
        self.tray.hide()
        self.dashboard.close()
        self.app.quit()

    def run(self) -> int:
        """アプリケーション実行"""
        logger.info("アプリケーション開始")
        return self.app.exec()


def main():
    """エントリーポイント"""
    try:
        app = PowerPlanAI()
        sys.exit(app.run())
    except Exception as e:
        logger.critical(f"致命的エラー: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
