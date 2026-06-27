# backports.interpreters

![Python package](https://github.com/aisk/backports.interpreters/workflows/Python%20package/badge.svg)

![](https://steamuserimages-a.akamaihd.net/ugc/884253767814091683/33BD3074E50D3E841C647E8BEE4CF680C35B152D/)

The `concurrent.interpreters` module ([PEP 734](https://peps.python.org/pep-0734/)), backported from the future. It lands in the standard library in Python 3.14, and this package provides it for 3.8 through 3.13. On 3.14+ it just re-exports the real thing.

## Install

```sh
$ pip install backports.interpreters
```

## Example

```python
from backports import interpreters
import threading


def task():
    interp = interpreters.create()
    interp.exec("""
a = 0
for i in range(99999999):
    a += i
print(a)
    """)


ts = []
for _ in range(8):
    t = threading.Thread(target=task)
    t.start()
    ts.append(t)

for t in ts:
    t.join()
```

Run this with Python 3.12+ and you will see Python use 8 cores of CPU:

![Python eats 8 CPU cores](https://i.v2ex.co/m80gRd7P.png)

Interpreters talk over queues, and you can call a function in one and get its result back:

```python
from backports import interpreters

def add(a, b):
    return a + b

interp = interpreters.create()
print(interp.call(add, 2, 3))  # 5
interp.close()
```

## Limitations

Real parallelism needs the per-interpreter GIL from [PEP 684](https://peps.python.org/pep-0684/), so it only kicks in on Python 3.12+. On 3.8 through 3.11 the API works but everything shares one GIL. Before 3.14, `call()` only accepts plain functions with no closure or free variables. Before 3.13, `Queue.qsize()` and `Queue.empty()` are unavailable because the channel underneath cannot report its size.

---

「すべてはシュタインズ・ゲートの選択である」
