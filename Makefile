# greenroom — 常用命令。`make` 或 `make dev` = 一键起本地取数服务。
.DEFAULT_GOAL := dev
.PHONY: dev serve help

dev:   ## 一键起本地服务：把工作台开成 HTTP 取数接口（= ./start.sh）
	@./start.sh

serve: ## 直接起服务（可带工作台目录：make serve DIR=~/my-greenroom）
	@python3 serve.py $(DIR)

help:  ## 列出所有命令
	@grep -hE '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:.*## / — /' | sort
