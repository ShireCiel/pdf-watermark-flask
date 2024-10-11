FROM python:3.11-slim

RUN pip install --upgrade pip

WORKDIR /opt

COPY src .
COPY requirements.txt .

RUN pip install -r requirements.txt

WORKDIR /opt/src/pdf_watermark

CMD ["python", "flaskserver.py"]