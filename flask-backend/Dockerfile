FROM python:3.9-alpine3.21
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    APP_PORT=8080
RUN apk add --no-cache gcc musl-dev python3-dev linux-headers libc-dev openssh-client

RUN pip install --no-cache-dir ansible -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY flask-backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN pip install --no-cache-dir pytest -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY flask-backend/app.py .
COPY tests ./tests
COPY ansible /app/ansible/
RUN PYTHONPATH=/app pytest tests/test_smoke.py -v

RUN addgroup -S flask-group && adduser -S flask-user -G flask-group
RUN chown -R flask-user:flask-group /app

USER flask-user
CMD ["python", "app.py"]