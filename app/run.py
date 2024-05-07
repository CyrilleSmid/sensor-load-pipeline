from web_service import app
from web_service import db

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=False)