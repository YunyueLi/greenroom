# 工作台取数对接（workspace bridge）

Greenroom 工作台是一个本地 Markdown 文件夹，格式见 `docs/workspace-spec.md`。任何第三方工具都可以按契约直读它：阅读器、检索工具、你自己写的客户端，取的都是同一份材料。本文只讲怎么把工作台接进你自己的程序——两种取数方式、岗位切换、以及取数时的边界。工作台里的每份材料由使用者本人写定并核过口径，取数方按原文取用。

## 两种取数方式

**方式一：HTTP 直读工作台（推荐自建工具用）**。后端实现 `GET /workspace/bundle` 与 `GET /workspace/file?path=`（契约见 `docs/workspace-spec.md`「工具取数约定」），客户端即可自动直连、免选文件夹。仓库自带的 `serve.py` 是参考实现。

取数端点的响应头带 `Access-Control-Allow-Origin: *`；建议同时实现 `OPTIONS`（返回 204 与同样的 CORS 头），兼容带 JSON header 的客户端。

**方式二：程序直读工作台文件（伪代码）**：

```python
from pathlib import Path

WS = Path("~/my-greenroom").expanduser()

def read_job(slug: str) -> dict:
    base = WS / "jobs" / slug
    intel = base / "intel.md"
    return {
        "script": (base / "script.md").read_text(encoding="utf-8"),
        "intel": intel.read_text(encoding="utf-8") if intel.exists() else "",
    }
```

`intel.md` 是可选文件，读之前先判断存在。岗位切换 = 换 slug 重读，不需要在工具里硬编码任何一套材料。逐字稿解析规则见 `docs/workspace-spec.md` 的 script.md 契约。

## 立场

工作台里每个数字都在逐字稿里写定了口径和出处，所以按契约取数的工具能把用词限定在使用者本人核过的材料里。Greenroom 的主张是赛前把准备做透，剩下的判断留给使用者自己。
