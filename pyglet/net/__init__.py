import queue as _queue
import struct as _struct
import socket as _socket
import threading as _threading

from pyglet.event import EventDispatcher as _EventDispatcher


class _BaseConnection(_EventDispatcher):
    """Base class for threaded socket connections."""

    def __init__(self, socket, address):
        self._socket = socket
        self._address = address[0]
        self._port = address[1]
        self._alive = _threading.Event()
        self._queue = _queue.Queue()
        _threading.Thread(target=self._recv, daemon=True).start()
        _threading.Thread(target=self._send, daemon=True).start()
        self._sentinal = object()   # poison pill

    def close(self):
        """Close the connection."""
        self._alive.set()
        self._queue.put(self._sentinal)
        self._socket.close()

    def _recv(self):  # Thread
        socket = self._socket

        while not self._alive.is_set():
            try:
                header = socket.recv(4)
                while len(header) < 4:
                    header += socket.recv(4)

                size = _struct.unpack('I', header)[0]

                message = socket.recv(size)
                while len(message) < size:
                    message += socket.recv(size)

                self.dispatch_event('on_receive', self, message)
            except BaseException as e:
                self.close()
                self.dispatch_event('on_disconnect', self, e)
                break

    def send(self, message):
        """Queue a message to send.

        Put a string of bytes into the queue to send.
        raises a `ConnectionError` if the connection
        has been closed or dropped.

       :Parameters:
            `message` : bytes
                A string of bytes to send.
        """
        if self._alive.is_set():
            raise ConnectionError("Connection is closed.")
        self._queue.put(message)

    def _send(self):    # Thread
        while not self._alive.is_set():
            message = self._queue.get()
            if message == self._sentinal:   # bail out on poison pill
                break
            try:
                packet = _struct.pack('I', len(message)) + message
                self._socket.sendall(packet)
            except BaseException as e:
                self.dispatch_event('on_disconnect', self, e)
                self._alive.set()
                break

    def on_receive(self, connection, message):
        """Event for received messages."""

    def on_disconnect(self, connection):
        """Event for disconnection. """

    def __repr__(self):
        return f"Connection(address={self._address}, port={self._port})"


_BaseConnection.register_event_type('on_receive')
_BaseConnection.register_event_type('on_disconnect')


class Client(_BaseConnection):
    def __init__(self, address, port):
        """Create a Client connection to a Server."""
        self._alive = True
        self._socket = _socket.create_connection((address, port))
        super().__init__(self._socket, address)

    def __repr__(self):
        return f"Client(address={self._address}, port={self._port})"


class Server(_EventDispatcher):

    def __init__(self, address, port, reuse_port=False):
        """Create a threaded socket server"""
        self._alive = _threading.Event()
        self._socket = _socket.create_server(
            (address, port), reuse_port=reuse_port)
        self._recv_thread = _threading.Thread(
            target=self._receive_connections, daemon=True)
        self._recv_thread.start()
        print("Server loop running in thread:", self._recv_thread.name)

    def close(self):
        self._alive.set()
        self._socket.close()

    def _receive_connections(self):     # Thread
        while not self._alive.is_set():
            try:
                new_socket, address = self._socket.accept()
                connection = _BaseConnection(new_socket, address)
                self.dispatch_event('on_connection', connection)
            except (BrokenPipeError, OSError):
                self._alive.set()
        self.dispatch_event('on_disconnect')

    def on_connection(self, connection):
        """Event for new Connections received."""

    def on_disconnect(self, exception):
        """Event for Server disconnection."""


Server.register_event_type('on_connection')
Server.register_event_type('on_disconnect')
