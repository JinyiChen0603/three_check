# 大模型配置数据库化设计方案

> 将大模型配置从代码迁移到数据库，让管理员可以在后台界面管理

## 一、设计目标

- 管理员可以在后台添加、编辑、删除大模型配置
- 无需修改代码即可新增或切换模型
- API Key 安全存储（加密）
- 支持启用/禁用模型

---

## 二、数据库表设计

### PostgreSQL

```sql
-- 大模型配置表
CREATE TABLE llm_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,              -- 显示名称，如 "GPT-4o"
    code VARCHAR(50) UNIQUE NOT NULL,       -- 代码标识，如 "gpt4o"（调用时用）
    description TEXT,                        -- 描述说明
    api_key_encrypted TEXT NOT NULL,        -- 加密后的 API Key
    base_url VARCHAR(255) NOT NULL,         -- API 接口地址
    model VARCHAR(100) NOT NULL,            -- 模型名称
    timeout INTEGER DEFAULT 60,             -- 超时时间（秒）
    default_temperature FLOAT DEFAULT 0.7,  -- 默认温度
    default_max_tokens INTEGER,             -- 默认最大 token（NULL 表示不限制）
    is_active BOOLEAN DEFAULT TRUE,         -- 是否启用
    sort_order INTEGER DEFAULT 0,           -- 排序顺序
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_llm_providers_code ON llm_providers(code);
CREATE INDEX idx_llm_providers_active ON llm_providers(is_active);

-- 初始数据示例
INSERT INTO llm_providers (name, code, api_key_encrypted, base_url, model, timeout, default_temperature) VALUES
('GPT-4o', 'gpt4o', '加密后的key', 'https://openrouter.ai/api/v1/chat/completions', 'openai/gpt-4o', 60, 0.7),
('GPT-4o 代理', 'gpt4o_proxy', '加密后的key', 'https://www.stem-align.com/v2/openrouter/api/v1/chat/completions', 'openai/gpt-4o', 90, 0.7),
('DeepSeek Math', 'deepseek_math', '加密后的key', 'https://api.canopywave.io/v1/chat/completions', 'deepseek-ai/DeepSeek-Math-V2', 90, 0.8),
('智谱 GLM-4', 'zhipu_glm', '加密后的key', 'https://open.bigmodel.cn/api/paas/v4/chat/completions', 'glm-4-plus', 90, 0.7),
('豆包', 'doubao', '加密后的key', 'https://ark.cn-beijing.volces.com/api/v3/chat/completions', 'doubao-seed-1-6-thinking-250715', 120, 0.7);
```

### SQLAlchemy Model

```python
# backend/app/models/llm_provider.py

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class LLMProvider(Base):
    """大模型配置表"""
    __tablename__ = "llm_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, comment="显示名称")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="代码标识")
    description = Column(Text, comment="描述说明")
    api_key_encrypted = Column(Text, nullable=False, comment="加密后的 API Key")
    base_url = Column(String(255), nullable=False, comment="API 接口地址")
    model = Column(String(100), nullable=False, comment="模型名称")
    timeout = Column(Integer, default=60, comment="超时时间（秒）")
    default_temperature = Column(Float, default=0.7, comment="默认温度")
    default_max_tokens = Column(Integer, nullable=True, comment="默认最大 token")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

---

## 三、API Key 加密方案

使用 `cryptography` 库进行对称加密：

```python
# backend/app/utils/encryption.py

from cryptography.fernet import Fernet
from app.config import settings

# 使用 SECRET_KEY 派生加密密钥
def get_fernet():
    # 从 SECRET_KEY 生成 32 字节的 key
    import hashlib
    import base64
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    key_b64 = base64.urlsafe_b64encode(key)
    return Fernet(key_b64)

def encrypt_api_key(api_key: str) -> str:
    """加密 API Key"""
    f = get_fernet()
    return f.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """解密 API Key"""
    f = get_fernet()
    return f.decrypt(encrypted_key.encode()).decode()
```

---

## 四、动态客户端服务

```python
# backend/app/services/llm/dynamic_client.py

import httpx
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.llm_provider import LLMProvider
from app.utils.encryption import decrypt_api_key


class DynamicLLMClient:
    """动态大模型客户端，从数据库读取配置"""
    
    # 缓存
    _cache: Dict[str, "DynamicLLMClient"] = {}
    
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 60.0,
        default_temperature: float = 0.7,
        default_max_tokens: Optional[int] = None
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
    
    @classmethod
    async def get_client(cls, db: AsyncSession, code: str) -> "DynamicLLMClient":
        """
        根据代码获取客户端（带缓存）
        
        Args:
            db: 数据库会话
            code: 模型代码，如 "gpt4o"
            
        Returns:
            DynamicLLMClient 实例
        """
        # 检查缓存
        if code in cls._cache:
            return cls._cache[code]
        
        # 从数据库查询
        result = await db.execute(
            select(LLMProvider).where(
                LLMProvider.code == code,
                LLMProvider.is_active == True
            )
        )
        provider = result.scalar_one_or_none()
        
        if not provider:
            raise ValueError(f"未找到模型配置: {code}")
        
        # 解密 API Key
        api_key = decrypt_api_key(provider.api_key_encrypted)
        
        # 创建客户端
        client = cls(
            api_key=api_key,
            base_url=provider.base_url,
            model=provider.model,
            timeout=provider.timeout,
            default_temperature=provider.default_temperature,
            default_max_tokens=provider.default_max_tokens
        )
        
        # 存入缓存
        cls._cache[code] = client
        return client
    
    @classmethod
    def clear_cache(cls, code: Optional[str] = None):
        """
        清除缓存
        
        Args:
            code: 指定代码则只清除该缓存，否则清除全部
        """
        if code:
            cls._cache.pop(code, None)
        else:
            cls._cache.clear()
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """调用大模型聊天接口"""
        
        # 使用传入值或默认值
        temp = temperature if temperature is not None else self.default_temperature
        
        # 构建请求体
        request_body = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
            **kwargs
        }
        
        # max_tokens 处理
        tokens = max_tokens if max_tokens is not None else self.default_max_tokens
        if tokens is not None:
            request_body["max_tokens"] = tokens
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_body
            )
            response.raise_for_status()
            return response.json()
```

---

## 五、管理后台 API

```python
# backend/app/api/admin/llm_providers.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models.llm_provider import LLMProvider
from app.utils.encryption import encrypt_api_key, decrypt_api_key
from app.services.llm.dynamic_client import DynamicLLMClient

router = APIRouter(prefix="/admin/llm-providers", tags=["管理-大模型配置"])


@router.get("/", response_model=List[LLMProviderResponse])
async def list_providers(db: AsyncSession = Depends(get_db)):
    """获取所有大模型配置"""
    result = await db.execute(select(LLMProvider).order_by(LLMProvider.sort_order))
    return result.scalars().all()


@router.post("/")
async def create_provider(data: LLMProviderCreate, db: AsyncSession = Depends(get_db)):
    """创建大模型配置"""
    provider = LLMProvider(
        name=data.name,
        code=data.code,
        description=data.description,
        api_key_encrypted=encrypt_api_key(data.api_key),  # 加密存储
        base_url=data.base_url,
        model=data.model,
        timeout=data.timeout,
        default_temperature=data.default_temperature,
        default_max_tokens=data.default_max_tokens,
        is_active=data.is_active
    )
    db.add(provider)
    await db.commit()
    return {"message": "创建成功", "id": provider.id}


@router.put("/{provider_id}")
async def update_provider(provider_id: int, data: LLMProviderUpdate, db: AsyncSession = Depends(get_db)):
    """更新大模型配置"""
    provider = await db.get(LLMProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 更新字段...
    if data.api_key:
        provider.api_key_encrypted = encrypt_api_key(data.api_key)
    
    await db.commit()
    
    # 清除缓存
    DynamicLLMClient.clear_cache(provider.code)
    
    return {"message": "更新成功"}


@router.delete("/{provider_id}")
async def delete_provider(provider_id: int, db: AsyncSession = Depends(get_db)):
    """删除大模型配置"""
    provider = await db.get(LLMProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    code = provider.code
    await db.delete(provider)
    await db.commit()
    
    # 清除缓存
    DynamicLLMClient.clear_cache(code)
    
    return {"message": "删除成功"}


@router.post("/{provider_id}/test")
async def test_provider(provider_id: int, db: AsyncSession = Depends(get_db)):
    """测试大模型连接"""
    provider = await db.get(LLMProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    try:
        client = await DynamicLLMClient.get_client(db, provider.code)
        result = await client.chat(
            messages=[{"role": "user", "content": "你好，请回复'连接成功'"}],
            max_tokens=50
        )
        content = result["choices"][0]["message"]["content"]
        return {"success": True, "response": content}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

## 六、前端管理界面设计

```
┌─────────────────────────────────────────────────────────────────────┐
│  大模型配置管理                                      [+ 添加模型]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ GPT-4o                                          ✅ 已启用    │   │
│  │ 代码: gpt4o                                                  │   │
│  │ 模型: openai/gpt-4o                                         │   │
│  │ 接口: https://openrouter.ai/api/v1/chat/completions         │   │
│  │                                    [测试] [编辑] [删除]      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 智谱 GLM-4                                      ✅ 已启用    │   │
│  │ 代码: zhipu_glm                                              │   │
│  │ 模型: glm-4-plus                                            │   │
│  │ 接口: https://open.bigmodel.cn/api/paas/v4/chat/completions │   │
│  │                                    [测试] [编辑] [删除]      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 添加/编辑表单

```
┌─────────────────────────────────────────────────┐
│  添加大模型配置                              ✕  │
├─────────────────────────────────────────────────┤
│                                                 │
│  显示名称 *                                     │
│  ┌─────────────────────────────────────────┐   │
│  │ GPT-4o                                   │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  代码标识 *（用于调用，不可重复）                │
│  ┌─────────────────────────────────────────┐   │
│  │ gpt4o                                    │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  API Key *                                      │
│  ┌─────────────────────────────────────────┐   │
│  │ sk-xxxxxxxxxxxx                          │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  接口地址 *                                     │
│  ┌─────────────────────────────────────────┐   │
│  │ https://openrouter.ai/api/v1/chat/...   │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  模型名称 *                                     │
│  ┌─────────────────────────────────────────┐   │
│  │ openai/gpt-4o                            │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  超时时间（秒）         默认温度                 │
│  ┌──────────────┐      ┌──────────────┐        │
│  │ 60           │      │ 0.7          │        │
│  └──────────────┘      └──────────────┘        │
│                                                 │
│  ☑ 启用                                        │
│                                                 │
│              [取消]    [保存]                   │
└─────────────────────────────────────────────────┘
```

---

## 七、使用方式对比

### 代码配置方式（当前）

```python
from app.services.llm import gpt4o

result = await gpt4o.chat(messages=[...])
```

### 数据库配置方式（未来）

```python
from app.services.llm.dynamic_client import DynamicLLMClient

client = await DynamicLLMClient.get_client(db, "gpt4o")
result = await client.chat(messages=[...])
```

---

## 八、实施步骤

1. **第一阶段**（当前）：使用代码配置 `clients.py`，跑通功能
2. **第二阶段**：创建数据库表和模型
3. **第三阶段**：实现加密工具和动态客户端
4. **第四阶段**：开发管理后台 API
5. **第五阶段**：开发前端管理界面
6. **第六阶段**：迁移数据，测试上线

---

## 九、注意事项

1. **API Key 安全**：必须加密存储，日志中不要打印
2. **缓存刷新**：管理员修改配置后要清除缓存
3. **兜底方案**：数据库不可用时，可以回退到代码配置
4. **权限控制**：只有管理员可以访问配置管理接口
5. **操作日志**：记录配置变更历史

