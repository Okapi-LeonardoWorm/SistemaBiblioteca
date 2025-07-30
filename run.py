from app import createApp
import logging
from gevent.pywsgi import WSGIServer


# Criar a aplicação
app = createApp()

# Configurar os LOGs de uso
logging.basicConfig(filename="app.log", level=logging.DEBUG)


if __name__ == '__main__':
    # Cria o servidor WSGI com gevent
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    
    # Executa o servidor WSGI
    http_server.serve_forever()