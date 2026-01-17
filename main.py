import argparse
from enum import Enum
from abc import ABC
import time
from dataclasses import dataclass
# objgraph

class TokenType(Enum):
    LPAREN = 0
    RPAREN = 1
    LSBRAC = 2
    RSBRAC = 3
    LCBRAC = 4
    RCBRAC = 5
    CARET = 6
    DOT = 7
    COMMA = 8
    COLON = 9
    AMP = 10
    AT = 11
    EXCLAM = 12
    PLUS = 13
    MINUS = 14
    ASTER = 15
    SLASH = 16
    EQUAL = 17
    IF = 18
    IFONLY = 19
    WHILE = 20
    RETURN = 21
    PRINT = 22
    THIS = 23
    CLASS = 24
    WITH = 25
    LOCALS = 26
    FIELDS = 27
    METHOD = 28
    NUMBER = 29
    IDENTIFIER = 30

OPERATORS = [TokenType.PLUS,TokenType.MINUS,TokenType.ASTER,TokenType.SLASH]


class Token():
    def __init__(self,typ:TokenType,lexeme:str):
        self.type = typ
        self.lexeme = lexeme
    def __repr__(self):
        return str((self.type,self.lexeme))


class Tokenizer:
    def __init__(self,s:str):
        self.s = s
        self.pos = 0
        self.toks = []

    def peek(self) -> Token:
        tok = self.get_next()
        self.pos -= 1
        return tok

    def get_next(self) -> Token:
        if len(self.toks) > self.pos:
            tok = self.toks[self.pos]
            self.pos += 1
            return tok

        pos = 0  # string pos not the token cache pos
        while(pos < len(self.s) and (c := self.s[pos]).isspace()):
            pos += 1

        if pos >= len(self.s):
            return None
        pos += 1

        tok = None
        if c == "(":
            tok = Token(TokenType.LPAREN, "(")
        if c == ")":
            tok = Token(TokenType.RPAREN, ")")
        if c == "[":
            tok = Token(TokenType.LSBRAC, "[")
        if c == "]":
            tok = Token(TokenType.RSBRAC, "]")
        if c == "{":
            tok = Token(TokenType.LCBRAC, "{")
        if c == "}":
            tok = Token(TokenType.RCBRAC, "}")
        if c == "^":
            tok = Token(TokenType.CARET, "^")
        if c == ".":
            tok = Token(TokenType.DOT, ".")
        if c == ",":
            tok = Token(TokenType.COMMA, ",")
        if c == ":":
            tok = Token(TokenType.COLON, ":")
        if c == "&":
            tok = Token(TokenType.AMP, "&")
        if c == "@":
            tok = Token(TokenType.AT, "@")
        if c == "!":
            tok = Token(TokenType.EXCLAM, "!")
        if c == "+":
            tok = Token(TokenType.PLUS, "+")
        if c == "-":
            tok = Token(TokenType.MINUS, "-")
        if c == "*":
            tok = Token(TokenType.ASTER, "*")
        if c == "/":
            tok = Token(TokenType.SLASH, "/")
        if c == "=":
            tok = Token(TokenType.EQUAL, "=")

        s = str(c)
        if c.isdigit():
            while pos < len(self.s) and (c:= self.s[pos]).isdigit():
                s += str(c)
                pos += 1
            tok = Token(TokenType.NUMBER,s)

        if c.isalpha():
            while pos < len(self.s) and (c := self.s[pos]).isalpha():
                s += c
                pos += 1
            tok = Token(TokenType.IDENTIFIER,s)
        if s == "if":
            tok = Token(TokenType.IF,s)
        if s == "ifonly":
            tok = Token(TokenType.IFONLY,s)
        if s == "while":
            tok = Token(TokenType.WHILE,s)
        if s == "return":
            tok = Token(TokenType.RETURN,s)
        if s == "print":
            tok = Token(TokenType.PRINT,s)
        if s == "this":
            tok = Token(TokenType.THIS,s)
        if s == "class":
            tok = Token(TokenType.CLASS,s)
        if s == "with":
            tok = Token(TokenType.WITH,s)
        if s == "locals":
            tok = Token(TokenType.LOCALS,s)
        if s == "fields":
            tok = Token(TokenType.FIELDS,s)
        if s == "method":
            tok = Token(TokenType.METHOD,s)


        self.s = self.s[pos:]
        if tok is None:
            raise ValueError(f"Inappropriate symbol {c}")
        else:
            self.pos +=1
            self.toks.append(tok)
            return tok


    def tokenize(self):
        while(self.get_next()):
            pass
        self.pos = 0
        return self.toks

class ASTNode(ABC):
    pass


class Statement(ASTNode):
    pass

class Expression(ASTNode):
    pass

@dataclass
class MethodDeclaration(ASTNode):
    method_name:str
    local_vars:list[str]
    statements:list[Statement]

@dataclass
class ClassDeclaration(ASTNode):
    class_name:str
    fields:list[str]
    methods:list[MethodDeclaration]

@dataclass
class Program(ASTNode):
    classes:list[ClassDeclaration]
    local_vars:list[str]
    statements:list[Statement]

@dataclass
class NumExpression(Expression):
    num:int

@dataclass
class VarExpression(Expression):
    var_name:str

@dataclass
class ParenExpression(Expression):
    left:Expression
    op:str
    right:Expression

@dataclass
class MethodExpression(Expression):
    expr:Expression
    method_name:str
    args:list[str]

@dataclass
class FieldReadExpression(Expression):
    class_name:str
    field_name:str

@dataclass
class NewClassExpression(Expression):
    class_name:str

@dataclass
class ThisExpression(Expression):
    pass

@dataclass
class AssignVarStatement(Statement):
    var_name:str
    val:Expression

@dataclass
class AssignFieldStatement(Statement):
    class_name:str
    var_name:str
    val:Expression

@dataclass
class IfStatement(Statement):
    condition:Expression
    statements_true:list[Statement]
    statements_false:list[Statement]

@dataclass
class IfOnlyStatement(Statement):
    condition:Expression
    statements:list[Statement]

@dataclass
class WhileStatement(Statement):
    condition:Expression
    statements:list[Statement]

@dataclass
class ReturnStatement(Statement):
    val:Expression

@dataclass
class PrintStatement(Statement):
    val:Expression


class Parser:
    def __init__(self,t:Tokenizer):
        self.t = t

    def parse_expr(self) -> Expression:
        tok = self.t.get_next()
        match tok.type:
            case TokenType.LPAREN:
                left = self.parse_expr()
                op = self.t.get_next()
                if op.type not in OPERATORS:
                    raise SyntaxError("Invalid operator on parenthesized expression")
                right = self.parse_expr()
                rparen = self.t.get_next()
                if rparen.type != TokenType.RPAREN:
                    raise SyntaxError("No closing parenthesis on parenthesized expression")
                return ParenExpression(left,op,right)
            case TokenType.IDENTIFIER:
                return VarExpression(tok.lexeme)
            case TokenType.NUMBER:
                return NumExpression(tok.lexeme)
            case TokenType.CARET:
                e = self.parse_expr()
                dot = self.t.get_next()
                if dot.type != TokenType.DOT:
                    raise SyntaxError("No dot used when accessing method")
                method_name = self.t.get_next()
                if method_name.type != TokenType.IDENTIFIER:
                    raise SyntaxError("Method name is not an identifier")
                lparen = self.t.get_next()
                if lparen.type != TokenType.LPAREN:
                    raise SyntaxError("Invalid argument structure to method")
                args = []
                t = self.t.peek()
                if t.type != TokenType.RPAREN:
                    e = self.parse_expr()
                    args.append(e)
                    while((t := self.t.get_next()).type == TokenType.COMMA):
                        e = self.parse_expr()
                        args.append(e)
                    if t.type != TokenType.RPAREN:
                        raise SyntaxError("Invalid argument structure to method")
                else:
                    self.t.get_next()

                return MethodExpression(e,method_name.lexeme,args)
            case TokenType.AMP:
                pass
            case TokenType.AT:
                pass
            case TokenType.THIS:
                #TODO figure out a representation for this
                pass

    def parse_statement(self):
        pass

    def parse_class(self):
        pass

    def parse_method(self):
        #TODO idk about this one
        pass

    def parse_program(self):
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="MiniPython Compiler")
    input_group = parser.add_mutually_exclusive_group(required=True)

    input_group.add_argument("-f","--file")
    input_group.add_argument("-s","--str","--string")

    stage_group = parser.add_mutually_exclusive_group()
    stage_group.add_argument("-t","--tokenize",action='store_true')
    stage_group.add_argument("-p","--parse",action='store_true')
    stage_group.add_argument("-a","--ast",action='store_true')
    stage_group.add_argument("-c","--cfg","--noopt",action='store_true')
    stage_group.add_argument("-o","--opt","--optimize","--optimization",action='store_true')
    args = parser.parse_args()

    if args.file:
        with open(args.file) as f:
            inp = f.read()
    elif args.str:
        inp = args.str

    stages = ["tokenize","parse","ast","cfg","opt"]
    stage = float("inf")  # by default we go to last stage
    for i,val in enumerate(stages):
        if val in args:
            stage=i
            break

    if stage >= 0:
        t = Tokenizer(inp)
        if args.tokenize:
            toks = t.tokenize()
            print(toks)

    if stage >= 1:
        p = Parser(t)
        parse_tree = p.parse_program()
        if args.parse:
            # use objgraph
            pass
