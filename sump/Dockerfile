ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3 py3-pip

WORKDIR /app
COPY app /app
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

EXPOSE 8099

CMD ["python3", "main.py"]
