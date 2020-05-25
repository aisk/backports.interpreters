# backports.interpreters

![](https://steamuserimages-a.akamaihd.net/ugc/884253767814091683/33BD3074E50D3E841C647E8BEE4CF680C35B152D/)

The `interpreters` module described in [PEP554](https://www.python.org/dev/peps/pep-0554/), which is not implemented now. This is backported from the future.

## Install

```sh
$ pip install backports.interpreters
```

## Usage

```sh
from backports import interpreters

interp = interpreters.create()
interp.run("print('El Psy Congroo.')")
interp.close()
```

## Limitations

Only support python3.8+.

---

「すべてはシュタインズ・ゲートの選択である」
