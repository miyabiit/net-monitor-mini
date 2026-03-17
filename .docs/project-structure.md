# ネットワークモニターサーバ 初期ディレクトリ構成設計

## 1. 文書情報
- 文書名: ネットワークモニターサーバ 初期ディレクトリ構成設計
- 作成日: 2026-03-16
- 対象プロジェクト: `net-monitor-mini`
- 参照元:
  - `.docs/system-design.md`
  - `.docs/technical-design.md`

## 2. 目的
- 初期実装時のファイル配置を統一する
- 監視機能追加時に既存構成を崩さず拡張できるようにする
- 実装者が責務単位でコード配置を判断できるようにする

## 3. 採用方針
- Python パッケージは `src` 配下に集約する
- 実行コード、設定、データ、ログ、テスト、文書を分離する
- UI の静的資産と API 実装を近接配置しつつ、責務としては分離する
- 将来の監視方式追加を見据え、`monitoring` は監視種別単位で分割しやすくする

## 4. 初期ディレクトリ構成

```text
net-monitor-mini/
  .docs/
    requirements.md
    system-design.md
    technical-design.md
    project-structure.md
    configuration-spec.md
  src/
    net_monitor/
      __init__.py
      main.py
      app/
        __init__.py
        bootstrap.py
      api/
        __init__.py
        routes/
          __init__.py
          health.py
          targets.py
      config/
        __init__.py
        loader.py
        schema.py
      logging/
        __init__.py
        setup.py
      models/
        __init__.py
        domain.py
      monitoring/
        __init__.py
        base.py
        ping/
          __init__.py
          parser.py
          runner.py
          service.py
      scheduler/
        __init__.py
        jobs.py
        manager.py
      storage/
        __init__.py
        database.py
        models.py
        repositories/
          __init__.py
          ping_results.py
          targets.py
      visualization/
        __init__.py
        templates/
          index.html
        static/
          css/
            app.css
          js/
            dashboard.js
  tests/
    unit/
    integration/
  config/
    appsettings.json
  data/
  logs/
  requirements.txt
  README.md
```

## 5. 配置ルール

### 5.1 src
- 実装コードは原則として `src/net_monitor` 以下に配置する
- 機能を跨る共通ロジックは責務に応じたモジュールへ分離する
- 単一ファイルへ機能を集約しない

### 5.2 api
- HTTP エンドポイントは `routes` 配下に分割する
- 初期リリースでは `health` と `targets` を分離する
- API 入出力モデルが増えた場合は専用モジュールを追加する

### 5.3 monitoring
- 監視方式ごとにサブディレクトリを切る
- 初期版は `ping` のみ実装する
- 共通インターフェースは `base.py` に置く

### 5.4 storage
- DB 接続とテーブル定義、リポジトリ責務を分離する
- SQL 文やクエリロジックは API 層に直接書かない

### 5.5 visualization
- HTML テンプレートと静的ファイルを保持する
- グラフ描画ロジックは `static/js` に置く
- API との通信ロジックは UI テンプレートに埋め込みすぎない

### 5.6 tests
- 単体テストと結合テストを分ける
- ping 実行のような OS 依存処理はモック可能な構造にする

### 5.7 config / data / logs
- 実装コード外の運用ファイル置き場として分離する
- 初期設定は `config/appsettings.json` を使用する
- DB ファイルは `data/`、ログファイルは `logs/` を既定とする

## 6. 主要ファイル責務

### 6.1 `main.py`
- アプリ起動エントリーポイント
- 起動パラメータ受付
- bootstrap 呼び出し

### 6.2 `app/bootstrap.py`
- 設定読込
- ログ初期化
- DB 初期化
- スケジューラ起動
- FastAPI アプリ生成

### 6.3 `config/schema.py`
- 設定ファイルの Pydantic スキーマ
- デフォルト値定義
- 値検証ロジック

### 6.4 `monitoring/ping/*`
- `runner.py`: ping コマンド実行
- `parser.py`: 実行結果解析
- `service.py`: 1 サイクル 3 回実行の制御

### 6.5 `scheduler/manager.py`
- 監視対象ごとのジョブ登録
- ジョブの更新、停止、再登録

### 6.6 `storage/repositories/*`
- 監視対象取得
- ping 結果保存
- UI 用参照クエリ提供

## 7. 拡張時の追加ルール
- 新しい監視方式を追加する場合は `monitoring/<type>/` を追加する
- 通知機能を追加する場合は `notifications/` など独立ディレクトリを新設する
- 集計機能が増えた場合は `services/` または `analytics/` の追加を検討する
- UI が大規模化した場合は `visualization` を別フロントエンド構成へ切り出せるよう、API 境界を保つ

## 8. 初期実装の最小対象
- `main.py`
- `config`
- `logging`
- `storage`
- `monitoring/ping`
- `scheduler`
- `api/routes`
- `visualization/templates`
- `visualization/static`

## 9. 保留事項
- `services/` ディレクトリを初期段階から置くかどうか
- マイグレーション管理ツールを初期導入するかどうか
- UI テンプレートを Jinja2 で構成するか、単純静的 HTML にするか
