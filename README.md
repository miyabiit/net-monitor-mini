# net-monitor-mini

Windows PC 上で動作する常時稼働型のネットワークモニターサーバです。

## 初期機能
- 指定対象への定期 ping 監視
- SQLite への監視結果保存
- ローカル Web UI によるグラフ表示

## 起動方法
1. `python -m venv .venv`
2. `.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `python main.py --config config/appsettings.json`

## 既定 URL
- `http://127.0.0.1:8080`
