from locust import HttpUser, TaskSet, between, task
import re
from queue import Queue
import uuid

class UserBehavior(HttpUser):
    wait_time = between(5, 9)
    user_queue = Queue()
    
    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.client.verify = False
        self.get_token()
        self.register_user()

    def on_stop(self):
        """ on_stop is called when the TaskSet is stopping """
        self.logout()

    def get_token(self):
        response = self.client.get("/login")
        # Sample string from response:
        # <input id="csrf_token" name="csrf_token" type="hidden" value="REDACTED">
        self.csrftoken = re.search(' name="csrf_token" .* value="(.+?)"', response.text).group(1)
        print(f"DEBUG: self.csrftoken = {self.csrftoken}")
        
    def register_user(self):
        user_id = str(uuid.uuid4())  # Generate a random user ID
        self.user_queue.put(user_id)  # Add user ID to the queue
        response = self.client.get("/register_user")
        if response.status_code == 200:
            # Perform registration
            self.client.post("/register_user", {
                "email": f"{user_id}@example.com",
                "password": "password",
                "test-mode": "locust-test"
            })    
        
    @task
    def login(self):
        user_id = self.user_queue.get()
        response = self.client.post("/login",
                                    {"email": f"{user_id}@example.com",
                                     "password": "password",
                                     "test-mode": "locust-test"
                                     },
                                    headers={"X-CSRFToken": self.csrftoken})
        print(f"DEBUG: login response.status_code = {response.status_code}")

    @task
    def index(self):
        self.client.get("/")
        
    def logout(self):
        self.client.get("/logout")


