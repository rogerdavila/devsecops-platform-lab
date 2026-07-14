# ---- builder ----
FROM python:3.13-slim-trixie AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/deps -r requirements.txt

COPY src/ src/

# ---- runtime ----
FROM gcr.io/distroless/python3-debian13:nonroot

WORKDIR /app

ENV PYTHONPATH=/app/deps

COPY --from=builder /app/deps /app/deps
COPY --from=builder /app/src /app/src

EXPOSE 8080 9090

USER nonroot

ENTRYPOINT ["python", "-m", "src.main"]
