#!/usr/bin/env python3
"""
快速读取配置值的脚本
不触发数据库初始化，运行速度快
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, '/app')

# 只导入 config，不导入其他可能触发数据库初始化的模块
from app.config import get_settings

# 清除缓存以确保获取最新配置
import functools
functools.lru_cache.cache_clear()

# 获取配置
settings = get_settings()

# 从命令行参数获取要读取的配置项名称
if len(sys.argv) > 1:
    config_key = sys.argv[1]
    if hasattr(settings, config_key):
        value = getattr(settings, config_key)
        print(f"{config_key}: {value}")
    else:
        print(f"Error: 配置项 '{config_key}' 不存在", file=sys.stderr)
        sys.exit(1)
else:
    # 如果没有参数，打印所有配置（隐藏敏感信息）
    print("可用配置项:")
    for key in dir(settings):
        if not key.startswith('_') and key.isupper():
            value = getattr(settings, key)
            # 隐藏敏感信息
            if 'KEY' in key or 'SECRET' in key or 'PASSWORD' in key:
                value = '***' if value else None
            print(f"  {key}: {value}")
