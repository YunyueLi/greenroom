#!/usr/bin/env bash
# greenroom core · 启动本地参考运行时。
# 用法：
#   ./start.sh                  只启动 core API 和状态页
#   ./start.sh ~/my-greenroom   挂载你的工作台（jobs/ 下岗位成为提词与模拟面试选项）
# Ctrl-C 退出。官方产品：https://greenroom.ungetsu.net/
set -euo pipefail

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
dim()  { printf "\033[2m%s\033[0m\n" "$1"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1) 环境检查：只需 python3
command -v python3 >/dev/null 2>&1 || {
  echo "✗ 需要 python3（macOS 自带；或装 https://python.org）"
  exit 1
}

# 2) 首次从模板生成 .env（不填 key 也能读工作台，只是不解锁实时助手/模拟面试）
if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  dim "已创建 .env（从 .env.example）"
fi

# 3) key 友好提示（没填也照常启动，接口会优雅降级）
if [ -f "$SCRIPT_DIR/.env" ] && grep -q "sk-your-own-key-here" "$SCRIPT_DIR/.env" 2>/dev/null; then
  echo
  bold "还没填模型 key —— 实时助手 / 模拟面试需要它（读工作台不需要）"
  echo "  1) 到 https://platform.deepseek.com 拿一个 key（便宜、常送额度）"
  echo "  2) 把 .env 里的 MODEL_API_KEY= 改成你的 key，保存后刷新页面即可"
  dim "  官方产品：https://greenroom.ungetsu.net/"
  echo
fi

# 4) 起服务（serve.py 纯标准库、自带开浏览器：http://127.0.0.1:8787/）
#    不 cd 进脚本目录，好让相对的工作台路径按你当前所在目录解析。
bold "启动 greenroom core …（Ctrl-C 退出）"
exec python3 "$SCRIPT_DIR/serve.py" "$@"
