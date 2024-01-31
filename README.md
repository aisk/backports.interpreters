# backports.interpreters

![Python package](https://github.com/aisk/backports.interpreters/workflows/Python%20package/badge.svg)

![](https://steamuserimages-a.akamaihd.net/ugc/884253767814091683/33BD3074E50D3E841C647E8BEE4CF680C35B152D/)

The `interpreters` module described in [PEP554](https://www.python.org/dev/peps/pep-0554/), which is not implemented now. This is backported from the future.

## Install

```sh
$ pip install backports.interpreters
```

## Example

```sh
from backports import interpreters
import threading


def task():
    intp = interpreters.create()
    intp.run("""
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

Run this code with Python3.12, you will see Python will use 8 cores of CPU:

![Python eats 8 CPU cores](https://i.v2ex.co/m80gRd7P.png)

## Limitations

Only support python3.8+.

---

「すべてはシュタインズ・ゲートの選択である」
