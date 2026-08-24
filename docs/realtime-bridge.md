# 工作台文件对接（workspace bridge）

Greenroom 工作台是一组可迁移的 Markdown 文件，格式见 `docs/workspace-spec.md`。阅读器、检索工具或个人脚本可以在使用者明确选择目录后直接读取同一份材料。本文只说明文件读取、岗位切换和权限边界；它不是 Greenroom 产品后端或本地部署说明。

## 程序直接读取文件

下面的 Python 示例从调用者显式传入的工作台路径读取材料：

```python
from pathlib import Path

def read_job(workspace: Path, slug: str) -> dict:
    root = workspace.expanduser().resolve(strict=True)
    base = (root / "jobs" / slug).resolve(strict=True)
    if root not in base.parents:
        raise ValueError("job path escapes the selected workspace")

    def selected_file(name: str, *, required: bool = True) -> Path | None:
        path = base / name
        if not path.exists() and not required:
            return None
        resolved = path.resolve(strict=True)
        if base != resolved and base not in resolved.parents:
            raise ValueError("file path escapes the selected job")
        return resolved

    script = selected_file("script.md")
    intel = selected_file("intel.md", required=False)
    return {
        "script": script.read_text(encoding="utf-8"),
        "intel": intel.read_text(encoding="utf-8") if intel else "",
    }
```

`intel.md` 是可选文件，读之前先判断存在。岗位切换就是更换 `slug` 后重新读取，不需要在工具里硬编码任何一套材料。逐字稿解析规则见 `docs/workspace-spec.md` 的 `script.md` 契约。

浏览器应用不能静默读取本机目录。应让使用者通过文件选择、目录选择或拖放主动授权；如果浏览器保存了目录句柄，也应显示授权状态并提供断开入口。不要探测 `localhost`、回环端口或其他本地服务。

## 安全与隐私边界

- 只读取使用者明确选择的目录和完成当前任务所需的文件。
- 对任何相对路径做根目录约束，拒绝 `..`、符号链接绕过和其他越界访问。
- 未经明确说明和同意，不把简历、岗位材料或面试记录上传到第三方。
- 本仓库不提供 Greenroom 本地 HTTP 运行时；需要账号、同步、托管模型、额度或支付的能力均属于官方托管产品。

## 立场

工作台里每个数字都应在逐字稿里写明口径和出处，因此按契约读取的工具可以把用词限定在使用者本人核过的材料里。Greenroom 的主张是赛前把准备做透，剩下的判断留给使用者自己。
