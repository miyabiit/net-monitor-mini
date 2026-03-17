# ネットワークモニターサーバ 設定ファイル仕様

## 1. 文書情報
- 文書名: ネットワークモニターサーバ 設定ファイル仕様
- 作成日: 2026-03-16
- 対象プロジェクト: `net-monitor-mini`
- 参照元:
  - `.docs/requirements.md`
  - `.docs/technical-design.md`

## 2. 目的
- 設定ファイルの配置、形式、項目、バリデーション条件を明確化する
- 初期実装時の設定読込仕様を固定する
- 将来の機能追加時に後方互換性を保ちやすくする

## 3. 基本方針
- 設定ファイル形式は JSON とする
- 既定ファイルパスは `config/appsettings.json` とする
- 起動時に設定を読み込み、Pydantic で検証する
- 無効な設定値がある場合は起動失敗として扱う
- 将来拡張に備えて、ルートに `version` を持たせる

## 4. ファイル配置
- 既定: `config/appsettings.json`
- 起動引数により別ファイル指定可能とする
- 相対パス指定時はプロジェクトルート基準で解決する

## 5. ルート構造

```json
{
  "version": 1,
  "app": {},
  "logging": {},
  "storage": {},
  "targets": []
}
```

## 6. 項目仕様

### 6.1 `version`
- 型: integer
- 必須: 必須
- 初期値: `1`
- 制約: 現時点では `1` のみ許可
- 用途: 将来の設定互換判定

### 6.2 `app`
- アプリ全体の起動設定

#### `app.host`
- 型: string
- 必須: 任意
- 初期値: `127.0.0.1`
- 制約: 初期リリースではローカルアドレスのみを推奨

#### `app.port`
- 型: integer
- 必須: 任意
- 初期値: `8080`
- 制約: `1` 以上 `65535` 以下

#### `app.open_browser_on_start`
- 型: boolean
- 必須: 任意
- 初期値: `true`
- 用途: 起動時に UI をブラウザで開くかを制御

### 6.3 `logging`
- ログ出力設定

#### `logging.level`
- 型: string
- 必須: 任意
- 初期値: `INFO`
- 許可値: `DEBUG`, `INFO`, `WARNING`, `ERROR`

#### `logging.file_path`
- 型: string
- 必須: 任意
- 初期値: `./logs/net-monitor.log`
- 用途: ログファイル出力先

#### `logging.rotate`
- 型: boolean
- 必須: 任意
- 初期値: `false`
- 用途: 将来のローテーション拡張予約

### 6.4 `storage`
- 永続化設定

#### `storage.database_path`
- 型: string
- 必須: 任意
- 初期値: `./data/net_monitor.db`
- 用途: SQLite DB ファイルパス

#### `storage.retention_days`
- 型: integer
- 必須: 任意
- 初期値: `30`
- 制約: `1` 以上
- 用途: 保存データの保持日数

### 6.5 `targets`
- 監視対象配列
- 必須: 必須
- 制約: 1 件以上を推奨

#### `targets[].id`
- 型: string
- 必須: 必須
- 制約:
  - 空文字不可
  - 一意であること
  - 英数字、ハイフン、アンダースコアを許可

#### `targets[].name`
- 型: string
- 必須: 必須
- 制約: 空文字不可

#### `targets[].address`
- 型: string
- 必須: 必須
- 制約:
  - 空文字不可
  - IP アドレスまたはホスト名

#### `targets[].enabled`
- 型: boolean
- 必須: 任意
- 初期値: `true`

#### `targets[].monitor_type`
- 型: string
- 必須: 任意
- 初期値: `ping`
- 制約: 初期リリースでは `ping` のみ許可

#### `targets[].interval_seconds`
- 型: integer
- 必須: 任意
- 初期値: `300`
- 制約: `60` 以上

#### `targets[].ping_count`
- 型: integer
- 必須: 任意
- 初期値: `3`
- 制約: `1` 以上 `10` 以下

#### `targets[].timeout_seconds`
- 型: number
- 必須: 任意
- 初期値: `2`
- 制約: `0.1` より大きい値

#### `targets[].tags`
- 型: array[string]
- 必須: 任意
- 初期値: `[]`
- 用途: 将来の分類表示用

## 7. 設定ファイル例

```json
{
  "version": 1,
  "app": {
    "host": "127.0.0.1",
    "port": 8080,
    "open_browser_on_start": true
  },
  "logging": {
    "level": "INFO",
    "file_path": "./logs/net-monitor.log",
    "rotate": false
  },
  "storage": {
    "database_path": "./data/net_monitor.db",
    "retention_days": 30
  },
  "targets": [
    {
      "id": "pc-001",
      "name": "FileServer",
      "address": "192.168.1.10",
      "enabled": true,
      "monitor_type": "ping",
      "interval_seconds": 300,
      "ping_count": 3,
      "timeout_seconds": 2,
      "tags": ["server", "office"]
    }
  ]
}
```

## 8. バリデーション方針
- ルート構造が不正な場合は起動中断
- 必須項目不足は起動中断
- `targets[].id` 重複は起動中断
- 初期版で未対応の `monitor_type` 指定は起動中断
- パス項目は必要に応じて親ディレクトリ作成対象とする

## 9. 互換性方針
- `version` で将来のスキーマ変更に対応する
- 既存キーの意味変更は極力避ける
- 新規キー追加は後方互換を維持する形で行う

## 10. 実装時の注意点
- JSON 読込失敗時は例外内容をログ出力する
- 設定エラーは利用者が修正しやすい形で項目名を含めて表示する
- 相対パスは絶対パスに正規化してアプリ内部で扱う
- デフォルト値適用後の設定オブジェクトを単一入口で利用する

## 11. 今後の拡張候補
- 通知設定セクション追加
- UI 表示設定追加
- 監視対象グループ設定追加
- 保存ポリシー詳細設定追加
