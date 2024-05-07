FROM python:3.7.9-slim

WORKDIR /usr/src/sensor_simulation

RUN pip install --upgrade pip

COPY . .

RUN pip install --no-cache-dir simpy numpy pandas paho-mqtt typing_extensions

# Expose the port the app runs on
EXPOSE 9999

# Define environment variable
CMD [ "python", "./client_manager.py" ]

