from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# Initialize centralized extensions
db = SQLAlchemy()
socketio = SocketIO()
