from abc import ABC, abstractmethod


class IGameSystem(ABC):
    @abstractmethod
    def update(self):
        pass
