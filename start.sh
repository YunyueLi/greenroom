#!/usr/bin/env bash
# greenroom · 起本地后端：工作台取数 + 实时提词 + 模拟面试的 HTTP 接口。
# 这里没有界面——界面是官方产品 https://greenroom.ungetsu.net/ ；
# 本仓库提供的是 skills、岗位知识库、工作台格式契约和这份参考后端。
# 用法：
#   ./start.sh                  只起服务（/ 返回端点清单）
#   ./start.sh ~/my-greenroom   挂载你的工作台（jobs/ 下岗位成为提词与模拟面试选项）
# Ctrl-C 退出。
set -euo pipefail

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
dim()  { printf "\033[2m%s\033[0m\n" "$1"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1) 环境检查：只需 python3（serve.py 纯标准库，无需 Node、无需构建）
command -v python3 >/dev/null 2>&1 || {
  echo "✗ 需要 python3（macOS 自带；或装 https://python.org）"
  exit 1
}

# 2) 首次从模板生成 .env（不填 key 也能跑：工作台取数照常，只是不解锁实时提词/模拟面试）
if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  dim "已创建 .env（从 .env.example）"
fi

# 3) key 友好提示（没填也照常启动，服务会优雅降级）
if [ -f "$SCRIPT_DIR/.env" ] && grep -q "sk-your-own-key-here" "$SCRIPT_DIR/.env" 2>/dev/null; then
  echo
  bold "还没填模型 key —— /api/answer、/api/mock、/api/setup 需要它（工作台取数不需要）"
  echo "  1) 到 https://platform.deepseek.com 拿一个 key（便宜、常送额度）"
  echo "  2) 把 .env 里的 MODEL_API_KEY= 改成你的 key，保存后重启即可"
  dim "  （不想自己搭？直接用线上版 https://greenroom.ungetsu.net/）"
  echo
fi

# 4) 起服务。不 cd 进脚本目录，好让相对的工作台路径按你当前所在目录解析。
bold "启动 greenroom 本地后端 …（Ctrl-C 退出）"
exec python3 "$SCRIPT_DIR/serve.py" "$@"
