FROM python:3.10-slim

WORKDIR /app

COPY api_server ./api_server
COPY requirements.txt .

# Pythonパッケージのインストール
RUN pip install -r requirements.txt

ENV FLASK_APP=api_server.Conograph_API
ENV FLASK_RUN_PORT=8000
ENV FLASK_DEBUG=0

# CMDで手動起動（Flaskリロード機能を使わない）
CMD ["python", "api_server/Conograph_API.py"]
