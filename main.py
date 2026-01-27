import argparse
from enum import Enum
from abc import ABC
from dataclasses import dataclass
from typing import Union
# TODO
# Questions
# No infinite parsing if the while loops don't terminate (check when we return None from tokenizer and end loop and
# check for that and provide a correct error message
# Symantic Analyzer - right now only capitalize classes?
# Use objgraph for output for parser

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
    IF = 24
    ELSE = 25
    IFONLY = 26
    WHILE = 27
    RETURN = 28
    PRINT = 29
    THIS = 30
    CLASS = 31
    WITH = 32
    LOCALS = 33
    FIELDS = 34
    METHOD = 35
    MAIN = 36
    NUMBER = 37
    IDENTIFIER = 38

OPERATORS = [TokenType.PLUS,TokenType.MINUS,TokenType.ASTER,TokenType.SLASH,TokenType.LABRAC,TokenType.RABRAC,TokenType.DEQUAL,TokenType.NEQUAL]


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
        while(pos < len(self.s) and (c := self.s[pos]) in ["\t"," "]):
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
            if self.s[pos] == "=":
                pos +=1
                tok = Token(TokenType.NEQUAL,"!=")
            else:
                tok = Token(TokenType.EXCLAM, "!")
        if c == "+":
            tok = Token(TokenType.PLUS, "+")
        if c == "-":
            tok = Token(TokenType.MINUS, "-")
        if c == "*":
            tok = Token(TokenType.ASTER, "*")
        if c == "/":
            tok = Token(TokenType.SLASH, "/")
        if c == "<":
            tok = Token(TokenType.LABRAC, "<")
        if c == ">":
            tok = Token(TokenType.RABRAC, ">")
        if c == "=":
            if self.s[pos] == "=":
                pos += 1
                tok = Token(TokenType.DEQUAL,"==")
            else:
                tok = Token(TokenType.EQUAL, "=")
        if c == "_":
            tok = Token(TokenType.UNDER, "_")
        if c == "\n":
            tok = Token(TokenType.NEWLINE,"\n")

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
        if s == "main":
            tok = Token(TokenType.MAIN,s)

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
class Method(ASTNode):
    method_name:str
    args:list[str]
    local_vars:list[str]
    statements:list[Statement]

@dataclass
class Class(ASTNode):
    class_name:str
    fields:list[str]
    methods:list[Method]

@dataclass
class Program(ASTNode):
    classes:list[Class]
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
        self.line_number = 1

    def get_next(self):
        if self.t.peek() is None:
            raise SyntaxError("Expected a token but got end of file")
        tok = self.t.get_next()
        if tok.type == TokenType.NEWLINE:
            self.line_number += 1
        return tok

    def parse(self,*typeset):
        ret = []
        for t in typeset:
            if t is Expression:
                expr = self.parse_expr()
                ret.append(expr)
            elif t is Statement:
                stmt = self.parse_stmt()
                ret.append(stmt)
            elif t is Method:
                mth = self.parse_mthd()
                ret.append(mth)
            elif t is Class:
                cls = self.parse_cls()
                ret.append(cls)
            else:
                tok = self.get_next()
                if type(t) is list:
                    if tok.type not in t:
                        self.parse_error(f"Expected a token of types: {t}, instead got {tok.lexeme} of type {tok.type}")
                else:
                    if tok.type != t:
                        self.parse_error(f"Expected a token of type: {t}, instead got {tok.lexeme} of type {tok.type}")
                ret.append(tok)
        return ret

    def parse_until(self, until, *typeset, grab_trail = True):
        ret = []
        for _ in range(len(typeset)):
            ret.append([])
        stop = (lambda: self.t.peek().type in until) if type(until) is list else (lambda: self.t.peek().type == until)
        while not stop():
            parsed = self.parse(*typeset)
            for i in range(len(typeset)):
                ret[i].append(parsed[i])
            
        if grab_trail:
            self.parse(until)
        return ret

    def parse_error(self,explaination):
        raise SyntaxError(f"Syntax Error on line: {self.line_number}\n{explaination}")

    def parse_expr(self) -> Expression:
        tok = self.t.get_next()
        match tok.type:
            case TokenType.LPAREN:
                left, op, right, _ = self.parse(Expression,OPERATORS,Expression,TokenType.RPAREN)
                return ParenExpression(left,op,right)
            case TokenType.IDENTIFIER:
                return VarExpression(tok)
            case TokenType.NUMBER:
                return NumExpression(tok)
            case TokenType.CARET:
                e, _, method_name, _ = self.parse(Expression,TokenType.DOT,[TokenType.IDENTIFIER,TokenType.THIS],TokenType.LPAREN)
                args = []
                t = self.t.peek()
                if t.type != TokenType.RPAREN:
                    e = self.parse_expr()
                    args.append(e)
                    while((t := self.t.get_next()).type == TokenType.COMMA):
                        args.append(self.parse_expr())
                    if t.type != TokenType.RPAREN:
                        raise SyntaxError("Invalid argument structure to method")
                else:
                    self.t.get_next()

                return MethodExpression(e,method_name,args)
            case TokenType.AMP:
                e, _, field_name = self.parse(Expression,TokenType.DOT,TokenType.IDENTIFIER)
                return FieldReadExpression(e,field_name)
            case TokenType.AT:
                cl = self.parse(TokenType.IDENTIFIER)
                return NewObjExpression(cl)
            case TokenType.THIS:
                return ThisExpression()
        raise SyntaxError(f"{tok.type}: {tok.lexeme} cannot start an expression")
    
    def parse_stmt(self):
        def parse_conditional_block():
            expr, _, _, _, s, _ = self.parse(Expression,TokenType.COLON,TokenType.LCBRAC,TokenType.NEWLINE, Statement, TokenType.NEWLINE)
            ss, _ = self.parse_until(TokenType.RCBRAC,Statement,TokenType.NEWLINE)
            return expr,[s,*ss]

        tok = self.t.get_next()
        match tok.type:
            case TokenType.IDENTIFIER | TokenType.UNDER:
                _, expr = self.parse(TokenType.EQUAL,Expression)
                return AssignVarStatement(tok,expr)
            case TokenType.EXCLAM:
                cls, _, field_name, _, expr = self.parse([TokenType.IDENTIFIER,TokenType.THIS],TokenType.DOT,TokenType.IDENTIFIER,TokenType.EQUAL,Expression)
                return AssignFieldStatement(cls,field_name,expr)
            case TokenType.IF:
                expr, stmts_if = parse_conditional_block()
                _,_,_,s,_ = self.parse(TokenType.ELSE,TokenType.LCBRAC,TokenType.NEWLINE,Statement,TokenType.NEWLINE)
                ss, _ = self.parse_until(TokenType.RCBRAC,Statement,TokenType.NEWLINE)
                return IfStatement(expr,stmts_if,[s,*ss])
            case TokenType.IFONLY:
                return IfOnlyStatement(*parse_conditional_block())
            case TokenType.WHILE:
                return WhileStatement(*parse_conditional_block())
            case TokenType.RETURN:
                expr = self.parse_expr()
                return ReturnStatement(expr)
            case TokenType.PRINT:
                _, expr, _ = self.parse(TokenType.LPAREN,Expression,TokenType.RPAREN)
                return PrintStatement(expr)
        raise Exception(f"how did we get here: {tok}")

    def parse_identifier_list(self):
        identifiers = []
        if self.t.peek().type == TokenType.IDENTIFIER:
            identifiers.append(self.t.get_next())
            while(self.t.peek().type == TokenType.COMMA):
                self.t.get_next()
                name = self.t.get_next()
                if name.type != TokenType.IDENTIFIER:
                    raise SyntaxError("identifier list isn't formatted correctly")
                identifiers.append(name)
        return identifiers


    def parse_cls(self):
        cls, ident, _, _, _ = self.parse(TokenType.CLASS,TokenType.IDENTIFIER,TokenType.LSBRAC,TokenType.NEWLINE,TokenType.FIELDS)
        field_names = self.parse_identifier_list()
        self.parse(TokenType.NEWLINE)
        mths = self.parse_until(TokenType.RSBRAC,Method)
        return Class(ident,field_names,mths)


    def parse_mthd(self):
        print(self.t.peek())
        mth, ident, _ = self.parse(TokenType.METHOD,TokenType.IDENTIFIER,TokenType.LPAREN)
        arg_names = self.parse_identifier_list()
        _, _, _ = self.parse(TokenType.RPAREN,TokenType.WITH,TokenType.LOCALS)
        local_names = self.parse_identifier_list()
        _, _, s, _ = self.parse(TokenType.COLON,TokenType.NEWLINE,Statement,TokenType.NEWLINE)
        ss, _ = self.parse_until([TokenType.METHOD,TokenType.RSBRAC],Statement,TokenType.NEWLINE,grab_trail=False)

        return Method(ident,arg_names,local_names,[s,*ss])

    def parse_program(self):
        cls = []
        if self.t.peek().type != TokenType.MAIN:
            cls, _ = self.parse_until(TokenType.NEWLINE,Class,TokenType.NEWLINE)
        _, _ = self.parse(TokenType.MAIN,TokenType.WITH)
        locs = self.parse_identifier_list()
        _ = self.parse(TokenType.COLON)

        stmts=[]
        while self.t.peek() is not None:
            nl = self.t.get_next()
            if nl.type != TokenType.NEWLINE:
                self.parse_error("No newlines between statements in program entry point (main)")
            if self.t.peek() is None:
                break

            print("a")
            stmt = self.parse_stmt()
            stmts.append(stmt)
        return Program(cls,locs,stmts)


class IRStatement(ABC):
    pass

class IRExpression(ABC):
    pass

class IRControlTransfer:
    pass

class IRVar():
    reg:str

class IRConst():
    n:int

class IRBlockName():
    name:str

class IRArray:
    # Since these are literally supposed to take on values that the same aspects in the blocks will take on they can have the same type, the IRBlockNames will match the block names of blocks etc
    vals:list[Union[IRBlockName,IRConst]]

class IRBasicBlock:
    name:IRBlockName
    statements:list[IRStatement]
    ctl_trans:IRControlTransfer

NONGLOBALS = Union[IRVar,IRConst]
GLOBALS = Union[NONGLOBALS,IRArray]

class IRCall(IRExpression):
    c:IRVar
    r:IRVar
    args:list[NONGLOBALS]

class IRPhi(IRExpression):
    block_names:list[IRBlockName]
    vars:list[IRVar]

class IRAlloc(IRExpression):
    n:IRConst

class IROp(IRExpression):
    l:NONGLOBALS
    op:str
    r:NONGLOBALS

class IRGetELT(IRExpression):
    base:IRVar
    i:NONGLOBALS

class IRLoad(IRExpression):
    base:IRVar

class IRStore(IRStatement):
    base:IRVar
    i:GLOBALS

class IRSetELT(IRStatement):
    base:IRVar
    i:GLOBALS
    i2:GLOBALS

class IRPrint(IRStatement):
    v:NONGLOBALS

class IRAssign(IRStatement):
    v:IRVar
    right:IRExpression

class IRIf(IRControlTransfer):
    v:IRVar
    b_true:IRBlockName
    b_false:IRBlockName

class IRJump(IRControlTransfer):
    b:IRBlockName

class IRRet(IRControlTransfer):
    v:NONGLOBALS

class IRFail(IRControlTransfer):
    m:str  # For the moment who knows

#TODO flatten math
# IRArray
# IRBasicBlock
# map field names to new name as we go through
# Peephole optimization


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

    if args.tokenize or args.parse:
        t = Tokenizer(inp)
        toks = t.tokenize()
        print(toks)

    if args.parse:
        p = Parser(t)
        parse_tree = p.parse_expr()
        print(parse_tree)
        # use objgraph
