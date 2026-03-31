# ネットワークモニターサーバ 技術設計

## 1. 文書情報
- 文書名: ネットワークモニターサーバ 技術設計
- 作成日: 2026-03-16
- 対象プロジェクト: `net-monitor-mini`
- 参照元:
  - `.docs/requirements.md`
  - `.docs/system-design.md`

## 2. 技術選定

### 2.1 採用技術
- 言語: Python 3.12 系
- Web フレームワーク: FastAPI
- ASGI サーバ: Uvicorn
- スケジューラ: APScheduler
- 永続化: SQLite
- ORM / DB アクセス: SQLAlchemy
- データ検証: Pydantic
- フロントエンド: HTML / JavaScript / Chart.js
- ログ: Python 標準 logging
- テスト: pytest

### 2.2 採用理由
- `FastAPI` はローカル API と設定 UI 用の実装を分離しやすい
- `APScheduler` はアプリ内定期実行に適しており、対象追加時も扱いやすい
- `SQLite` は初期リリースの単一マシン用途に対して十分で、導入と配布が軽い
- `SQLAlchemy` は将来 DB を差し替える余地を残しやすい
- `Chart.js` は初期段階の時系列グラフ描画に必要十分で軽量
- いずれも Python エコシステムで一般的であり、小規模監視ツールの初期構築に適する

## 3. 非採用技術
- Electron
  - 初期段階では UI コストが高く、ローカル Web UI で要件を満たせるため採用しない
- PostgreSQL
  - 初期リリースでは運用負荷が過剰なため採用しない
- Windows タスクスケジューラ
  - ジョブごとの柔軟な制御と将来拡張を考え、アプリ内スケジューラを優先する

## 4. ディレクトリ方針

```text
net-monitor-mini/
  .docs/
  src/
    net_monitor/
      app/
      api/
      config/
      monitoring/
      scheduler/
      storage/
      visualization/
      logging/
      models/
  tests/
  data/
  logs/
```

## 5. コンポーネント設計

### 5.1 app
- アプリケーション起動順序を制御する
- 設定ロード、DB 初期化、スケジューラ起動、API 起動をまとめる

### 5.2 config
- 設定ファイルの読込、バリデーション、デフォルト値適用を担う
- 監視対象一覧、監視間隔、保持期間などを管理する

### 5.3 monitoring
- ping 実行ロジックを提供する
- 将来は `http`, `tcp` など別監視方式を同一インターフェースで追加できるようにする

### 5.4 scheduler
- 監視対象ごとのジョブ登録、再登録、停止制御を担う
- 有効/無効設定に応じて対象ジョブを更新できる構造とする

### 5.5 storage
- DB 接続管理、スキーマ管理、監視結果永続化、参照 API 用クエリを担う

### 5.6 api
- UI 向けに JSON API を提供する
- 将来、外部連携 API を分離しやすい構成とする

### 5.7 visualization
- 初期版では Web UI テンプレート、静的ファイル、グラフ用データ整形を管理する

## 6. 設定設計

### 6.1 設定ファイル形式
- JSON または YAML を候補とする
- 初期リリースでは Python 標準機能で扱いやすい JSON を採用する

### 6.2 設定項目案
- アプリ設定
  - API ホスト
  - API ポート
  - ログレベル
  - データ保存先
- 監視設定
  - 監視対象 ID
  - 表示名
  - ホスト名または IP
  - 有効/無効
  - 監視間隔秒
  - 1 サイクルあたり ping 回数
  - タイムアウト秒

### 6.3 設定ファイル例
```json
{
  "app": {
    "host": "127.0.0.1",
    "port": 8080,
    "log_level": "INFO",
    "database_path": "./data/net_monitor.db"
  },
  "targets": [
    {
      "id": "pc-001",
      "name": "FileServer",
      "address": "192.168.1.10",
      "enabled": true,
      "interval_seconds": 300,
      "ping_count": 3,
      "timeout_seconds": 2
    }
  ]
}
```

## 7. データモデル設計

### 7.1 テーブル方針
- 初期版では最低限 `monitor_targets` と `ping_results` を持つ
- 将来の監視方式追加を見据え、監視対象と監視結果を分離する

### 7.2 monitor_targets
- `id`
- `target_key`
- `name`
- `address`
- `enabled`
- `monitor_type`
- `interval_seconds`
- `probe_count`
- `timeout_seconds`
- `created_at`
- `updated_at`

### 7.3 ping_results
- `id`
- `target_id`
- `cycle_id`
- `measured_at`
- `attempt_no`
- `success`
- `latency_ms`
- `status_code`
- `status_message`
- `created_at`

### 7.4 補足
- `cycle_id` により 1 回の監視サイクル内の 3 試行をグルーピングする
- `status_code` は `success`, `timeout`, `dns_error`, `unreachable`, `unknown_error` などを想定する
- ping 応答不能時の `latency_ms` は `NULL` を許容する

## 8. API 設計方針

### 8.1 初期 API 一覧
- `GET /api/targets`
  - 監視対象一覧取得
- `GET /api/targets/{target_id}/results`
  - 指定対象の監視結果取得
  - `days` による期間指定と `limit` による件数上限指定を受け付ける
- `GET /api/targets/{target_id}/summary`
  - 直近状態や成功率の簡易集計取得
- `GET /health`
  - アプリ正常性確認

### 8.2 レスポンス方針
- UI で扱いやすい JSON を返す
- 時刻は ISO 8601 形式で返す
- 応答時間グラフと成功/失敗表示に必要な項目を含める

## 9. ping 実装方針

### 9.1 実装方法
- Windows 標準の `ping` コマンドを subprocess 経由で呼び出す
- OS 依存処理は `monitoring.ping_runner` に閉じ込める

### 9.2 理由
- Windows 環境での動作前提が明確であり、OS 標準機能を活用できる
- 権限やネットワーク制約を含む実運用に近い結果を取得しやすい

### 9.3 注意点
- 実行結果の解析は Windows の出力形式に依存するため、専用パーサを分離する
- ロケール差異の影響を受ける可能性があるため、出力解析は実測で調整前提とする

## 10. UI 設計方針

### 10.1 初期画面
- 監視対象一覧
- 選択対象の最新状態表示
- 応答時間推移グラフ
- 成功/失敗の状態表示
- グラフは直近 1 週間を初期表示し、X 軸は `dd HH` 表示とする

### 10.2 UI 実装方針
- 初期版はサーバサイド配信する単純な Web UI とする
- 複雑なフロントエンドビルドは導入しない
- 将来の SPA 化を妨げないよう、API と表示層を分離する

## 11. ログ設計方針
- 起動ログ
- 監視実行ログ
- 監視失敗ログ
- DB エラーログ
- API エラーログ

### 11.1 ログ出力内容
- 時刻
- ログレベル
- 対象 ID
- イベント種別
- エラーメッセージ

## 12. テスト方針

### 12.1 単体テスト
- ping 出力パーサ
- 設定バリデーション
- 結果保存処理
- API レスポンス整形

### 12.2 結合テスト
- 監視ジョブ実行から DB 保存までの一連処理
- API 経由でグラフ用データ取得ができること

### 12.3 手動確認
- Windows 上で ping 実行結果が正しく保存されること
- 5 分ごとのスケジュール実行が継続すること
- UI で結果がグラフ表示されること

## 13. 技術上のリスク
- Windows `ping` 出力のロケール差異により解析ロジックが不安定になる可能性がある
- SQLite は単一マシン用途には適するが、多数同時アクセスには向かない
- 常駐方法によっては、PC ログオフ時の挙動を別途検証する必要がある

## 14. 初期実装時の優先順
1. 設定読込
2. DB 初期化
3. ping 実行モジュール
4. スケジューラ
5. 保存処理
6. API
7. グラフ UI

## 15. 次に確定すべき事項
- 設定ファイル配置場所
- DB ファイル配置場所
- ログファイル出力方式
- 初期 UI の画面レイアウト
- Windows 自動起動方式
