"""Slicer backend abstraction: how a slicing job is actually executed."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable, Awaitable

from src.models.slicer import SlicerProfile

ProgressCb = Optional[Callable[[int], Awaitable[None]]]


@dataclass
class SliceResult:
    success: bool
    output_path: Optional[str]
    estimated_print_time: Optional[int]
    filament_used: Optional[float]
    error_message: Optional[str] = None


class SlicerBackend(ABC):
    @abstractmethod
    async def slice(self, input_path: str, profile: SlicerProfile,
                    output_path: str, progress_cb: ProgressCb = None) -> SliceResult:
        ...

    @abstractmethod
    async def verify(self) -> bool:
        ...

    @abstractmethod
    async def version(self) -> Optional[str]:
        ...
