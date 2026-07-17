class CompilerException(Exception):
    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "message": str(self)
        }

class LexerError(CompilerException):
    def __init__(self, message, position):
        super().__init__(message)
        self.message = message
        self.position = position
        
    def to_dict(self):
        return {
            "type": "LexerError",
            "message": self.message,
            "position": self.position
        }

class ParserError(CompilerException):
    def __init__(self, message, position, suggestion):
        super().__init__(message)
        self.message = message
        self.position = position
        self.suggestion = suggestion
        
    def to_dict(self):
        return {
            "type": "ParserError",
            "message": self.message,
            "position": self.position,
            "suggestion": self.suggestion
        }

class SemanticError(CompilerException):
    def __init__(self, message, suggestion):
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion
        
    def to_dict(self):
        return {
            "type": "SemanticError",
            "message": self.message,
            "suggestion": self.suggestion
        }

class CompilerError(CompilerException):
    def __init__(self, phase, message, position=None, suggestion=None):
        super().__init__(f"[{phase}] {message}")
        self.phase = phase
        self.message = message
        self.position = position
        self.suggestion = suggestion
        
    def to_dict(self):
        return {
            "type": "CompilerError",
            "phase": self.phase,
            "message": self.message,
            "position": self.position,
            "suggestion": self.suggestion
        }
