import pyglet


window = pyglet.window.Window()


@window.event
def on_draw():
    window.clear()


class PingServer(pyglet.net.Server):
    def __init__(self, address, port):
        super().__init__(address, port)
        self._connections = []

    def on_connection(self, connection):
        print("Connected <---", connection)
        connection.set_handler('on_receive', self._return_message)
        connection.set_handler('on_disconnect', self._connection_cleanup)
        self._connections.append(connection)

    def _return_message(self, connection, message):
        preview_length = min(24, len(message))
        print("Received message --->", message[:preview_length])
        connection.send(message)

    def _connection_cleanup(self, connection):
        print("Closed Connection --->", connection)
        self._connections.remove(connection)

    def pinger(self, dt):
        for conn in self._connections:
            conn.send(b'PING!')


server = PingServer('localhost', 8080)
pyglet.clock.schedule_interval(server.pinger, 3)
pyglet.app.run()
