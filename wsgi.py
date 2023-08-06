
from eventlet import wsgi
import eventlet
from app import app

from app.scheduler import sched

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=5000, debug=True)
    sched.start()
    app.run(host="0.0.0.0", port=5001, debug=True, use_debugger=False, use_reloader=False)
