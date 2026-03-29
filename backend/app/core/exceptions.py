class PlatformException(Exception):
    """Base exception for the platform"""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)

class DataCollectionError(PlatformException):
    """Raised when data collection fails"""
    def __init__(self, message: str):
        super().__init__(message, code=4001)

class PreprocessingError(PlatformException):
    """Raised when preprocessing fails"""
    def __init__(self, message: str):
        super().__init__(message, code=4002)

class TokenizationError(PlatformException):
    """Raised when tokenization fails"""
    def __init__(self, message: str):
        super().__init__(message, code=4003)

class TrainingError(PlatformException):
    """Raised when training fails"""
    def __init__(self, message: str):
        super().__init__(message, code=4004)

class ModelNotFoundError(PlatformException):
    """Raised when model is not found"""
    def __init__(self, message: str):
        super().__init__(message, code=4005)