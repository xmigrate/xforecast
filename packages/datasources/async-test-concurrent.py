import asyncio

async def print_hello(msg):
    a = 0
    while True:
        print(f"{msg} {a}")
        a += 1
        if a>5:
            b=2/0
        await asyncio.sleep(1)

async def test():
    #multiple tasks running con currently
    a = asyncio.gather(print_hello("hi"), print_hello("hello"))
    #a is a future object. a.done when the task is ready, refer this https://docs.python.org/3/library/asyncio-future.html#asyncio.ensure_future
    while not a.done():
       await asyncio.sleep(1)
    try:
        result = a.result()
    except asyncio.CancelledError:
        print("Someone cancelled")
    except Exception as e:
        print(f"Some error: {e}")

asyncio.run(test())