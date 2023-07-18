
from eventlet import wsgi
import eventlet
from app import app

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=5000, debug=True)
    app.run(debug=True, use_debugger=False, use_reloader=False)
