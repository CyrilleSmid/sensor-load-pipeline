FROM nvidia/cuda:11.3.1-cudnn8-devel-ubuntu20.04

# Install additional packages
RUN apt-get -y update && \
         apt-get -y upgrade && \
         apt-get install -y python3-pip python3-dev

RUN apt-get install -y git

# Install any python packages you need
COPY requirements.txt requirements.txt

RUN python3 -m pip install --upgrade pip && \
   python3 -m pip install -r requirements.txt

COPY . .

# RUN pip install --no-cache-dir flask flask-sqlalchemy flask-wtf flask-bcrypt flask-login werkzeug jinja2 email_validator docker influxdb-client ciso8601 holidays dash plotly pandas tensorflow==2.11 scikit-learn joblib

# Expose the port the app runs on
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=run.py

# Run the application
CMD ["flask", "run", "--host=0.0.0.0"]
