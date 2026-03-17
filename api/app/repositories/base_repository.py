"""Base repository class for common CRUD operations"""

from typing import Generic, TypeVar, Optional, List, Any, Dict, Type
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Generic repository for CRUD operations with synchronous SQLAlchemy"""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get(self, id: Any) -> Optional[ModelType]:
        """Get single record by ID"""
        stmt = select(self.model).where(self.model.id == id)  # type: ignore[attr-defined]
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """Get multiple records with pagination and filtering"""
        stmt = select(self.model)
        
        # Apply filters
        if filters:
            conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    attr = getattr(self.model, key)
                    if isinstance(value, list):
                        conditions.append(attr.in_(value))
                    elif isinstance(value, str) and "%" in value:
                        conditions.append(attr.like(value))
                    else:
                        conditions.append(attr == value)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
        
        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_attr = getattr(self.model, order_by)
            stmt = stmt.order_by(order_attr.desc() if order_desc else order_attr)
        
        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        result = self.db.execute(stmt)
        return list(result.scalars().all())
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering"""
        stmt = select(func.count(self.model.id))  # type: ignore[attr-defined]
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    attr = getattr(self.model, key)
                    if isinstance(value, list):
                        conditions.append(attr.in_(value))
                    elif isinstance(value, str) and "%" in value:
                        conditions.append(attr.like(value))
                    else:
                        conditions.append(attr == value)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = self.db.execute(stmt)
        count = result.scalar()
        return count if count is not None else 0
    
    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create new record"""
        if hasattr(obj_in, 'model_dump'):
            obj_data = obj_in.model_dump()
        else:
            obj_data = obj_in.dict()
        
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.flush()  # Flush to get the ID
        self.db.refresh(db_obj)
        return db_obj
    
    def create_batch(self, objects_in: List[CreateSchemaType]) -> List[ModelType]:
        """Create multiple records in batch"""
        db_objects = []
        
        for obj_in in objects_in:
            if hasattr(obj_in, 'model_dump'):
                obj_data = obj_in.model_dump()
            else:
                obj_data = obj_in.dict()
            
            db_obj = self.model(**obj_data)
            db_objects.append(db_obj)
        
        self.db.add_all(db_objects)
        self.db.flush()
        
        for db_obj in db_objects:
            self.db.refresh(db_obj)
        
        return db_objects
    
    def update(self, id: Any, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """Update existing record"""
        # Get existing record
        db_obj = self.get(id)
        if not db_obj:
            return None
        
        # Update fields
        if hasattr(obj_in, 'model_dump'):
            obj_data = obj_in.model_dump(exclude_unset=True)
        else:
            obj_data = obj_in.dict(exclude_unset=True)
        
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: Any) -> bool:
        """Delete record by ID"""
        db_obj = self.get(id)
        if not db_obj:
            return False
        
        self.db.delete(db_obj)
        self.db.flush()
        return True
    
    def exists(self, filters: Dict[str, Any]) -> bool:
        """Check if record exists with given filters"""
        stmt = select(self.model.id)  # type: ignore[attr-defined]
        
        conditions = []
        for key, value in filters.items():
            if hasattr(self.model, key):
                attr = getattr(self.model, key)
                conditions.append(attr == value)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.limit(1)
        result = self.db.execute(stmt)
        return result.scalar() is not None