import asyncio
from aio_zmq_rpc import AioZmqRpcClient, AioZmqRpcError

client = AioZmqRpcClient('ipc:///tmp/zmqrpc1')


async def main():
    try:
        ret = await client.send_rpc('summing', 22, 33, timeout=1)
    except AioZmqRpcError as e:
        print(e)
        ret = None
    print(ret)

    # ret = await client.send_rpc('cube', 22)
    # print(ret)


asyncio.run(main())
