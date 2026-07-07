FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \                                                                                                                                                     
    PYTHONDONTWRITEBYTECODE=1 \                                                                                                                                              
    PORT=8000    

WORKDIR /app  

RUN apt-get update && apt-get install -y --no-install-recommends \                                                                                                           
    build-essential \                                                                                                                                                        
    libpq-dev \                                                                                                                                                              
    && rm -rf /var/lib/apt/lists/*    

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock* ./

RUN uv pip install --system -r pyproject.toml

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]