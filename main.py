from flask import Flask
from routes import garbage_bp  # Removed "src."

app = Flask(__name__)

# Register blueprint
app.register_blueprint(garbage_bp)

if __name__ == "__main__":
    app.run(debug=True)
