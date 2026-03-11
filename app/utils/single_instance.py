from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstanceManager(QObject):
    raise_requested = Signal()

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self._name = name
        self._server = None
        self.is_secondary_launch = False

        self._try_connect_then_listen()

    def _try_connect_then_listen(self):
        # Try connecting to an existing instance
        socket = QLocalSocket(self)
        socket.connectToServer(self._name)
        if socket.waitForConnected(200):
            try:
                socket.write(b"raise")
                socket.flush()
                socket.waitForBytesWritten(200)
            finally:
                socket.disconnectFromServer()
            self.is_secondary_launch = True
            return

        # No server: clean stale and listen
        QLocalServer.removeServer(self._name)
        server = QLocalServer(self)
        if not server.listen(self._name):
            # If still cannot listen, treat as secondary to avoid duplicate
            self.is_secondary_launch = True
            return
        server.newConnection.connect(self._on_new_connection)
        self._server = server

    def _on_new_connection(self):
        if self._server is None:
            return
        sock = self._server.nextPendingConnection()
        if sock is None:
            return
        # Read and ignore any payload
        sock.readAll()
        sock.disconnectFromServer()
        self.raise_requested.emit()
