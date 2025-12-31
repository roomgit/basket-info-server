# FastAPI WebSocket Server for Google Cloud Run

Google Cloud Run にデプロイできる FastAPI ベースの WebSocket サーバーです。

## 機能

- WebSocket 接続のサポート
- 複数クライアントへのブロードキャスト
- ヘルスチェックエンドポイント
- テスト用 HTML クライアント

## ローカルでの実行

### 前提条件
- Python 3.11 以上
- pip

### セットアップと実行

```bash
# 依存関係のインストール
pip install -r requirements.txt

# サーバーの起動
python main.py
```

サーバーは `http://localhost:8080` で起動します。

### エンドポイント

- `GET /` - サーバー情報
- `GET /health` - ヘルスチェック
- `GET /test` - WebSocket テストクライアント
- `WebSocket /ws/{client_id}` - WebSocket エンドポイント

## Google Cloud Run へのデプロイ

### 前提条件

- Google Cloud SDK (gcloud) がインストールされていること
- Google Cloud プロジェクトが作成されていること
- Container Registry または Artifact Registry が有効化されていること

### デプロイ手順

1. **Google Cloud にログイン**
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

2. **Docker イメージのビルドとプッシュ**

Artifact Registry を使用する場合:
```bash
# リージョンを設定（例: asia-northeast1）
export REGION=asia-northeast1
export PROJECT_ID=YOUR_PROJECT_ID
export SERVICE_NAME=websocket-server

# Artifact Registry リポジトリの作成（初回のみ）
gcloud artifacts repositories create cloud-run-repo \
    --repository-format=docker \
    --location=${REGION} \
    --description="Docker repository for Cloud Run"

# Docker 認証設定
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# イメージのビルドとプッシュ
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-repo/${SERVICE_NAME}:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-repo/${SERVICE_NAME}:latest
```

3. **Cloud Run へのデプロイ**

```bash
gcloud run deploy ${SERVICE_NAME} \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-repo/${SERVICE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --timeout 3600 \
    --cpu 1 \
    --memory 512Mi \
    --min-instances 0 \
    --max-instances 10
```

### 重要な注意点

1. **WebSocket のタイムアウト設定**
   - Cloud Run の WebSocket 接続は最大 60 分まで
   - `--timeout 3600` で最大タイムアウトを設定

2. **認証設定**
   - `--allow-unauthenticated` で誰でもアクセス可能
   - 本番環境では適切な認証を実装してください

3. **スケーリング設定**
   - `--min-instances 0` でコスト削減（コールドスタートあり）
   - 常時接続が必要な場合は `--min-instances 1` 以上に設定

### デプロイ後の確認

```bash
# サービス URL の取得
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)'

# ログの確認
gcloud run services logs read ${SERVICE_NAME} --region ${REGION}
```

## テスト方法

1. ブラウザで `https://YOUR_SERVICE_URL/test` にアクセス
2. "Connect" ボタンをクリックして WebSocket 接続
3. メッセージを送信してテスト

## トラブルシューティング

### WebSocket 接続が確立できない場合

- Cloud Run のログを確認: `gcloud run services logs read ${SERVICE_NAME}`
- ブラウザの開発者ツールでネットワークタブを確認
- HTTP → HTTPS へのアップグレードが正しく行われているか確認

### 接続がすぐに切断される場合

- タイムアウト設定を確認
- クライアント側で定期的に ping/pong を送信することを検討

## ローカル Docker テスト

```bash
# イメージのビルド
docker build -t websocket-server .

# コンテナの実行
docker run -p 8080:8080 websocket-server

# ブラウザで http://localhost:8080/test にアクセス
```

## セキュリティに関する考慮事項

- 本番環境では認証・認可を実装してください
- CORS 設定が必要な場合は FastAPI の CORSMiddleware を追加
- レート制限の実装を検討
- 環境変数で機密情報を管理

## ライセンス

このプロジェクトは自由に使用できます。
