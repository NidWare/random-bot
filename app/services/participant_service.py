from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session

from app.repositories.participant_repository import ParticipantRepository


class ParticipantService:
    def __init__(self, session: Session):
        self._repo = ParticipantRepository(session)

    def submit_participation(
        self,
        telegram_user_id: int,
        username: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str],
        language_code: Optional[str],
        is_premium: Optional[bool],
        extra_data: Optional[dict],
    ):
        return self._repo.upsert_participant(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            is_premium=is_premium,
            extra_data=extra_data,
        ) 