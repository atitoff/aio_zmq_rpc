import asyncio
import zmq
import zmq.asyncio
import msgpack


def rpc(instance, name):
    def my_decorator(func):
        instance.add(func, name)

    return my_decorator


class AioZmqRpcError(Exception):
    def __init__(self, text):
        self.text = text


class AioZmqRpcServer:

    def __init__(self, url):
        self.url = url
        self._sock = None
        self._task_receive = None
        #
        self._function_dict = {}  # {name_rpc_method: function}

    def start(self):
        if self._task_receive is None:
            ctx = zmq.asyncio.Context()
            self._sock = ctx.socket(zmq.ROUTER)
            self._sock.bind(self.url)
            self._task_receive = asyncio.create_task(self._receive())

    def add(self, fn, name):
        self._function_dict.update({name: fn})

    async def _receive(self):
        while True:
            msg = await self._sock.recv_multipart()
            # msg[0] - ZMQ ROUTER session id
            # msg[1] - token
            # msg[2] - arguments
            asyncio.create_task(self._worker(msg))

    async def _worker(self, msg):
        ret = {}
        input_data = msgpack.loads(msg[2])
        if input_data['method'] in self._function_dict:
            fn = self._function_dict[input_data['method']]
            try:
                if asyncio.iscoroutinefunction(fn):
                    try:
                        result = await asyncio.wait_for(fn(*input_data['params']), timeout=input_data['timeout'])
                        ret.update({'result': result})
                    except asyncio.TimeoutError:
                        print('timeout!')
                        ret.update({"error": {"code": -32000, "message": f"Timeout error"}})
                    # result = await fn(*input_data['params'])
                else:
                    result = fn(*input_data['params'])
                    ret.update({'result': result})
            except TypeError as e:
                ret.update({"error": {"code": -32602, "message": f"Invalid params {e}"}})
        else:
            ret.update({"error": {"code": -32601, "message": f"Procedure {input_data['method']} not found."}})

        self._sock.send_multipart([msg[0], msg[1], msgpack.dumps(ret)])

    def __del__(self):
        self._sock.close()
        self._task_receive.cancel()


class AioZmqRpcClient:
    def __init__(self, url):
        self.url = url
        self._sock = None
        self._token_dict = {}
        self._task_receive = None
        self._msg_id = 0

    async def send_rpc(self, rpc_name, *arg, timeout=10):
        if not self._task_receive:
            ctx = zmq.asyncio.Context()
            self._sock = ctx.socket(zmq.DEALER)
            self._sock.connect(self.url)
            self._task_receive = asyncio.create_task(self._receive())
        arg = msgpack.dumps({'method': rpc_name, 'params': arg, 'timeout': timeout})
        # token = secrets.token_bytes(64)
        token = self._token()
        event = asyncio.Event()
        self._token_dict.update({token: [event, '']})
        self._sock.send_multipart([token, arg])
        timeout_connect = False
        try:
            await asyncio.wait_for(event.wait(), timeout+1)  # timeout connect to RPC server
        except asyncio.TimeoutError:
            timeout_connect = True

        ret = self._token_dict[token][1]
        self._token_dict.pop(token)

        if timeout_connect:
            ret = dict()
            ret['error'] = 'connect to RPC server timeout error'
        else:
            ret = msgpack.loads(ret)
        print('self._token_dict', self._token_dict)
        if 'error' in ret:
            raise AioZmqRpcError(ret['error'])

        return ret['result']

    async def _receive(self):
        while True:
            token, msg = await self._sock.recv_multipart()
            if token in self._token_dict:
                self._token_dict[token][1] = msg
                self._token_dict[token][0].set()

    def _token(self):
        self._msg_id += 1
        return self._msg_id.to_bytes((self._msg_id.bit_length() + 7) // 8, 'big')

    def __del__(self):
        self._task_receive.cancel()
        self._sock.close()
