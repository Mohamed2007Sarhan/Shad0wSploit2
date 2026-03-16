FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir paramiko colorama requests

COPY chimera.py .


EXPOSE 2222 8080 2121 9999

CMD ["python", "chimera.py"]