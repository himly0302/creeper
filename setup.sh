#!/bin/bash

# Creeper 项目快速启动脚本
# 用途: 自动创建虚拟环境并安装依赖

set -e  # 遇到错误立即退出

echo "======================================"
echo "  Creeper 项目初始化脚本"
echo "======================================"
echo ""

# 检查 Python 版本
echo "📋 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3,请先安装 Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 创建虚拟环境
if [ -d "venv" ]; then
    echo "⚠️  虚拟环境已存在,跳过创建"
else
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
fi
echo ""

# 激活虚拟环境
echo "🔌 激活虚拟环境..."
source venv/bin/activate
echo "✅ 虚拟环境已激活"
echo ""

# 升级 pip
echo "⬆️  升级 pip..."
pip install --upgrade pip -q
echo "✅ pip 升级完成"
echo ""

# 安装依赖
echo "📥 安装项目依赖..."
pip install -r requirements.txt -q
echo "✅ 依赖安装完成"
echo ""

# 安装 Playwright 浏览器
echo "🎭 安装 Playwright 浏览器..."
playwright install chromium
echo "✅ Playwright 浏览器安装完成"
echo ""

# 复制配置文件
if [ ! -f ".env" ]; then
    echo "⚙️  创建配置文件..."
    cp .env.example .env
    echo "✅ 配置文件已创建: .env"
    echo "   (可根据需要编辑此文件)"
else
    echo "⚠️  配置文件已存在,跳过创建"
fi
echo ""

# 检查 Redis 连接
echo "🔍 检查 Redis 连接..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis 连接正常"
    else
        echo "⚠️  无法连接到 Redis,请检查:"
        echo "   1. Redis 服务是否运行"
        echo "   2. .env 中的 Redis 配置是否正确"
    fi
else
    echo "⚠️  未找到 redis-cli 命令"
    echo "   Redis 已在全局安装,但 redis-cli 不在 PATH 中"
    echo "   可以忽略此警告,运行时会自动连接"
fi
echo ""

echo "======================================"
echo "  🎉 初始化完成!"
echo "======================================"
echo ""
echo "下一步操作:"
echo "1. 激活虚拟环境:"
echo "   source venv/bin/activate"
echo ""
echo "2. 运行爬虫:"
echo "   python creeper.py input.md"
echo ""
echo "3. 查看帮助:"
echo "   python creeper.py --help"
echo ""
echo "4. 退出虚拟环境:"
echo "   deactivate"
echo ""
