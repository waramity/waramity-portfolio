FROM python:3.10.7-alpine
WORKDIR /waramity-portfolio
COPY . /waramity-portfolio
# COPY requirements.txt .
RUN pip install -r requirements.txt
# COPY . .
EXPOSE 5000
CMD ["python", "wsgi.py", "--host=0.0.0.0"]
