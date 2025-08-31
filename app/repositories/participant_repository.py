from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import Participant


class ParticipantRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_telegram_user_id(self, telegram_user_id: int) -> Optional[Participant]:
        stmt = select(Participant).where(Participant.telegram_user_id == telegram_user_id)
        return self._session.execute(stmt).scalar_one_or_none()

    def upsert_participant(
        self,
        telegram_user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None,
        is_premium: Optional[bool] = None,
        extra_data: Optional[dict] = None,
    ) -> Participant:
        participant = self.get_by_telegram_user_id(telegram_user_id)
        if participant is None:
            participant = Participant(
                telegram_user_id=telegram_user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
                is_premium=is_premium,
                extra_data=extra_data or {},
            )
            self._session.add(participant)
        else:
            participant.username = username
            participant.first_name = first_name
            participant.last_name = last_name
            participant.language_code = language_code
            participant.is_premium = is_premium
            participant.extra_data = extra_data or participant.extra_data
        self._session.commit()
        self._session.refresh(participant)
        return participant 