FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Kraken CLI
RUN curl --proto '=https' --tlsv1.2 -LsSf \
    https://github.com/krakenfx/kraken-cli/releases/latest/download/kraken-cli-installer.sh | sh

ENV PATH="/root/.cargo/bin:${PATH}"
ENV KRAKEN_CLI_PATH="/root/.cargo/bin/kraken"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
