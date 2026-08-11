# greenroom — 常用命令。`make` 或 `make dev` = 一键起本地后端。
.DEFAULT_GOAL := dev
.PHONY: dev serve help

dev:   ## 一键起本地后端：工作台取数 + 实时提词 + 模拟面试接口（= ./start.sh）
	@./start.sh

serve: ## 直接起后端（可带工作台目录：make serve DIR=~/my-greenroom）
	@python3 serve.py $(DIR)

help:  ## 列出所有命令
	@grep -hE '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:.*## / — /' | sort
