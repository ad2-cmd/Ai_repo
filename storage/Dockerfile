FROM python:3.13-alpine

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install uv \
    && uv pip install --system --no-cache --upgrade pip \
    && uv pip install --system --no-cache -r requirements.txt

COPY . .

CMD ["python", "scheduler.py"]
