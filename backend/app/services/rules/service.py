import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload
from ...shared.models.rules import RuleSet, Rule
from ...shared.models.user import User
from .schemas import RuleSetCreate, RuleSetUpdate, RuleCreate, RuleUpdate
from fastapi import HTTPException, status

class RuleService:
    @staticmethod
    async def get_rule_sets(db: AsyncSession) -> List[RuleSet]:
        result = await db.execute(
            select(RuleSet)
            .options(selectinload(RuleSet.rules))
            .order_by(RuleSet.id)
        )
        return result.scalars().all()

    @staticmethod
    async def get_rule_set(db: AsyncSession, rule_set_id: int) -> RuleSet:
        result = await db.execute(
            select(RuleSet)
            .options(selectinload(RuleSet.rules))
            .where(RuleSet.id == rule_set_id)
        )
        rule_set = result.scalar_one_or_none()
        if not rule_set:
            raise HTTPException(status_code=404, detail="Không tìm thấy bộ quy tắc")
        return rule_set

    @staticmethod
    async def create_rule_set(db: AsyncSession, data: RuleSetCreate, user: User) -> RuleSet:
        # Check code
        result = await db.execute(select(RuleSet).where(RuleSet.code == data.code))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Mã bộ quy tắc đã tồn tại")

        rule_set = RuleSet(**data.model_dump(), created_by=user.id)

        # If is_default, unset others
        if data.is_default:
            await db.execute(update(RuleSet).values(is_default=False))

        db.add(rule_set)
        await db.commit()
        await db.refresh(rule_set)
        return rule_set

    @staticmethod
    async def update_rule_set(db: AsyncSession, rule_set_id: int, data: RuleSetUpdate) -> RuleSet:
        rule_set = await db.get(RuleSet, rule_set_id)
        if not rule_set:
            raise HTTPException(status_code=404, detail="Không tìm thấy bộ quy tắc")

        update_data = data.model_dump(exclude_unset=True)

        if data.is_default:
            await db.execute(update(RuleSet).where(RuleSet.id != rule_set_id).values(is_default=False))

        for key, value in update_data.items():
            setattr(rule_set, key, value)

        rule_set.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(rule_set)
        return rule_set

    @staticmethod
    async def set_default(db: AsyncSession, rule_set_id: int):
        rule_set = await db.get(RuleSet, rule_set_id)
        if not rule_set:
            raise HTTPException(status_code=404, detail="Không tìm thấy bộ quy tắc")

        await db.execute(update(RuleSet).values(is_default=False))
        rule_set.is_default = True
        await db.commit()
        return True

    @staticmethod
    async def clone_rule_set(db: AsyncSession, rule_set_id: int, new_name: str, new_code: str, user: User) -> RuleSet:
        source_set = await RuleService.get_rule_set(db, rule_set_id)

        # Check code
        result = await db.execute(select(RuleSet).where(RuleSet.code == new_code))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Mã bộ quy tắc mới đã tồn tại")

        new_set = RuleSet(
            name=new_name,
            code=new_code,
            description=source_set.description,
            doc_types=source_set.doc_types,
            is_default=False,
            is_active=True,
            version="1.0",
            created_by=user.id
        )
        db.add(new_set)
        await db.flush() # Get new_set.id

        # Clone rules
        for rule in source_set.rules:
            new_rule = Rule(
                rule_set_id=new_set.id,
                rule_code=rule.rule_code,
                category=rule.category,
                name=rule.name,
                description=rule.description,
                check_property=rule.check_property,
                expected_value=rule.expected_value,
                tolerance=rule.tolerance,
                severity=rule.severity,
                error_message=rule.error_message,
                fix_suggestion=rule.fix_suggestion,
                is_active=rule.is_active,
                sort_order=rule.sort_order
            )
            db.add(new_rule)

        await db.commit()
        await db.refresh(new_set)
        return await RuleService.get_rule_set(db, new_set.id)

    # ---------- Rule Methods ----------

    @staticmethod
    async def create_rule(db: AsyncSession, rule_set_id: int, data: RuleCreate) -> Rule:
        rule_set = await db.get(RuleSet, rule_set_id)
        if not rule_set:
            raise HTTPException(status_code=404, detail="Không tìm thấy bộ quy tắc")

        rule = Rule(**data.model_dump(), rule_set_id=rule_set_id)
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    @staticmethod
    async def update_rule(db: AsyncSession, rule_id: uuid.UUID, data: RuleUpdate) -> Rule:
        rule = await db.get(Rule, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Không tìm thấy quy tắc")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(rule, key, value)

        rule.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(rule)
        return rule

    @staticmethod
    async def delete_rule(db: AsyncSession, rule_id: uuid.UUID):
        rule = await db.get(Rule, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Không tìm thấy quy tắc")

        await db.delete(rule)
        await db.commit()
        return True
