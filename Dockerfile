# Windows
# FROM python:3.10.7-alpine

# MacOS
# FROM python:3.10.7-slim

# WORKDIR /waramity-portfolio
# COPY . /waramity-portfolio
# COPY requirements.txt .
# RUN pip install -r requirements.txt
# COPY . .

# M1 cannot use port 5000
# EXPOSE 5001
# CMD ["python", "wsgi.py", "--host=0.0.0.0"]
# CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]

FROM tiangolo/uwsgi-nginx:python3.10
# RUN apk --update add bash nano
ENV STATIC_URL /static
ENV STATIC_PATH /var/www/app/static
COPY requirements.txt /var/www/requirements.txt
RUN pip install -r /var/www/requirements.txt
