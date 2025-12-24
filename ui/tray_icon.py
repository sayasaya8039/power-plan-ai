"""
トレイアイコンモジュール
システムトレイに常駐してクイックアクセスを提供
"""
from PyQt6.QtWidgets import (
    QSystemTrayIcon, QMenu, QApplication
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PyQt6.QtCore import pyqtSignal, QObject
import logging

logger = logging.getLogger(__name__)


class TrayIcon(QObject):
    """システムトレイアイコン"""

    # シグナル
    show_dashboard = pyqtSignal()
    plan_changed = pyqtSignal(str)  # プランGUID
    quit_app = pyqtSignal()

    # プランGUID
    PLAN_ULTIMATE = "e9a42b02-d5df-448d-aa00-03f14749eb61"
    PLAN_HIGH = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    PLAN_BALANCED = "381b4222-f694-41f0-9685-ff5bb260df2e"
    PLAN_SAVER = "a1841308-3541-4fab-bc81-f71556f20b4a"

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self._current_plan = ""
        self._battery_percent: int | None = None

        # トレイアイコン作成
        self.tray = QSystemTrayIcon(app)
        self.tray.setToolTip("Power Plan AI - 電源プラン最適化")

        # コンテキストメニュー作成
        self._create_menu()

        # アイコン設定
        self._update_icon()

        # クリックイベント
        self.tray.activated.connect(self._on_activated)

        self.tray.show()
        logger.info("トレイアイコン初期化完了")

    def _create_menu(self):
        """コンテキストメニュー作成"""
        self.menu = QMenu()

        # ダッシュボード表示
        self.action_dashboard = QAction("ダッシュボードを開く", self.menu)
        self.action_dashboard.triggered.connect(self.show_dashboard.emit)
        self.menu.addAction(self.action_dashboard)

        self.menu.addSeparator()

        # 電源プラン選択
        self.action_ultimate = QAction("究極のパフォーマンス", self.menu)
        self.action_ultimate.setCheckable(True)
        self.action_ultimate.triggered.connect(
            lambda: self.plan_changed.emit(self.PLAN_ULTIMATE)
        )
        self.menu.addAction(self.action_ultimate)

        self.action_high = QAction("高パフォーマンス", self.menu)
        self.action_high.setCheckable(True)
        self.action_high.triggered.connect(
            lambda: self.plan_changed.emit(self.PLAN_HIGH)
        )
        self.menu.addAction(self.action_high)

        self.action_balanced = QAction("バランス", self.menu)
        self.action_balanced.setCheckable(True)
        self.action_balanced.triggered.connect(
            lambda: self.plan_changed.emit(self.PLAN_BALANCED)
        )
        self.menu.addAction(self.action_balanced)

        self.action_saver = QAction("省電力", self.menu)
        self.action_saver.setCheckable(True)
        self.action_saver.triggered.connect(
            lambda: self.plan_changed.emit(self.PLAN_SAVER)
        )
        self.menu.addAction(self.action_saver)

        self.menu.addSeparator()

        # AI自動最適化トグル
        self.action_auto = QAction("AI自動最適化", self.menu)
        self.action_auto.setCheckable(True)
        self.action_auto.setChecked(True)
        self.menu.addAction(self.action_auto)

        self.menu.addSeparator()

        # 終了
        self.action_quit = QAction("終了", self.menu)
        self.action_quit.triggered.connect(self.quit_app.emit)
        self.menu.addAction(self.action_quit)

        self.tray.setContextMenu(self.menu)

    def _create_icon(self, plan: str, battery: int | None = None) -> QIcon:
        """動的アイコン生成"""
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))  # 透明背景

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # プランに応じた色
        if "究極" in plan or "Ultimate" in plan:
            color = QColor(255, 200, 50)  # 金色
            text = "U"
        elif "高パフォーマンス" in plan or "High" in plan:
            color = QColor(255, 100, 100)  # 赤
            text = "H"
        elif "省電力" in plan or "Saver" in plan:
            color = QColor(100, 200, 100)  # 緑
            text = "S"
        else:
            color = QColor(100, 150, 255)  # 青
            text = "B"

        # 円を描画
        painter.setBrush(color)
        painter.setPen(QColor(255, 255, 255))
        painter.drawEllipse(4, 4, size - 8, size - 8)

        # テキスト
        font = QFont("Arial", 28, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(pixmap.rect(), 0x0084, text)  # AlignCenter

        painter.end()

        return QIcon(pixmap)

    def _update_icon(self):
        """アイコンを更新"""
        icon = self._create_icon(self._current_plan, self._battery_percent)
        self.tray.setIcon(icon)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """トレイアイコンクリック時"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_dashboard.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # シングルクリック: メニュー表示
            pass

    def update_status(self, plan_name: str, battery: int | None = None):
        """ステータス更新"""
        self._current_plan = plan_name
        self._battery_percent = battery

        # メニューのチェック状態更新
        self.action_ultimate.setChecked("究極" in plan_name or "Ultimate" in plan_name)
        self.action_high.setChecked("高パフォーマンス" in plan_name or "High" in plan_name)
        self.action_balanced.setChecked("バランス" in plan_name or "Balanced" in plan_name)
        self.action_saver.setChecked("省電力" in plan_name or "Saver" in plan_name)

        # ツールチップ更新
        tooltip = f"Power Plan AI\n現在: {plan_name}"
        if battery is not None:
            tooltip += f"\nバッテリー: {battery}%"
        self.tray.setToolTip(tooltip)

        # アイコン更新
        self._update_icon()

    def show_notification(self, title: str, message: str):
        """通知を表示"""
        self.tray.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def is_auto_enabled(self) -> bool:
        """AI自動最適化が有効か"""
        return self.action_auto.isChecked()

    def hide(self):
        """トレイアイコンを非表示"""
        self.tray.hide()
