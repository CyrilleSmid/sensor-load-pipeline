FROM python:3.7.9-slim

WORKDIR /usr/src/app

RUN pip install --upgrade pip

COPY . .

RUN pip install --no-cache-dir flask flask-sqlalchemy flask-wtf flask-bcrypt flask-login werkzeug jinja2 email_validator docker influxdb-client ciso8601 holidays dash plotly

# Expose the port the app runs on
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=run.py

# Run the application
CMD ["flask", "run", "--host=0.0.0.0"]
