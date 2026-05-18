FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Kraken CLI
RUN curl -L -o /usr/local/bin/kraken https://github.com/krakenfx/kraken-cli/releases/latest/download/kraken-linux-amd64 && \
    chmod +x /usr/local/bin/kraken

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
