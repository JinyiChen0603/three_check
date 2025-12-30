"""
进度追踪服务模块
用于存储和订阅异步任务的进度状态
"""

import json
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator

from app.services.redis_client import get_redis
from app.config import settings


class ProgressService:
    """
    进度追踪服务
    
    使用 Redis 存储任务进度，支持：
    - 更新进度
    - 获取当前进度（用于刷新恢复）
    - 订阅进度变化（用于 SSE 推送）
    """
    
    KEY_PREFIX = "diff_progress:"
    
    async def update_progress(
        self,
        task_id: str,
        progress: int,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        更新任务进度
        
        Args:
            task_id: 任务唯一标识
            progress: 进度百分比 (0-100)
            result: 可选的最终结果（任务完成时传入）
        """
        redis_client = get_redis()
        if not redis_client:
            return
        
        key = f"{self.KEY_PREFIX}{task_id}"
        data: Dict[str, Any] = {"progress": progress}
        
        if result is not None:
            data["result"] = result
        
        await redis_client.set(
            key,
            json.dumps(data, ensure_ascii=False),
            ex=settings.PROGRESS_EXPIRE_SECONDS
        )
    
    async def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取当前进度
        
        用于页面刷新后恢复进度状态
        
        Args:
            task_id: 任务唯一标识
            
        Returns:
            进度数据字典，包含 progress 和可选的 result
            如果任务不存在或 Redis 未连接，返回 None
        """
        redis_client = get_redis()
        if not redis_client:
            return None
        
        key = f"{self.KEY_PREFIX}{task_id}"
        data = await redis_client.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    async def subscribe_progress(
        self,
        task_id: str,
        poll_interval: float = 0.3,
        timeout: float = 3600.0,
        heartbeat_interval: float = 15.0
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        订阅进度变化（异步生成器）
        
        使用轮询实现，适合长时任务（<10分钟）
        比 Pub/Sub 简单，避免连接管理复杂度
        
        Args:
            task_id: 任务唯一标识
            poll_interval: 轮询间隔（秒），默认 0.3s
            timeout: 超时时间（秒），默认 600s（10分钟）
            heartbeat_interval: 心跳间隔（秒），默认 15s，防止连接被浏览器/代理断开
            
        Yields:
            进度数据字典，心跳消息包含 {"heartbeat": True, "progress": int}
        """
        last_progress = -1
        elapsed = 0.0
        last_had_result = False
        last_send_time = 0.0  # 上次发送数据的时间
        
        while elapsed < timeout:
            data = await self.get_progress(task_id)
            
            if data:
                current_progress = data.get("progress", 0)
                has_result = "result" in data
                
                # 在进度变化时 yield，或者首次收到 result 时也要 yield
                if current_progress != last_progress or (has_result and not last_had_result):
                    last_progress = current_progress
                    last_had_result = has_result
                    last_send_time = elapsed
                    yield data
                
                # 任务完成（有result），退出循环
                if has_result:
                    break
            
            # 发送心跳消息（防止连接超时）
            if elapsed - last_send_time >= heartbeat_interval:
                last_send_time = elapsed
                yield {"heartbeat": True, "progress": last_progress if last_progress >= 0 else 0}
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        # 超时后再尝试获取一次最终状态
        if elapsed >= timeout:
            final_data = await self.get_progress(task_id)
            if final_data and final_data.get("progress", 0) != last_progress:
                yield final_data
    
    async def delete_progress(self, task_id: str) -> None:
        """
        删除进度数据
        
        Args:
            task_id: 任务唯一标识
        """
        redis_client = get_redis()
        if not redis_client:
            return
        
        key = f"{self.KEY_PREFIX}{task_id}"
        await redis_client.delete(key)


# 全局服务实例
progress_service = ProgressService()

