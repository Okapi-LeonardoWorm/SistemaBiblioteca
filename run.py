from app import app
import logging
from gevent.pywsgi import WSGIServer


logging.basicConfig(filename="app.log", level=logging.DEBUG)

if __name__ == '__main__':
    app.run(debug=True)
    http_server = WSGIServer(('0.0.0.0', 5000), app)