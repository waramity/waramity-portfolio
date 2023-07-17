# Windows
# FROM python:3.10.7-alpine

# MacOS
FROM python:3.10.7-slim

# Update the package list and install dependencies
RUN apt-get update -y \
    && apt-get install -y python3-pip python3-dev build-essential locales

# Set the locale to avoid Unicode-related issues
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gene

WORKDIR /waramity-portfolio
COPY . /waramity-portfolio
# COPY requirements.txt .
RUN pip install -r requirements.txt
# COPY . .

# M1 cannot use port 5000
EXPOSE 5001
# CMD ["python", "wsgi.py", "--host=0.0.0.0"]
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001", "--reload"]

