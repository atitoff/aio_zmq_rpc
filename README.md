# Simple and fast asyncio zmq_rpc

Вased on asynchronous ZMQ.DEALER / ZMQ.ROUTER  
dependency: pyzmq, msgpack

benchmark i5-3470  
more than 5000 per second

## install

`pip install aio-zmq-rpc`

## Use

### server
```python
import asyncio
from aio_zmq_rpc import AioZmqRpcServer, rpc

server = AioZmqRpcServer('tcp://127.0.0.1:5000')

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
```

### client

```python
import asyncio
from aio_zmq_rpc import AioZmqRpcClient, AioZmqRpcError

client = AioZmqRpcClient('tcp://127.0.0.1:5000')


async def main():
    try:
        ret = await client.send_rpc('summing', 22, 33, timeout=1)
    except AioZmqRpcError as e:
        print(e)
        ret = None
    print(ret)

    ret = await client.send_rpc('cube', 22)
    print(ret)


asyncio.run(main())
```

## What's new in version
### 0.4
added an timeout error when the server did not reply