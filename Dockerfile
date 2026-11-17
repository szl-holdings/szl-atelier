FROM python:3.14-slim@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

WORKDIR /app

RUN useradd --create-home --uid 1000 appuser

# Hash-locked from requirements.txt by requirements/docker/runtime.in (see that file to regenerate).
COPY requirements/docker/runtime.txt /tmp/runtime-requirements.txt
RUN python -m pip install --require-hashes --requirement /tmp/runtime-requirements.txt

COPY --chown=appuser:appuser . /app

USER appuser
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/readyz', timeout=3)"

CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
