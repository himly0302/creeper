#!/bin/bash

# Creeper 测试环境清理脚本
# 用途: 清空 Redis 数据和删除输出文件,便于重新测试

set -e  # 遇到错误立即退出

echo "======================================"
echo "  Creeper 测试环境清理脚本"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 确认操作
echo -e "${YELLOW}⚠️  警告: 此操作将清空以下内容:${NC}"
echo "  1. Redis 中所有 'creeper:' 开头的键"
# echo "  2. output/ 和 outputs/ 目录下的所有爬虫输出文件"
echo "  3. parsers/ 目录下的所有解析文件"
echo "  4. aggregators/ 目录下的所有整合文件"
# echo "  5. creeper.log 日志文件"
echo "  6. data/ 目录下的所有本地缓存文件"
echo ""
read -p "确认继续? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消操作"
    exit 0
fi

echo ""
echo "开始清理..."
echo ""

# 1. 清空 Redis
echo "🗑️  清空 Redis 数据..."
if command -v redis-cli &> /dev/null; then
    # 加载 .env 配置(只加载需要的变量)
    if [ -f .env ]; then
        REDIS_HOST=$(grep "^REDIS_HOST=" .env | cut -d '=' -f2)
        REDIS_PORT=$(grep "^REDIS_PORT=" .env | cut -d '=' -f2)
        REDIS_DB=$(grep "^REDIS_DB=" .env | cut -d '=' -f2)
        REDIS_PASSWORD=$(grep "^REDIS_PASSWORD=" .env | cut -d '=' -f2)
    fi

    # 设置默认值
    REDIS_HOST=${REDIS_HOST:-localhost}
    REDIS_PORT=${REDIS_PORT:-6379}
    REDIS_DB=${REDIS_DB:-1}
    REDIS_PASSWORD=${REDIS_PASSWORD:-}

    # 构建 redis-cli 命令
    REDIS_CMD="redis-cli -h $REDIS_HOST -p $REDIS_PORT -n $REDIS_DB"
    if [ -n "$REDIS_PASSWORD" ]; then
        REDIS_CMD="$REDIS_CMD -a $REDIS_PASSWORD"
    fi

    # 获取匹配的键数量
    KEY_COUNT=$($REDIS_CMD --no-auth-warning KEYS "creeper:*" 2>/dev/null | wc -l)

    if [ "$KEY_COUNT" -gt 0 ]; then
        # 删除所有匹配的键
        $REDIS_CMD --no-auth-warning KEYS "creeper:*" 2>/dev/null | xargs $REDIS_CMD --no-auth-warning DEL > /dev/null 2>&1
        echo -e "${GREEN}✓ 已删除 $KEY_COUNT 个 Redis 键${NC}"
    else
        echo -e "${GREEN}✓ Redis 中没有需要清理的数据${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  未找到 redis-cli,跳过 Redis 清理${NC}"
fi
echo ""

# 2. 删除输出目录
# echo "🗑️  删除爬虫输出文件..."
# TOTAL_FILES=0

# # 删除 output/ 目录
# if [ -d "output" ]; then
#     FILE_COUNT=$(find output -type f 2>/dev/null | wc -l)
#     rm -rf output/*
#     TOTAL_FILES=$((TOTAL_FILES + FILE_COUNT))
#     echo -e "${GREEN}✓ 已删除 output/ 目录下的 $FILE_COUNT 个文件${NC}"
# else
#     echo -e "${GREEN}✓ output/ 目录不存在,跳过${NC}"
# fi

# # 删除 outputs/ 目录（约定名称）
# if [ -d "outputs" ]; then
#     FILE_COUNT=$(find outputs -type f 2>/dev/null | wc -l)
#     rm -rf outputs/*
#     TOTAL_FILES=$((TOTAL_FILES + FILE_COUNT))
#     echo -e "${GREEN}✓ 已删除 outputs/ 目录下的 $FILE_COUNT 个文件${NC}"
# else
#     echo -e "${GREEN}✓ outputs/ 目录不存在,跳过${NC}"
# fi

# if [ "$TOTAL_FILES" -gt 0 ]; then
#     echo -e "${GREEN}  共删除 $TOTAL_FILES 个爬虫输出文件${NC}"
# fi
# echo ""

# 3. 删除解析文件目录
echo "🗑️  删除解析文件..."
if [ -d "parsers" ]; then
    FILE_COUNT=$(find parsers -type f 2>/dev/null | wc -l)
    rm -rf parsers/*
    echo -e "${GREEN}✓ 已删除 parsers/ 目录下的 $FILE_COUNT 个文件${NC}"
else
    echo -e "${GREEN}✓ parsers/ 目录不存在,跳过${NC}"
fi
echo ""

# 4. 删除整合文件目录
echo "🗑️  删除整合文件..."
if [ -d "aggregators" ]; then
    FILE_COUNT=$(find aggregators -type f 2>/dev/null | wc -l)
    rm -rf aggregators/*
    echo -e "${GREEN}✓ 已删除 aggregators/ 目录下的 $FILE_COUNT 个文件${NC}"
else
    echo -e "${GREEN}✓ aggregators/ 目录不存在,跳过${NC}"
fi
echo ""

# 5. 删除日志文件
# echo "🗑️  删除日志文件..."
# if [ -f "creeper.log" ]; then
#     LOG_SIZE=$(du -h creeper.log | cut -f1)
#     rm -f creeper.log
#     echo -e "${GREEN}✓ 已删除 creeper.log ($LOG_SIZE)${NC}"
# else
#     echo -e "${GREEN}✓ creeper.log 不存在,跳过${NC}"
# fi
# echo ""

# 6. 删除测试输出的失败记录
echo "🗑️  删除失败 URL 记录..."
FAILED_COUNT=0
if [ -d "output" ]; then
    FAILED_COUNT=$(find output -name "failed_urls_*.txt" 2>/dev/null | wc -l)
    if [ "$FAILED_COUNT" -gt 0 ]; then
        find output -name "failed_urls_*.txt" -delete 2>/dev/null
    fi
fi
if [ -d "outputs" ]; then
    FAILED_COUNT_2=$(find outputs -name "failed_urls_*.txt" 2>/dev/null | wc -l)
    FAILED_COUNT=$((FAILED_COUNT + FAILED_COUNT_2))
    if [ "$FAILED_COUNT_2" -gt 0 ]; then
        find outputs -name "failed_urls_*.txt" -delete 2>/dev/null
    fi
fi
if [ "$FAILED_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ 已删除 $FAILED_COUNT 个失败记录文件${NC}"
else
    echo -e "${GREEN}✓ 没有失败记录文件${NC}"
fi
echo ""

# 7. 删除所有本地缓存文件
echo "🗑️  删除本地缓存文件..."
CACHE_COUNT=0
CACHE_FILES=(
    "data/dedup_cache.json"
    "data/cookies_cache.json"
    "data/aggregator_cache.json"
    "data/parser_cache.json"
)

for cache_file in "${CACHE_FILES[@]}"; do
    if [ -f "$cache_file" ]; then
        rm -f "$cache_file"
        CACHE_COUNT=$((CACHE_COUNT + 1))
        echo -e "${GREEN}✓ 已删除 $cache_file${NC}"
    fi
done

if [ "$CACHE_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ 没有本地缓存文件${NC}"
else
    echo -e "${GREEN}  共删除 $CACHE_COUNT 个本地缓存文件${NC}"
fi
echo ""

echo "======================================"
echo -e "${GREEN}  ✅ 清理完成!${NC}"
echo "======================================"
echo ""
echo "现在可以重新运行测试:"
echo "  source venv/bin/activate"
echo "  python creeper.py inputs/input.md"
echo ""
