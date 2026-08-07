FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# data/ holds the SQLite file - mounted as a volume in docker-compose so it
# survives container rebuilds/restarts.
CMD ["python", "-m", "bot.main"]
