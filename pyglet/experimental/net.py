"""Experimental networking

This module contains experiments in making user-friendly Server and Client
classes that integrate with pyglet's event system. These are very basic,
socket server/client examples, and are not ready to be used in production.
They are included here to solicit feedback, and possibly spark further
development. Basic Server usage::

    server = net.Server(address='0.0.0.0', port=1234)
    active_connections = weakref.WeakSet()

    def pong(connection, message):
        print(f"Received '{message}' from '{connection}'")
        connection.send(b'pong')

    @server.event
    def on_connection(connection):
        print(f"New client connected: {connection}")
        connection.set_handler('on_receive', pong)
        active_connections.add(connection)

    @server.event
    def on_disconnect(connection):
        print(f"Client disconnected: {connection}")
        active_connections.discard(connection)


Basic Client example::

    client = net.Client(address='localhost', port=1234)

    @client.event
    def on_receive(client, message):
        print(f"Received: {message}")

    @client.event
    def on_disconnect(client):
        print(f"Disconnected: {client}")

    client.send(b'ping')

"""


import queue as _queue
import struct as _struct
import socket as _socket
import asyncio as _asyncio
import threading as _threading

from pyglet.event import EventDispatcher as _EventDispatcher

from pyglet.util import debug_print

_debug_net = debug_print('debug_net')


class Client(_EventDispatcher):
    def __init__(self, address, port):
        """Create a Client connection to a Server."""
        self._socket = _socket.create_connection((address, port))
        self._address = address
        self._port = port

        self._terminate = _threading.Event()
        self._queue = _queue.Queue()

        _threading.Thread(target=self._recv, daemon=True).start()
        _threading.Thread(target=self._send, daemon=True).start()

        self._sentinal = object()  # poison pill

    def close(self):
        """Close the connection."""
        self._queue.put(self._sentinal)
        self._socket.shutdown(1)
        if not self._terminate.is_set():
            self._terminate.set()
            self.dispatch_event('on_disconnect', self)

    def send(self, message):
        """Queue a message to send.

        Put a string of bytes into the queue to send.
        raises a `ConnectionError` if the connection
        has been closed or dropped.

       :Parameters:
            `message` : bytes
                A string of bytes to send.
        """
        if self._terminate.is_set():
            raise ConnectionError("Connection is closed.")
        self._queue.put(message)

    def _send(self):    # Thread
        """Background Thread to send messages from the queue."""
        while not self._terminate.is_set():
            message = self._queue.get()
            if message == self._sentinal:  # bail out on poison pill
                break
            try:
                # Attach a 4byte header to the front of the message:
                packet = _struct.pack('I', len(message)) + message
                self._socket.sendall(packet)
            except (ConnectionError, OSError):
                self.close()
                break

        assert _debug_net("Exiting _send thread")


    def _recv(self):    # Thread
        socket = self._socket

        while not self._terminate.is_set():
            try:
                header = socket.recv(4)
                while len(header) < 4:
                    header += socket.recv(4 - len(header))
                size = _struct.unpack('I', header)[0]

                message = socket.recv(size)
                while len(message) < size:
                    message += socket.recv(size)
                self.dispatch_event('on_receive', self, message)
            except (ConnectionError, OSError):
                self.close()
                break

        assert _debug_net("Exiting _recv thread")

    def on_receive(self, connection, message):
        """Event for received messages."""

    def on_disconnect(self, connection):
        """Event for disconnection. """

    def __repr__(self):
        return f"Client(address={self._address}, port={self._port})"


Client.register_event_type('on_receive')
Client.register_event_type('on_disconnect')


class ClientConnection(_EventDispatcher):

    def __init__(self, reader, writer):
        self._reader = reader
        self._writer = writer
        self._closed = False
        self._loop = _asyncio.get_event_loop()
        _asyncio.run_coroutine_threadsafe(self._recv(), self._loop)

    def close(self):
        if not self._closed:
            self._writer.transport.close()
            self._closed = True
            self.dispatch_event('on_disconnect', self)

    async def _recv(self):
        while not self._closed:
            try:
                header = await self._reader.readexactly(4)
                size = _struct.unpack('I', header)[0]
                message = await self._reader.readexactly(size)
                self._loop.call_soon(self.dispatch_event, 'on_receive', self, message)

            except _asyncio.IncompleteReadError:
                self.close()
                break

    async def _send(self, message):
        try:
            packet = _struct.pack('I', len(message)) + message
            self._writer.write(packet)
            await self._writer.drain()
        except ConnectionResetError:
            self.close()

    def send(self, message):
        # Synchrounously send a message in an async coroutine.
        if self._writer.transport is None or self._writer.transport.is_closing():
            self.close()
            return
        _future = _asyncio.run_coroutine_threadsafe(self._send(message), self._loop)

    def on_receive(self, connection, message):
        """Event for received messages."""

    def on_disconnect(self, connection):
        """Event for disconnection. """

    def __del__(self):
        assert _debug_net(f"Connection garbage collected: {self}")

    def __repr__(self):
        return f"{self.__class__.__name__}({id(self)})"


ClientConnection.register_event_type('on_receive')
ClientConnection.register_event_type('on_disconnect')


class Server(_EventDispatcher):

    def __init__(self, address, port):
        self._address = address
        self._port = port

        self._server = None

        self._thread = _threading.Thread(target=self._run, daemon=True)
        self._thread.start()

        blurb = f"Server listening on {address}:{port}"
        assert _debug_net(f"{'-' * len(blurb)}\n{blurb}\n{'-' * len(blurb)}")


    async def handle_connection(self, reader, writer):
        connection = ClientConnection(reader, writer)
        self.dispatch_event('on_connection', connection)

    async def _start_server(self):
        self._server = await _asyncio.start_server(self.handle_connection, self._address, self._port)
        async with self._server:
            await self._server.serve_forever()

    def _run(self):
        try:
            _asyncio.run(self._start_server())
        except KeyboardInterrupt:
            self._server.close()

    def on_connection(self, connection):
        """Event for new Client connections."""
        assert _debug_net(f"Connected <--- {connection}")
        connection.set_handler('on_disconnect', self.on_disconnect)

    def on_disconnect(self, connection):
        """Event for disconnected Clients."""
        assert _debug_net(f"Disconnected ---> {connection}")


Server.register_event_type('on_connection')
Server.register_event_type('on_disconnect')
