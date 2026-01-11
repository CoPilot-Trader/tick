from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    Abstract Base Class for all Prediction & Analysis Agents.
    Enforces a standard interface for training, inference, and persistence.
    """
    
    def __init__(self):
        pass

    @abstractmethod
    def train(self, data_path: str, **kwargs):
        """
        Train the internal model using data at the given path.
        """
        pass

    @abstractmethod
    def predict(self, input_data):
        """
        Run inference on the provided input data.
        Return format depends on the specific agent.
        """
        pass

    @abstractmethod
    def save(self, path: str):
        """
        Save the agent's state (model weights, configuration) to disk.
        """
        pass

    @abstractmethod
    def load(self, path: str):
        """
        Load the agent's state from disk.
        """
        pass
