from abc import ABC, abstractmethod
from typing import Any


class IRMCPContext(ABC):

    # Convenience methods for common log levels
    @abstractmethod
    def debug(self, message: str, **extra: Any) -> None:
        """Send a debug log message."""

    @abstractmethod
    def info(self, message: str, **extra: Any) -> None:
        """Send an info log message."""

    @abstractmethod
    def warning(self, message: str, **extra: Any) -> None:
        """Send a warning log message."""

    @abstractmethod
    def error(self, message: str, **extra: Any) -> None:
        """Send an error log message."""

class DebugRMCPContext(IRMCPContext):
    def debug(self, message: str, **extra: Any) -> None:
        print(f"DEBUG: {message}")

    def info(self, message: str, **extra: Any) -> None:
        print(f"INFO: {message}")

    def warning(self, message: str, **extra: Any) -> None:
        print(f"WARNING: {message}")

    def error(self, message: str, **extra: Any) -> None:
        print(f"ERROR: {message}")