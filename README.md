# ⚡ Power Plan AI - Windows電源プラン最適化アプリ

[![Release](https://img.shields.io/github/v/release/sayasaya8039/power-plan-ai?style=flat-square)](https://github.com/sayasaya8039/power-plan-ai/releases)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![Windows](https://img.shields.io/badge/platform-Windows-0078D6?style=flat-square&logo=windows)](https://github.com/sayasaya8039/power-plan-ai/releases)

**AIがあなたの使用パターンを学習し、Windows電源プランを自動で最適化します**

> 🔥 **世界初！** ユーザーの使用パターンをAIで学習して電源プランを自動切り替えするアプリ

## 概要

Power Plan AI は、ユーザーの使用パターン（アプリ使用、時間帯、バッテリー状態、CPU負荷）を学習し、最適な電源プラン（究極のパフォーマンス/高パフォーマンス/バランス/省電力）を自動で切り替えるWindowsデスクトップアプリです。

**既存ツールとの違い:**
- 従来の電源管理ツール → 手動切り替えのみ
- Power Plan AI → **AIが自動で最適なプランを選択**

## 主な機能

- **AI自動最適化**: 使用パターンを学習し、最適な電源プランを自動選択
- **4つの電源プラン**: 究極のパフォーマンス/高パフォーマンス/バランス/省電力
- **スタートアップ登録**: Windows起動時に自動で開始（設定画面から有効化可能）
- **トレイ常駐**: システムトレイに常駐し、いつでもクイックアクセス
- **ダッシュボード**: 現在の状態、AI推奨、統計情報を一覧表示
- **手動切替**: 必要に応じて手動でプランを変更可能
- **プライバシー保護**: 全てローカル処理、外部送信なし

## スクリーンショット

```
┌───────────────────────────────────────────┐
│  ⚡ Power Plan AI                          │
│  AIが最適な電源プランを自動選択します     │
├───────────────────────────────────────────┤
│  現在のプラン │ バッテリー │ CPU使用率    │
│    バランス   │    96%     │    22%       │
├───────────────────────────────────────────┤
│  👑 究極        │  🚀 高パフォーマンス    │
│  ⚖️ バランス    │  🔋 省電力              │
├───────────────────────────────────────────┤
│  AI推奨: バランス                         │
│  理由: 標準設定（学習データ収集中）       │
│  信頼度: ████████░░ 80%                   │
└───────────────────────────────────────────┘
```

## インストール

### EXE版（推奨）
1. `PowerPlanAI/PowerPlanAI.exe` をダウンロード
2. ダブルクリックで起動
3. システムトレイにアイコンが表示されます

### 開発版
```bash
# 依存関係インストール
uv venv
uv pip install -r pyproject.toml

# 起動
.venv/Scripts/python.exe src/main.py
```

## 使い方

1. **起動**: アプリを起動するとシステムトレイに常駐
2. **ダッシュボード**: トレイアイコンをダブルクリックでダッシュボード表示
3. **自動最適化**: デフォルトでAI自動最適化が有効
4. **手動切替**: トレイメニューまたはダッシュボードから切替可能

## AI学習について

- 使用パターン（アプリ、時間帯、CPU負荷、バッテリー状態）を記録
- 1週間程度の使用でユーザーの生活パターンを学習
- 学習が進むと予測精度が向上（最大85%）

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| 言語 | Python 3.11+ |
| GUI | PyQt6 |
| システム監視 | psutil, pywin32 |
| データベース | SQLite |
| 機械学習 | scikit-learn |
| ビルド | PyInstaller |

## ファイル構成

```
Windows_power_plan_AI_optimization/
├── src/
│   ├── main.py              # メインアプリ
│   ├── power_manager.py     # 電源プラン制御
│   ├── system_monitor.py    # システム監視
│   ├── database.py          # データベース
│   ├── pattern_learner.py   # AI学習
│   ├── startup_manager.py   # スタートアップ管理
│   └── ui/
│       ├── tray_icon.py     # トレイアイコン
│       └── dashboard.py     # ダッシュボード
├── PowerPlanAI/
│   └── PowerPlanAI.exe      # ビルド済みEXE
├── pyproject.toml           # 依存関係
└── README.md
```

## データ保存場所

- 使用ログ: `%APPDATA%/PowerPlanAI/usage.db`
- 学習モデル: `%APPDATA%/PowerPlanAI/model.pkl`

## 注意事項

- Windows専用アプリです
- 初回起動時はAI学習データがないため、デフォルト設定で動作します
- バッテリー残量20%未満では自動的に省電力モードになります
- 「究極のパフォーマンス」プランが存在しない場合は自動的に作成されます

## ライセンス

MIT License

## バージョン履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 1.1.0 | 2025-12-24 | スタートアップ登録機能追加 |
| 1.0.0 | 2025-12-24 | 初回リリース |
