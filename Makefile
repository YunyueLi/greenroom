# greenroom — 常用命令。`make` 或 `make dev` = 一键本地运行。
.DEFAULT_GOAL := dev
.PHONY: dev serve help

dev:   ## 一键本地运行：控制台 + 模型代理 + 自动开浏览器（= ./start.sh）
	@./start.sh

serve: ## 直接起后端（可带工作台目录：make serve DIR=~/my-greenroom）
	@python3 serve.py $(DIR)

help:  ## 列出所有命令
	@grep -hE '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:.*## / — /' | sort
