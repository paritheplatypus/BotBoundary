from abc import ABC, abstractmethod
from typing import List

class Basemodel(ABC):
    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def predict(self, feature_vector: List[float]) -> dict:
        pass