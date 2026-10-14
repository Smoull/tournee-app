from typing import Protocol

from app.lead_schema import LeadIn


class DuplicateLeadError(Exception):
    pass


class StorageUnavailableError(Exception):
    pass


class LeadRepository(Protocol):
    def add(self, lead: LeadIn) -> None: ...

    def count(self) -> int: ...


class InMemoryLeadRepository:
    def __init__(self) -> None:
        self._leads: dict[str, LeadIn] = {}

    def add(self, lead: LeadIn) -> None:
        if lead.email in self._leads:
            raise DuplicateLeadError("email déjà inscrit")
        self._leads[lead.email] = lead

    def count(self) -> int:
        return len(self._leads)
