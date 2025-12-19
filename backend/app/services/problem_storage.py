"""
题目存储服务
实现PostgreSQL（元数据）+ MongoDB（内容）的混合存储架构
"""

from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models import Problem


# ==================== MongoDB连接管理 ====================

_mongodb_client: Optional[AsyncIOMotorClient] = None
_mongodb_db: Optional[AsyncIOMotorDatabase] = None


def init_mongodb(mongodb_url: str) -> None:
    """
    初始化MongoDB连接
    
    Args:
        mongodb_url: MongoDB连接URL，例如: mongodb://admin:password@localhost:27017/?authSource=admin
    """
    global _mongodb_client, _mongodb_db
    
    if not mongodb_url:
        raise ValueError("MongoDB URL不能为空")
    
    _mongodb_client = AsyncIOMotorClient(mongodb_url)
    # 从URL中提取数据库名，如果没有指定则使用默认的
    # 如果URL中没有指定数据库，使用默认的数据库名
    db_name = "mathtasks"  # 默认数据库名
    _mongodb_db = _mongodb_client[db_name]
    
    print(f"✅ MongoDB连接已初始化: {mongodb_url}")


async def close_mongodb() -> None:
    """关闭MongoDB连接"""
    global _mongodb_client, _mongodb_db
    
    if _mongodb_client:
        _mongodb_client.close()
        _mongodb_client = None
        _mongodb_db = None
        print("✅ MongoDB连接已关闭")


def get_mongodb_collection() -> AsyncIOMotorCollection:
    """
    获取MongoDB集合（collection）
    
    Returns:
        problems集合
        
    Raises:
        RuntimeError: 如果MongoDB未初始化
    """
    if _mongodb_db is None:
        raise RuntimeError("MongoDB未初始化，请先配置MONGODB_URL")
    
    return _mongodb_db["problems"]


# ==================== 存储服务类 ====================

class ProblemStorageService:
    """
    题目存储服务
    负责在PostgreSQL和MongoDB之间协调数据存储
    """
    
    def __init__(self):
        self.collection = get_mongodb_collection()
    
    async def create_problem(
        self,
        db: AsyncSession,
        problem_metadata: Dict[str, Any],
        problem_content: Dict[str, Any]
    ) -> tuple[int, str]:
        """
        创建题目（同时写入PostgreSQL和MongoDB）
        
        Args:
            db: PostgreSQL数据库会话
            problem_metadata: 题目元数据（存储在PostgreSQL）
            problem_content: 题目内容（存储在MongoDB）
            
        Returns:
            (problem_id, mongo_id) 元组
            
        Raises:
            RuntimeError: 如果MongoDB未配置
        """
        # 1. 先创建PostgreSQL记录（获取problem_id）
        new_problem = Problem(
            creator_id=problem_metadata["creator_id"],
            parent_problem_id=problem_metadata.get("parent_problem_id"),
            title=problem_metadata["title"],
            category=problem_metadata["category"],
            source_type=problem_metadata["source_type"],
            ocr_image_url=problem_metadata.get("ocr_image_url"),
            status=problem_metadata["status"],
            validation_status=problem_metadata["validation_status"],
            human_review_status=problem_metadata["human_review_status"],
            variant_count=problem_metadata.get("variant_count", 0),
            # 这些字段已迁移到MongoDB，但保留为可空以兼容
            content=None,
            explanation=None,
            answer=None,
            validation_result=None,
            quality_check_details=None
        )
        
        db.add(new_problem)
        await db.commit()
        await db.refresh(new_problem)
        
        problem_id = new_problem.id
        
        # 2. 创建MongoDB文档
        mongo_doc = {
            "problem_id": problem_id,  # 关联PostgreSQL的ID
            "content": problem_content.get("content"),  # 题目内容（JSON格式）
            "explanation": problem_content.get("explanation"),  # 解析
            "answer": problem_content.get("answer"),  # 答案
            "validation_result": problem_content.get("validation_result"),  # 验证结果
            "quality_check_details": problem_content.get("quality_check_details"),  # 质检详情
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.collection.insert_one(mongo_doc)
        mongo_id = str(result.inserted_id)
        
        # 3. 更新PostgreSQL记录，保存mongo_id
        new_problem.mongo_id = mongo_id
        await db.commit()
        
        return problem_id, mongo_id
    
    async def get_problem(
        self,
        db: AsyncSession,
        problem_id: int
    ) -> Dict[str, Any]:
        """
        获取完整题目数据（合并PostgreSQL和MongoDB）
        
        Args:
            db: PostgreSQL数据库会话
            problem_id: 题目ID
            
        Returns:
            完整的题目数据字典
            
        Raises:
            RuntimeError: 如果MongoDB未配置
        """
        # 1. 从PostgreSQL获取元数据
        result = await db.execute(
            select(Problem).where(Problem.id == problem_id)
        )
        problem = result.scalar_one_or_none()
        
        if not problem:
            raise ValueError(f"题目不存在: {problem_id}")
        
        # 2. 从MongoDB获取内容
        mongo_doc = None
        if problem.mongo_id:
            mongo_doc = await self.collection.find_one({"_id": ObjectId(problem.mongo_id)})
        
        # 3. 合并数据
        problem_dict = {
            "id": problem.id,
            "creator_id": problem.creator_id,
            "parent_problem_id": problem.parent_problem_id,
            "title": problem.title,
            "category": problem.category.value if problem.category else None,
            "source_type": problem.source_type.value if problem.source_type else None,
            "ocr_image_url": problem.ocr_image_url,
            "status": problem.status.value if problem.status else None,
            "validation_status": problem.validation_status.value if problem.validation_status else None,
            "human_review_status": problem.human_review_status.value if problem.human_review_status else None,
            "variant_count": problem.variant_count,
            "difficulty": problem.difficulty,
            "validation_correct_count": problem.validation_correct_count,
            "validation_completed_at": problem.validation_completed_at.isoformat() if problem.validation_completed_at else None,
            "quality_check": problem.quality_check,
            "review_count": problem.review_count,
            "avg_innovation_score": problem.avg_innovation_score,
            "avg_rigor_score": problem.avg_rigor_score,
            "created_at": problem.created_at.isoformat() if problem.created_at else None,
            "updated_at": problem.updated_at.isoformat() if problem.updated_at else None,
            "published_at": problem.published_at.isoformat() if problem.published_at else None,
            "human_review_note": problem.human_review_note,
            # 从MongoDB获取的内容
            "content": mongo_doc.get("content") if mongo_doc else None,
            "explanation": mongo_doc.get("explanation") if mongo_doc else None,
            "answer": mongo_doc.get("answer") if mongo_doc else None,
            "validation_result": mongo_doc.get("validation_result") if mongo_doc else None,
            "quality_check_details": mongo_doc.get("quality_check_details") if mongo_doc else None,
        }
        
        return problem_dict
    
    async def update_problem_content(
        self,
        db: AsyncSession,
        problem_id: int,
        updates: Dict[str, Any]
    ) -> None:
        """
        更新MongoDB中的题目内容
        
        Args:
            db: PostgreSQL数据库会话
            problem_id: 题目ID
            updates: 要更新的字段字典
            
        Raises:
            RuntimeError: 如果MongoDB未配置
            ValueError: 如果题目不存在或没有mongo_id
        """
        # 1. 检查题目是否存在
        result = await db.execute(
            select(Problem).where(Problem.id == problem_id)
        )
        problem = result.scalar_one_or_none()
        
        if not problem:
            raise ValueError(f"题目不存在: {problem_id}")
        
        if not problem.mongo_id:
            raise ValueError(f"题目没有MongoDB记录: {problem_id}")
        
        # 2. 更新MongoDB文档
        update_doc = {
            "$set": {
                **updates,
                "updated_at": datetime.utcnow()
            }
        }
        
        await self.collection.update_one(
            {"_id": ObjectId(problem.mongo_id)},
            update_doc
        )


# ==================== 服务实例获取 ====================

_storage_service: Optional[ProblemStorageService] = None


def get_problem_storage_service() -> ProblemStorageService:
    """
    获取题目存储服务实例
    
    Returns:
        ProblemStorageService实例
        
    Raises:
        RuntimeError: 如果MongoDB未配置
    """
    global _storage_service
    
    if not settings.MONGODB_URL:
        raise RuntimeError("MongoDB未配置，请设置MONGODB_URL环境变量")
    
    if _storage_service is None:
        _storage_service = ProblemStorageService()
    
    return _storage_service

