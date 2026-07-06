# greenroom core — 常用命令。`make` 或 `make dev` = 启动本地参考运行时。
.DEFAULT_GOAL := dev
.PHONY: dev serve help

dev:   ## 启动 core runtime（= ./start.sh）
	@./start.sh

serve: ## 直接起后端（可带工作台目录：make serve DIR=~/my-greenroom）
	@python3 serve.py $(DIR)

help:  ## 列出所有命令
	@grep -hE '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:.*## / — /' | sort
