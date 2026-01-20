import argparse
from enum import Enum
from abc import ABC
import time
from dataclasses import dataclass
# TODO
# Questions
# Do we need to end all methods with return?
# Implement 
# Figure out newlines
# No infinite parsing if the while loops don't terminate (check when we return None from tokenizer and end loop and
# check for that and provide a correct error message
# Symantic Analyzer
# Use objgraph for output for parser

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
    UNDER = 18
    IF = 19
    ELSE = 20
    IFONLY = 21
    WHILE = 22
    RETURN = 23
    PRINT = 24
    THIS = 25
    CLASS = 26
    WITH = 27
    LOCALS = 28
    FIELDS = 29
    METHOD = 30
    NUMBER = 31
    IDENTIFIER = 32

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
        if c == "_":
            tok = Token(TokenType.UNDER, "_")

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
        if s == "else":
            tok = Token(TokenType.ELSE,s)
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
    expr:Expression
    field_name:str

@dataclass
class NewObjExpression(Expression):
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
    field_name:str
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
                e = self.parse_expr()
                dot = self.t.get_next()
                if dot.type != TokenType.DOT:
                    raise SyntaxError("No dot used when accessing field")
                field_name = self.t.get_next()
                if field_name.type != TokenType.IDENTIFIER:
                    raise SyntaxError("Field name is not an identifier")
                return FieldReadExpression(e,field_name)
            case TokenType.AT:
                cl = self.t.get_next()
                if cl.type != TokenType.IDENTIFIER:
                    raise SyntaxError("Class instantiation doesn't refer to a valid identifier")
                return NewObjExpression(cl)
            case TokenType.THIS:
                return ThisExpression()
        raise SyntaxError(f"{tok.lexeme} cannot start an expression")

    def parse_stmt(self):
        def parse_conditional_block(block_type:str):
            expr = self.parse_expr()
            colon = self.t.get_next()
            if colon.type != TokenType.COLON:
                raise SyntaxError(f"No colon seperator between conditional and statements to execute in {block_type} statement")
            lbrac = self.t.get_next()
            if lbrac.type != TokenType.LCBRAC:
                raise SyntaxError("No curly bracket to open statments after conditional in {block_type} statement")
            stmts = [self.parse_stmt()] # each block needs at least one statement in it
            while self.t.peek().type != TokenType.RCBRAC:
                stmts.append(self.parse_stmt())
            rbrac = self.t.get_next()
            return expr,stmts

        tok = self.t.get_next()
        match tok.type:
            case TokenType.IDENTIFIER | TokenType.UNDER:
                eq = self.t.get_next()
                if eq.type != TokenType.EQUAL:
                    raise SyntaxError("Variable assignment missing equal sign")
                expr = self.parse_expr()
                return AssignVarStatement(tok,expr)
            case TokenType.EXCLAM:
                cls = self.t.get_next()
                if cls.type != TokenType.IDENTIFIER:
                    raise SyntaxError("Field assignment doesn't refer to valid object identifier")
                dot = self.t.get_next()
                if dot.type != TokenType.DOT:
                    raise SyntaxError("No dot used when referring to field to assign value to")
                field_name = self.t.get_next()
                if field_name.type != TokenType.IDENTIFIER:
                    raise SyntaxError("Field assignment doesn't refer to valid field name identifier")
                eq = self.t.get_next()
                if eq.type != TokenType.EQUAL:
                    raise SyntaxError("Field assignment missing equal sign")
                expr = self.parse_expr()
                return AssignFieldStatement(cls,field_name,expr)
            case TokenType.IF:
                expr, stmts_if = parse_conditional_block("if")
                kw_else = self.t.get_next()
                if kw_else.type != TokenType.ELSE:
                    raise SyntaxError("No else clause in if statement (must use ifonly if this was intended)")
                lbrac = self.t.get_next()
                if lbrac.type != TokenType.LCBRAC:
                    raise SyntaxError("No curly bracket to open statments after else in if statement")
                stmts_else = []
                while self.t.peek().type != TokenType.RCBRAC:
                    stmts_else.append(self.parse_stmt())
                rbrac = self.t.get_next()
                return IfStatement(expr,stmts_if,stmts_else)
                    
            case TokenType.IFONLY:
                return IfOnlyStatement(*parse_conditional_block("ifonly"))
            case TokenType.WHILE:
                return WhileStatement(*parse_conditional_block("while"))
            case TokenType.RETURN:
                expr = self.parse_expr()
                return ReturnStatement(expr)
            case TokenType.PRINT:
                expr = self.parse_expr()
                return PrintStatement(expr)
            

    def parse_cls(self):
        pass

    def parse_mthd(self):
        pass

    def parse_program(self):
        pass

class Analyzer():
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

    # stages = ["tokenize","parse","ast","cfg","opt"]
    if args.tokenize or args.parse:
        t = Tokenizer(inp)
        toks = t.tokenize()
        print(toks)

    if args.parse:
        p = Parser(t)
        parse_tree = p.parse_expr()
        print(parse_tree)
        # use objgraph
