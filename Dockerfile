### Base stage: shared between production and development
FROM python:3.13-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

### Production stage
FROM base AS production

COPY . .

ENV PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /bin/bash appuser
USER appuser

CMD ["python3", "main.py"]

### Development stage (used by devcontainer)
FROM base AS dev

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*


RUN useradd --create-home --shell /bin/bash devuser
USER devuser

# Source is bind-mounted by the devcontainer, no COPY needed
CMD ["sleep", "infinity"]