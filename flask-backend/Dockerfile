FROM python:3.9-alpine
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    APP_PORT=8080
RUN apk add --no-cache gcc musl-dev python3-dev linux-headers libc-dev openssh-client

RUN pip install --no-cache-dir ansible -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN addgroup -S flask-group && adduser -S flask-user -G flask-group
RUN chown -R flask-user:flask-group /app

COPY app.py .

USER flask-user
CMD ["python", "app.py"]