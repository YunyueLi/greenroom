#!/usr/bin/env bash
# greenroom · 起本地服务：把工作台开成 HTTP 取数接口。
# 这里没有界面——界面是官方产品 https://greenroom.ungetsu.net/ ；
# 本仓库提供的是 skills、岗位知识库、工作台格式契约和这份取数参考服务。
# 用法：
#   ./start.sh                  只起服务（/ 返回端点清单）
#   ./start.sh ~/my-greenroom   挂载你的工作台（客户端按契约直连取数）
# Ctrl-C 退出。
set -euo pipefail

bold() { printf "\033[1m%s\033[0m\n" "$1"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1) 环境检查：只需 python3（serve.py 纯标准库，无需 Node、无需构建）
command -v python3 >/dev/null 2>&1 || {
  echo "✗ 需要 python3（macOS 自带；或装 https://python.org）"
  exit 1
}

# 2) 起服务。不 cd 进脚本目录，好让相对的工作台路径按你当前所在目录解析。
bold "启动 greenroom 本地取数服务 …（Ctrl-C 退出）"
exec python3 "$SCRIPT_DIR/serve.py" "$@"
