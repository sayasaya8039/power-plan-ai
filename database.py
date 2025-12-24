"""
データベースモジュール
使用パターンログをSQLiteに保存
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """使用記録"""
    id: Optional[int]
    timestamp: datetime
    hour: int
    day_of_week: int  # 0=月曜日
    cpu_percent: float
    memory_percent: float
    battery_percent: Optional[int]
    is_charging: bool
    active_app: str
    power_plan: str


class Database:
    """SQLiteデータベース管理"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            app_data = Path(os.environ.get("APPDATA", "."))
            self.db_path = app_data / "PowerPlanAI" / "usage.db"
        else:
            self.db_path = db_path

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """データベース初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    hour INTEGER NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_percent REAL NOT NULL,
                    battery_percent INTEGER,
                    is_charging INTEGER NOT NULL,
                    active_app TEXT NOT NULL,
                    power_plan TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date DATE PRIMARY KEY,
                    total_minutes INTEGER DEFAULT 0,
                    high_perf_minutes INTEGER DEFAULT 0,
                    balanced_minutes INTEGER DEFAULT 0,
                    power_saver_minutes INTEGER DEFAULT 0,
                    estimated_battery_saved INTEGER DEFAULT 0
                )
            """)

            # インデックス作成
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON usage_log(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hour ON usage_log(hour)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_app ON usage_log(active_app)")

            conn.commit()
            logger.info(f"データベース初期化完了: {self.db_path}")

    def add_usage_record(self, record: UsageRecord):
        """使用記録を追加"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO usage_log
                (timestamp, hour, day_of_week, cpu_percent, memory_percent,
                 battery_percent, is_charging, active_app, power_plan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.timestamp.isoformat(),
                record.hour,
                record.day_of_week,
                record.cpu_percent,
                record.memory_percent,
                record.battery_percent,
                1 if record.is_charging else 0,
                record.active_app,
                record.power_plan
            ))
            conn.commit()

    def get_recent_records(self, hours: int = 24) -> list[UsageRecord]:
        """直近の使用記録を取得"""
        since = datetime.now() - timedelta(hours=hours)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM usage_log
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """, (since.isoformat(),))

            records = []
            for row in cursor.fetchall():
                records.append(UsageRecord(
                    id=row["id"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    hour=row["hour"],
                    day_of_week=row["day_of_week"],
                    cpu_percent=row["cpu_percent"],
                    memory_percent=row["memory_percent"],
                    battery_percent=row["battery_percent"],
                    is_charging=bool(row["is_charging"]),
                    active_app=row["active_app"],
                    power_plan=row["power_plan"]
                ))
            return records

    def get_hourly_pattern(self, hour: int) -> dict:
        """特定時間帯の使用パターンを取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    AVG(cpu_percent) as avg_cpu,
                    AVG(memory_percent) as avg_memory,
                    COUNT(*) as count
                FROM usage_log
                WHERE hour = ?
            """, (hour,))
            row = cursor.fetchone()

            return {
                "avg_cpu": row[0] or 0,
                "avg_memory": row[1] or 0,
                "count": row[2] or 0
            }

    def get_app_usage_stats(self) -> dict[str, int]:
        """アプリ別使用回数を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT active_app, COUNT(*) as count
                FROM usage_log
                GROUP BY active_app
                ORDER BY count DESC
                LIMIT 20
            """)
            return {row[0]: row[1] for row in cursor.fetchall()}

    def update_daily_stats(self, plan_name: str, minutes: int = 1):
        """日次統計を更新"""
        today = datetime.now().date().isoformat()
        plan_col_map = {
            "高パフォーマンス": "high_perf_minutes",
            "バランス": "balanced_minutes",
            "省電力": "power_saver_minutes",
        }
        plan_col = plan_col_map.get(plan_name, "balanced_minutes")

        with sqlite3.connect(self.db_path) as conn:
            # まず既存レコードを確認
            cursor = conn.execute("SELECT 1 FROM daily_stats WHERE date = ?", (today,))
            exists = cursor.fetchone() is not None

            if exists:
                conn.execute(f"""
                    UPDATE daily_stats SET
                        total_minutes = total_minutes + ?,
                        {plan_col} = {plan_col} + ?
                    WHERE date = ?
                """, (minutes, minutes, today))
            else:
                conn.execute(f"""
                    INSERT INTO daily_stats (date, total_minutes, {plan_col})
                    VALUES (?, ?, ?)
                """, (today, minutes, minutes))
            conn.commit()

    def get_today_stats(self) -> dict:
        """今日の統計を取得"""
        today = datetime.now().date().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM daily_stats WHERE date = ?
            """, (today,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return {
                "total_minutes": 0,
                "high_perf_minutes": 0,
                "balanced_minutes": 0,
                "power_saver_minutes": 0,
            }

    def get_setting(self, key: str, default: str = "") -> str:
        """設定値を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            return row[0] if row else default

    def set_setting(self, key: str, value: str):
        """設定値を保存"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
            """, (key, value))
            conn.commit()

    def cleanup_old_records(self, days: int = 30):
        """古い記録を削除"""
        cutoff = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM usage_log WHERE timestamp < ?
            """, (cutoff.isoformat(),))
            deleted = cursor.rowcount
            conn.commit()

            if deleted > 0:
                logger.info(f"古い記録を削除: {deleted}件")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    db = Database(Path("./test_usage.db"))

    # テストデータ追加
    record = UsageRecord(
        id=None,
        timestamp=datetime.now(),
        hour=datetime.now().hour,
        day_of_week=datetime.now().weekday(),
        cpu_percent=45.5,
        memory_percent=60.0,
        battery_percent=80,
        is_charging=True,
        active_app="chrome.exe",
        power_plan="バランス"
    )
    db.add_usage_record(record)

    print("今日の統計:", db.get_today_stats())
    print("アプリ使用統計:", db.get_app_usage_stats())
