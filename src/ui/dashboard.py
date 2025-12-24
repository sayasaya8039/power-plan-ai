"""
ダッシュボードウィンドウ
メインのユーザーインターフェース
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QProgressBar,
    QGroupBox, QGridLayout, QScrollArea
)
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
import logging

logger = logging.getLogger(__name__)


class StatusCard(QFrame):
    """ステータスカード"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            StatusCard {
                background-color: #2d2d2d;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)

        # タイトル
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.title_label)

        # 値
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.value_label)

        # サブテキスト
        self.sub_label = QLabel("")
        self.sub_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.sub_label)

    def set_value(self, value: str, sub: str = ""):
        """値を設定"""
        self.value_label.setText(value)
        self.sub_label.setText(sub)


class PlanButton(QPushButton):
    """電源プラン選択ボタン"""

    def __init__(self, text: str, color: str, parent=None):
        super().__init__(text, parent)
        self._color = color
        self._active = False
        self._update_style()

    def _update_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._color};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 15px 20px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #3d3d3d;
                    color: #aaa;
                    border: 2px solid #555;
                    border-radius: 8px;
                    padding: 15px 20px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: #4d4d4d;
                    border-color: {self._color};
                }}
            """)

    def set_active(self, active: bool):
        self._active = active
        self._update_style()


class DashboardWindow(QMainWindow):
    """ダッシュボードウィンドウ"""

    plan_changed = pyqtSignal(str)  # プランGUID

    PLAN_HIGH = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    PLAN_BALANCED = "381b4222-f694-41f0-9685-ff5bb260df2e"
    PLAN_SAVER = "a1841308-3541-4fab-bc81-f71556f20b4a"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Power Plan AI - ダッシュボード")
        self.setMinimumSize(500, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: white;
            }
            QGroupBox {
                color: white;
                border: 1px solid #444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        self._setup_ui()

    def _setup_ui(self):
        """UIをセットアップ"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ヘッダー
        header = QLabel("⚡ Power Plan AI")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #4fc3f7;")
        main_layout.addWidget(header)

        subtitle = QLabel("AIが最適な電源プランを自動選択します")
        subtitle.setStyleSheet("color: #888; font-size: 12px;")
        main_layout.addWidget(subtitle)

        # ステータスカード
        cards_layout = QHBoxLayout()

        self.card_plan = StatusCard("現在のプラン")
        cards_layout.addWidget(self.card_plan)

        self.card_battery = StatusCard("バッテリー")
        cards_layout.addWidget(self.card_battery)

        self.card_cpu = StatusCard("CPU使用率")
        cards_layout.addWidget(self.card_cpu)

        main_layout.addLayout(cards_layout)

        # 電源プラン選択
        plan_group = QGroupBox("電源プラン")
        plan_layout = QHBoxLayout(plan_group)

        self.btn_high = PlanButton("🚀 高パフォーマンス", "#e74c3c")
        self.btn_high.clicked.connect(lambda: self.plan_changed.emit(self.PLAN_HIGH))
        plan_layout.addWidget(self.btn_high)

        self.btn_balanced = PlanButton("⚖️ バランス", "#3498db")
        self.btn_balanced.clicked.connect(lambda: self.plan_changed.emit(self.PLAN_BALANCED))
        plan_layout.addWidget(self.btn_balanced)

        self.btn_saver = PlanButton("🔋 省電力", "#27ae60")
        self.btn_saver.clicked.connect(lambda: self.plan_changed.emit(self.PLAN_SAVER))
        plan_layout.addWidget(self.btn_saver)

        main_layout.addWidget(plan_group)

        # AI推奨
        self.ai_group = QGroupBox("AI推奨")
        ai_layout = QVBoxLayout(self.ai_group)

        self.ai_recommendation = QLabel("分析中...")
        self.ai_recommendation.setStyleSheet("font-size: 14px;")
        self.ai_recommendation.setWordWrap(True)
        ai_layout.addWidget(self.ai_recommendation)

        self.ai_confidence = QProgressBar()
        self.ai_confidence.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 5px;
                text-align: center;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #4fc3f7;
                border-radius: 4px;
            }
        """)
        self.ai_confidence.setFormat("信頼度: %p%")
        ai_layout.addWidget(self.ai_confidence)

        main_layout.addWidget(self.ai_group)

        # 今日の統計
        stats_group = QGroupBox("今日の統計")
        stats_layout = QGridLayout(stats_group)

        self.stat_total = QLabel("総稼働時間: --分")
        stats_layout.addWidget(self.stat_total, 0, 0)

        self.stat_high = QLabel("高パフォーマンス: --分")
        stats_layout.addWidget(self.stat_high, 0, 1)

        self.stat_balanced = QLabel("バランス: --分")
        stats_layout.addWidget(self.stat_balanced, 1, 0)

        self.stat_saver = QLabel("省電力: --分")
        stats_layout.addWidget(self.stat_saver, 1, 1)

        main_layout.addWidget(stats_group)

        # スペーサー
        main_layout.addStretch()

        # フッター
        footer = QLabel("© 2024 Power Plan AI - ローカル処理・プライバシー保護")
        footer.setStyleSheet("color: #555; font-size: 10px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer)

    def update_status(
        self,
        plan_name: str,
        battery: int | None,
        cpu: float,
        is_charging: bool
    ):
        """ステータスを更新"""
        # プラン
        self.card_plan.set_value(plan_name)

        # バッテリー
        if battery is not None:
            status = "充電中" if is_charging else "バッテリー"
            self.card_battery.set_value(f"{battery}%", status)
        else:
            self.card_battery.set_value("AC電源", "デスクトップPC")

        # CPU
        self.card_cpu.set_value(f"{cpu:.0f}%")

        # プランボタンの状態更新
        self.btn_high.set_active("高パフォーマンス" in plan_name or "High" in plan_name)
        self.btn_balanced.set_active("バランス" in plan_name or "Balanced" in plan_name)
        self.btn_saver.set_active("省電力" in plan_name or "Saver" in plan_name)

    def update_ai_recommendation(self, plan: str, confidence: float, reason: str):
        """AI推奨を更新"""
        self.ai_recommendation.setText(f"推奨: {plan}\n理由: {reason}")
        self.ai_confidence.setValue(int(confidence * 100))

    def update_stats(self, stats: dict):
        """統計を更新"""
        self.stat_total.setText(f"総稼働時間: {stats.get('total_minutes', 0)}分")
        self.stat_high.setText(f"高パフォーマンス: {stats.get('high_perf_minutes', 0)}分")
        self.stat_balanced.setText(f"バランス: {stats.get('balanced_minutes', 0)}分")
        self.stat_saver.setText(f"省電力: {stats.get('power_saver_minutes', 0)}分")

    def closeEvent(self, event):
        """閉じるボタンでは非表示にする"""
        event.ignore()
        self.hide()
