import asyncio
from aio_zmq_rpc import AioZmqRpcServer, rpc

server = AioZmqRpcServer('ipc:///tmp/zmqrpc1')


# register rpc function 'summing'
@rpc(server, 'summing')
async def sum1(n1, n2):
    return [n1, n2]


def cube1(n1):
    return n1 ** 3


# register rpc function 'cube'
server.add(cube1, 'cube')


async def main():
    server.start()
    while True:
        await asyncio.sleep(2)


asyncio.run(main())
