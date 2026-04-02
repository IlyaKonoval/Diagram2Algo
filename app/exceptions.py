class CVUMLException(Exception):
    def __init__(self, message: str, detail: str = ""):
        self.message = message
        self.detail = detail
        super().__init__(message)


class LLMProviderError(CVUMLException):
    pass


class ExtractionError(CVUMLException):
    pass


class ParsingError(CVUMLException):
    pass


class FileProcessingError(CVUMLException):
    pass


class UnsupportedFileError(FileProcessingError):
    pass
