"""
電源プラン制御モジュール
powercfgコマンドを使用してWindows電源プランを管理
"""
import subprocess
import re
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class PowerPlan:
    """電源プランの情報"""
    guid: str
    name: str
    is_active: bool


class PowerManager:
    """Windows電源プラン管理クラス"""
    
    # 標準電源プランのGUID
    PLAN_HIGH_PERFORMANCE = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    PLAN_BALANCED = "381b4222-f694-41f0-9685-ff5bb260df2e"
    PLAN_POWER_SAVER = "a1841308-3541-4fab-bc81-f71556f20b4a"
    
    PLAN_NAMES = {
        PLAN_HIGH_PERFORMANCE: "高パフォーマンス",
        PLAN_BALANCED: "バランス",
        PLAN_POWER_SAVER: "省電力",
    }
    
    def __init__(self):
        self._plans_cache: list[PowerPlan] = []
        self._current_plan: Optional[str] = None
    
    def get_power_plans(self) -> list[PowerPlan]:
        """利用可能な電源プラン一覧を取得"""
        try:
            result = subprocess.run(
                ["powercfg", "/list"],
                capture_output=True,
                text=True,
                encoding="cp932",  # Windows日本語環境
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            plans = []
            # GUID抽出: (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
            pattern = r"GUID: ([a-f0-9-]+)\s+\((.+?)\)(\s*\*)?"
            
            for match in re.finditer(pattern, result.stdout, re.IGNORECASE):
                guid = match.group(1)
                name = match.group(2).strip()
                is_active = match.group(3) is not None
                
                plans.append(PowerPlan(guid=guid, name=name, is_active=is_active))
                
                if is_active:
                    self._current_plan = guid
            
            self._plans_cache = plans
            logger.info(f"電源プラン取得: {len(plans)}件")
            return plans
            
        except Exception as e:
            logger.error(f"電源プラン取得エラー: {e}")
            return []
    
    def get_active_plan(self) -> Optional[PowerPlan]:
        """現在アクティブな電源プランを取得"""
        plans = self.get_power_plans()
        for plan in plans:
            if plan.is_active:
                return plan
        return None
    
    def set_active_plan(self, guid: str) -> bool:
        """電源プランを切り替え"""
        try:
            # 現在のプランと同じなら何もしない
            if self._current_plan == guid:
                logger.debug(f"既に同じプラン: {guid}")
                return True
            
            result = subprocess.run(
                ["powercfg", "/setactive", guid],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                self._current_plan = guid
                plan_name = self.PLAN_NAMES.get(guid, guid)
                logger.info(f"電源プラン変更: {plan_name}")
                return True
            else:
                logger.error(f"電源プラン変更失敗: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"電源プラン変更エラー: {e}")
            return False
    
    def set_high_performance(self) -> bool:
        """高パフォーマンスモードに切り替え"""
        return self.set_active_plan(self.PLAN_HIGH_PERFORMANCE)
    
    def set_balanced(self) -> bool:
        """バランスモードに切り替え"""
        return self.set_active_plan(self.PLAN_BALANCED)
    
    def set_power_saver(self) -> bool:
        """省電力モードに切り替え"""
        return self.set_active_plan(self.PLAN_POWER_SAVER)
    
    def get_current_plan_name(self) -> str:
        """現在のプラン名を取得"""
        plan = self.get_active_plan()
        if plan:
            return plan.name
        return "不明"


if __name__ == "__main__":
    # テスト
    logging.basicConfig(level=logging.DEBUG)
    pm = PowerManager()
    
    print("=== 電源プラン一覧 ===")
    for plan in pm.get_power_plans():
        status = "★" if plan.is_active else " "
        print(f"{status} {plan.name} ({plan.guid})")
    
    print("")
    print(f"現在のプラン: {pm.get_current_plan_name()}")
