from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    An abstract base class that defines the interface for agents.
    """

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def invoke(self, state: dict, config: dict) -> dict:
        """
        Process the given state and configuration, and return the new state.
        """
        pass
