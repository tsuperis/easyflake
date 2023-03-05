import sys
from unittest.mock import AsyncMock, MagicMock

import grpc
import pytest

from easyflake.grpc.sequence_pb2 import SequenceReply, SequenceRequest
from easyflake.node.grpc import NodeIdPool, SequenceServicer

if sys.version_info < (3, 10):

    async def anext(ait):
        return await ait.__anext__()


@pytest.fixture
def context_mock():
    return MagicMock(spec=grpc.aio.ServicerContext)


@pytest.fixture
def daemon_mode(mocker):
    mocker.patch("easyflake.config.DAEMON_MODE", True)


class Cancelled(Exception, grpc.Call):
    __abstractmethods__ = set()  # type: ignore

    def code(self):
        return grpc.StatusCode.CANCELLED


class Unavailable(Exception, grpc.Call):
    __abstractmethods__ = set()  # type: ignore

    def code(self):
        return grpc.StatusCode.UNAVAILABLE


class OutOfRange(Exception, grpc.Call):
    __abstractmethods__ = set()  # type: ignore

    def code(self):
        return grpc.StatusCode.OUT_OF_RANGE


def test_NodeIdPool_listen(mocker):
    bits = 10
    sequence = 123

    pool = NodeIdPool("localhost", bits)

    connection_mock = mocker.patch("easyflake.node.grpc.NodeIdPool._connection")

    def infinite_reply():
        while True:
            yield SequenceReply(sequence=sequence)

    connection_mock.LiveStream.return_value = infinite_reply()

    data_iter = pool.listen()
    assert next(data_iter) == sequence


def test_NodeIdPool_listen_cancel(mocker):
    bits = 10

    pool = NodeIdPool("localhost", bits)

    connection_mock = mocker.patch("easyflake.node.grpc.NodeIdPool._connection")
    connection_mock.LiveStream.side_effect = Cancelled()  # type: ignore

    data_iter = pool.listen()
    with pytest.raises(StopIteration):
        next(data_iter)


def test_NodeIdPool_listen_server_down(mocker):
    bits = 10

    pool = NodeIdPool("localhost", bits)

    err = Unavailable()  # type: ignore

    connection_mock = mocker.patch("easyflake.node.grpc.NodeIdPool._connection")
    connection_mock.LiveStream.side_effect = err

    log_mock = mocker.patch("easyflake.logging.exception")
    data_iter = pool.listen()

    with pytest.raises(Unavailable):
        next(data_iter)

    log_mock.assert_called_once_with(err)


def test_NodeIdPool_listen_depleted(mocker):
    bits = 10
    sequence = 124

    pool = NodeIdPool("localhost", bits)

    err = OutOfRange()  # type: ignore

    connection_mock = mocker.patch("easyflake.node.grpc.NodeIdPool._connection")
    connection_mock.LiveStream.side_effect = [err, [SequenceReply(sequence=sequence)]]

    data_iter = pool.listen()
    assert next(data_iter) == sequence


@pytest.mark.asyncio
async def test_SequenceServicer_LiveStream_single_users(mocker, context_mock):
    bits = 0
    loop = 2

    service = SequenceServicer()
    request = SequenceRequest(bits=bits)

    sleep_mock = mocker.patch("asyncio.sleep")

    response_iter = service.LiveStream(request, context_mock)
    for _ in range(loop):
        rep = await anext(response_iter)
        assert rep.sequence == 0

    sleep_mock.assert_called()


@pytest.mark.asyncio
async def test_SequenceServicer_LiveStream_exit(mocker, context_mock):
    bits = 0

    service = SequenceServicer()
    request = SequenceRequest(bits=bits)

    mocker.patch("asyncio.sleep", side_effect=Cancelled)

    response_iter = service.LiveStream(request, context_mock)
    rep = await anext(response_iter)
    assert rep.sequence == 0

    with pytest.raises(Cancelled):
        await anext(response_iter)


@pytest.mark.asyncio
async def test_SequenceServicer_LiveStream_multi_users(context_mock):
    bits = 2
    loop = 4

    service = SequenceServicer()
    request = SequenceRequest(bits=bits)

    for i in range(loop):
        response_iter = service.LiveStream(request, context_mock)
        rep = await anext(response_iter)
        assert rep.sequence == i

    with pytest.raises(StopAsyncIteration):
        response_iter = service.LiveStream(request, context_mock)
        await anext(response_iter)

    context_mock.abort.assert_called_once()


def test_NodeIdPool_serve(mocker):
    mock_server = MagicMock()
    mock_server.start = AsyncMock()
    mock_server.stop = AsyncMock()
    mock_server.wait_for_termination = AsyncMock()
    mocker.patch("grpc.aio.server", return_value=mock_server)

    NodeIdPool.serve("localhost", 8080)

    mock_server.add_insecure_port.assert_called_once_with("localhost:8080")
    mock_server.start.assert_called_once()
    mock_server.wait_for_termination.assert_called_once()


@pytest.mark.skipif(sys.platform == "win32", reason="Windows not supported")
def test_NodeIdPool_serve_daemon(mocker, daemon_mode):
    mock_server = MagicMock()
    mock_server.start = AsyncMock()
    mock_server.stop = AsyncMock()
    mock_server.wait_for_termination = AsyncMock()
    mocker.patch("grpc.aio.server", return_value=mock_server)
    daemon_mock = mocker.patch("daemon.DaemonContext")

    NodeIdPool.serve("localhost", 8080)

    mock_server.add_insecure_port.assert_called_once_with("localhost:8080")
    mock_server.start.assert_called_once()
    mock_server.wait_for_termination.assert_called_once()

    daemon_mock.assert_called_once()