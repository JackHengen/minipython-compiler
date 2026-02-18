from enum import Enum

class TokenType(Enum):
    LPAREN = 0
    RPAREN = 1
    LSBRAC = 2
    RSBRAC = 3
    LCBRAC = 4
    RCBRAC = 5
    LABRAC = 6
    RABRAC = 7
    CARET = 8
    DOT = 9
    COMMA = 10
    COLON = 11
    AMP = 12
    AT = 13
    EXCLAM = 14
    PLUS = 15
    MINUS = 16
    ASTER = 17
    SLASH = 18
    EQUAL = 19
    DEQUAL = 20
    NEQUAL = 21
    UNDER = 22
    NEWLINE = 23
    NEWLINES = 24
    IF = 25
    ELSE = 26
    IFONLY = 27
    WHILE = 28
    RETURN = 29
    PRINT = 30
    THIS = 31
    CLASS = 32
    WITH = 33
    LOCALS = 34
    FIELDS = 35
    METHOD = 36
    MAIN = 37
    NUMBER = 38
    IDENTIFIER = 39

OPERATORS = [TokenType.PLUS,TokenType.MINUS,TokenType.ASTER,TokenType.SLASH,TokenType.LABRAC,TokenType.RABRAC,TokenType.DEQUAL,TokenType.NEQUAL]


class Token():
    def __init__(self,typ:TokenType,lexeme:str):
        self.type = typ
        self.lexeme = lexeme
    def __repr__(self):
        return str((self.type,self.lexeme))
