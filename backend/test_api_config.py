"""测试 API 配置是否正确"""
import asyncio
from app.config import settings
from app.services.llm import gpt52_research, gpt52_with_reasoning

async def test_config():
    print("="*60)
    print("测试 API 配置")
    print("="*60)
    
    # 1. 检查配置是否加载
    print(f"\n1. 检查环境变量:")
    if settings.OPENAI_API_KEY:
        key_preview = settings.OPENAI_API_KEY[:10] + "..." if len(settings.OPENAI_API_KEY) > 10 else "太短"
        print(f"   [OK] OPENAI_API_KEY: {key_preview}")
    else:
        print(f"   [FAIL] OPENAI_API_KEY: 未配置")
        return
    
    # 2. 测试严谨性检测 API（不需要联网）
    print(f"\n2. 测试严谨性检测 API（GPT-5.2 基础调用）:")
    try:
        from app.services.rigor_check_service import rigor_check_service
        result = await rigor_check_service.check_rigor(
            problem="1+1等于多少？",
            answer="2"
        )
        if result.get('success'):
            print(f"   [OK] 严谨性检测 API 正常")
            print(f"   判断结果: {result.get('verdict')}")
        else:
            print(f"   [FAIL] 严谨性检测失败: {result.get('error')}")
    except Exception as e:
        print(f"   [FAIL] 严谨性检测异常: {e}")
    
    # 3. 测试原创性检测 API（需要联网搜索）
    print(f"\n3. 测试原创性检测 API（GPT-5.2 + web_search）:")
    try:
        from app.services.originality_check_service import originality_check_service
        result = await originality_check_service.check_originality(
            problem="求解方程 x^2 = 4"
        )
        if result.get('success'):
            print(f"   [OK] 原创性检测 API 正常")
            print(f"   判断结果: {result.get('verdict')}")
        else:
            print(f"   [FAIL] 原创性检测失败: {result.get('error')}")
    except Exception as e:
        print(f"   [FAIL] 原创性检测异常: {e}")
    
    print(f"\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_config())

