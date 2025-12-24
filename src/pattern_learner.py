"""
AI学習モジュール
使用パターンを学習して最適な電源プランを提案
"""
import pickle
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import logging
import os

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    """予測結果"""
    recommended_plan: str
    confidence: float
    reason: str


class PatternLearner:
    """使用パターン学習・予測クラス"""

    # 電源プランのラベル
    PLAN_HIGH = "高パフォーマンス"
    PLAN_BALANCED = "バランス"
    PLAN_SAVER = "省電力"

    # 負荷の高いアプリ
    HEAVY_APPS = {
        "steam.exe", "steamwebhelper.exe", "epicgameslauncher.exe",
        "premiere pro.exe", "afterfx.exe", "davinci resolve.exe",
        "blender.exe", "maya.exe", "3dsmax.exe",
        "devenv.exe", "rider64.exe",
    }

    # 軽いアプリ
    LIGHT_APPS = {
        "notepad.exe", "notepad++.exe", "winword.exe",
        "wmplayer.exe", "vlc.exe", "spotify.exe",
        "explorer.exe", "searchhost.exe",
    }

    def __init__(self, model_path: Optional[Path] = None):
        if model_path is None:
            app_data = Path(os.environ.get("APPDATA", "."))
            self.model_path = app_data / "PowerPlanAI" / "model.pkl"
        else:
            self.model_path = model_path

        self.model_path.parent.mkdir(parents=True, exist_ok=True)

        # 学習データ
        self._patterns: list[dict] = []
        self._load_model()

    def _load_model(self):
        """モデルを読み込み"""
        if self.model_path.exists():
            try:
                with open(self.model_path, "rb") as f:
                    self._patterns = pickle.load(f)
                logger.info(f"モデル読み込み: {len(self._patterns)}パターン")
            except Exception as e:
                logger.warning(f"モデル読み込みエラー: {e}")
                self._patterns = []

    def _save_model(self):
        """モデルを保存"""
        try:
            with open(self.model_path, "wb") as f:
                pickle.dump(self._patterns, f)
            logger.debug("モデル保存完了")
        except Exception as e:
            logger.error(f"モデル保存エラー: {e}")

    def add_pattern(
        self,
        hour: int,
        day_of_week: int,
        cpu_percent: float,
        memory_percent: float,
        is_charging: bool,
        active_app: str,
        chosen_plan: str
    ):
        """学習パターンを追加"""
        pattern = {
            "hour": hour,
            "day_of_week": day_of_week,
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "is_charging": is_charging,
            "active_app": active_app.lower(),
            "chosen_plan": chosen_plan,
            "timestamp": datetime.now().isoformat()
        }

        self._patterns.append(pattern)

        # 最大1000パターンを保持
        if len(self._patterns) > 1000:
            self._patterns = self._patterns[-1000:]

        self._save_model()

    def predict(
        self,
        hour: int,
        day_of_week: int,
        cpu_percent: float,
        memory_percent: float,
        battery_percent: Optional[int],
        is_charging: bool,
        active_app: str
    ) -> Prediction:
        """最適な電源プランを予測"""
        app_lower = active_app.lower()

        # ルールベースの判定（優先）

        # 1. バッテリー残量が低い場合は省電力
        if battery_percent is not None and battery_percent < 20 and not is_charging:
            return Prediction(
                recommended_plan=self.PLAN_SAVER,
                confidence=0.95,
                reason=f"バッテリー残量が{battery_percent}%のため省電力モード推奨"
            )

        # 2. 負荷の高いアプリ使用中
        if app_lower in self.HEAVY_APPS:
            if is_charging:
                return Prediction(
                    recommended_plan=self.PLAN_HIGH,
                    confidence=0.90,
                    reason=f"{active_app}使用中（重いアプリ）＋AC接続"
                )
            else:
                return Prediction(
                    recommended_plan=self.PLAN_BALANCED,
                    confidence=0.85,
                    reason=f"{active_app}使用中（重いアプリ）・バッテリー節約"
                )

        # 3. 軽いアプリ使用中
        if app_lower in self.LIGHT_APPS:
            if is_charging:
                return Prediction(
                    recommended_plan=self.PLAN_BALANCED,
                    confidence=0.85,
                    reason=f"{active_app}使用中（軽いアプリ）"
                )
            else:
                return Prediction(
                    recommended_plan=self.PLAN_SAVER,
                    confidence=0.80,
                    reason=f"{active_app}使用中・省電力推奨"
                )

        # 4. CPU負荷ベースの判定
        if cpu_percent > 70:
            plan = self.PLAN_HIGH if is_charging else self.PLAN_BALANCED
            return Prediction(
                recommended_plan=plan,
                confidence=0.85,
                reason=f"CPU負荷が{cpu_percent:.0f}%と高い"
            )

        if cpu_percent < 20:
            plan = self.PLAN_BALANCED if is_charging else self.PLAN_SAVER
            return Prediction(
                recommended_plan=plan,
                confidence=0.75,
                reason=f"CPU負荷が{cpu_percent:.0f}%と低い"
            )

        # 5. 学習パターンからの予測
        if len(self._patterns) >= 10:
            prediction = self._predict_from_patterns(
                hour, day_of_week, cpu_percent, is_charging, app_lower
            )
            if prediction:
                return prediction

        # 6. デフォルト：バランス
        return Prediction(
            recommended_plan=self.PLAN_BALANCED,
            confidence=0.50,
            reason="標準設定（学習データ収集中）"
        )

    def _predict_from_patterns(
        self,
        hour: int,
        day_of_week: int,
        cpu_percent: float,
        is_charging: bool,
        active_app: str
    ) -> Optional[Prediction]:
        """学習パターンから予測"""
        # 類似パターンを検索
        similar_patterns = []

        for p in self._patterns:
            score = 0.0

            # 時間帯の類似度
            hour_diff = abs(p["hour"] - hour)
            if hour_diff <= 1:
                score += 0.3
            elif hour_diff <= 3:
                score += 0.1

            # 曜日の類似度
            if p["day_of_week"] == day_of_week:
                score += 0.2

            # AC接続状態
            if p["is_charging"] == is_charging:
                score += 0.2

            # アプリの一致
            if p["active_app"] == active_app:
                score += 0.3

            if score >= 0.5:
                similar_patterns.append((score, p["chosen_plan"]))

        if not similar_patterns:
            return None

        # 最も多いプランをカウント
        plan_counts = {}
        for score, plan in similar_patterns:
            plan_counts[plan] = plan_counts.get(plan, 0) + score

        if not plan_counts:
            return None

        best_plan = max(plan_counts, key=plan_counts.get)
        total_score = sum(plan_counts.values())
        confidence = plan_counts[best_plan] / total_score if total_score > 0 else 0.5

        return Prediction(
            recommended_plan=best_plan,
            confidence=min(confidence, 0.85),
            reason=f"過去の使用パターン（{len(similar_patterns)}件）から予測"
        )

    def get_stats(self) -> dict:
        """学習統計を取得"""
        if not self._patterns:
            return {"total_patterns": 0, "plan_distribution": {}}

        plan_dist = {}
        for p in self._patterns:
            plan = p["chosen_plan"]
            plan_dist[plan] = plan_dist.get(plan, 0) + 1

        return {
            "total_patterns": len(self._patterns),
            "plan_distribution": plan_dist
        }


class SmartOptimizer:
    """スマート最適化エンジン"""

    def __init__(self):
        self.learner = PatternLearner()
        self._last_plan: Optional[str] = None
        self._switch_count = 0
        self._min_switch_interval = 60  # 最小切り替え間隔（秒）

    def get_recommendation(
        self,
        hour: int,
        day_of_week: int,
        cpu_percent: float,
        memory_percent: float,
        battery_percent: Optional[int],
        is_charging: bool,
        active_app: str
    ) -> Prediction:
        """最適化推奨を取得"""
        prediction = self.learner.predict(
            hour=hour,
            day_of_week=day_of_week,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            battery_percent=battery_percent,
            is_charging=is_charging,
            active_app=active_app
        )

        return prediction

    def record_choice(
        self,
        hour: int,
        day_of_week: int,
        cpu_percent: float,
        memory_percent: float,
        is_charging: bool,
        active_app: str,
        chosen_plan: str
    ):
        """ユーザーの選択を学習"""
        self.learner.add_pattern(
            hour=hour,
            day_of_week=day_of_week,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            is_charging=is_charging,
            active_app=active_app,
            chosen_plan=chosen_plan
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    optimizer = SmartOptimizer()

    # テスト予測
    prediction = optimizer.get_recommendation(
        hour=14,
        day_of_week=2,
        cpu_percent=45.0,
        memory_percent=60.0,
        battery_percent=80,
        is_charging=True,
        active_app="chrome.exe"
    )

    print(f"推奨プラン: {prediction.recommended_plan}")
    print(f"信頼度: {prediction.confidence:.0%}")
    print(f"理由: {prediction.reason}")

    print("\n学習統計:", optimizer.learner.get_stats())
