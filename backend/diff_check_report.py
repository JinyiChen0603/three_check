"""
难度检测报告导出工具

功能：
1. 自动登录获取 token
2. 从 API 获取所有难度检测报告
3. 导出为 JSON 文件

使用方法：
    python diff_check_report.py

配置说明：
    默认从 .env 文件读取配置，也可以直接修改下面的配置项
"""

import requests
import json
import os
import sys
from datetime import datetime
from pathlib import Path


# ==================== 配置区域 ====================

# API 地址（默认本地开发环境）
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

# 用户凭证（优先从环境变量读取，否则使用默认值）
USERNAME = os.getenv("EXPORT_USERNAME", "chenjinyi")  # 修改为您的用户名
PASSWORD = os.getenv("EXPORT_PASSWORD", "user123")  # 修改为您的密码

# 输出文件名（自动添加时间戳）
OUTPUT_DIR = "exports"  # 导出目录
OUTPUT_FILENAME_PREFIX = "difficulty_reports"  # 文件名前缀

# ===================================================


class DifficultyReportExporter:
    """难度检测报告导出器"""
    
    def __init__(self, api_base_url: str, username: str, password: str):
        self.api_base_url = api_base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
    
    def login(self) -> bool:
        """登录获取 token"""
        print("🔐 正在登录...")
        
        try:
            response = requests.post(
                f"{self.api_base_url}/api/auth/login",
                data={
                    "username": self.username,
                    "password": self.password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                print(f"✅ 登录成功！用户: {self.username}")
                return True
            else:
                print(f"❌ 登录失败 (状态码: {response.status_code})")
                print(f"   错误信息: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到服务器: {self.api_base_url}")
            print("   请确保后端服务正在运行")
            return False
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
            return False
        except Exception as e:
            print(f"❌ 登录时发生错误: {e}")
            return False
    
    def get_reports(self) -> dict:
        """获取难度检测报告"""
        print("📥 正在获取难度检测报告...")
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_base_url}/api/problems/export-list",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功获取报告数据")
                return data
            elif response.status_code == 401:
                print("❌ 认证失败，token 可能已过期")
                return None
            else:
                print(f"❌ 获取报告失败 (状态码: {response.status_code})")
                print(f"   错误信息: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
            return None
        except Exception as e:
            print(f"❌ 获取报告时发生错误: {e}")
            return None
    
    def save_to_json(self, data: dict, output_path: str) -> bool:
        """保存为 JSON 文件"""
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"❌ 保存文件时发生错误: {e}")
            return False
    
    def export(self) -> bool:
        """执行完整的导出流程"""
        # 1. 登录
        if not self.login():
            return False
        
        # 2. 获取报告
        data = self.get_reports()
        if not data:
            return False
        
        # 3. 生成输出文件名（带时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{OUTPUT_FILENAME_PREFIX}_{timestamp}.json"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # 4. 保存文件
        print(f"💾 正在保存到文件...")
        if not self.save_to_json(data, output_path):
            return False
        
        # 5. 显示统计信息
        print("\n" + "="*60)
        print("✅ 导出成功！")
        print("="*60)
        print(f"📊 总题目数:   {data.get('total', 0)}")
        print(f"✓  通过题目:   {data.get('passed', 0)}")
        print(f"✗  未通过题目: {data.get('failed', 0)}")
        print(f"📁 文件路径:   {os.path.abspath(output_path)}")
        print(f"📦 文件大小:   {os.path.getsize(output_path) / 1024:.2f} KB")
        print("="*60)
        
        # 6. 显示题目详情（可选）
        if data.get('problems'):
            print(f"\n前 5 个题目预览：")
            for i, problem in enumerate(data['problems'][:5], 1):
                print(f"\n题目 {i} (ID: {problem.get('id')})")
                print(f"  内容: {problem.get('content', '')[:50]}...")
                print(f"  难度通过: {problem.get('difficulty_passed', False)}")
                print(f"  原创性通过: {problem.get('originality_passed', False)}")
                print(f"  严谨性通过: {problem.get('rigor_passed', False)}")
        
        return True


def main():
    """主函数"""
    print("\n" + "="*60)
    print("   难度检测报告导出工具 v1.0")
    print("="*60 + "\n")
    
    # 检查配置
    if USERNAME == "admin" and PASSWORD == "admin123":
        print("⚠️  警告: 正在使用默认用户名和密码")
        print("   如需修改，请编辑脚本顶部的配置或设置环境变量\n")
    
    print(f"🌐 API 地址: {API_BASE_URL}")
    print(f"👤 用户名: {USERNAME}\n")
    
    # 创建导出器并执行
    exporter = DifficultyReportExporter(API_BASE_URL, USERNAME, PASSWORD)
    
    success = exporter.export()
    
    if success:
        sys.exit(0)
    else:
        print("\n❌ 导出失败")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

