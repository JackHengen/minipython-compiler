import argparse
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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

class IRStatement(ABC):
    pass

class IRExpression(ABC):
    pass

class IRControlTransfer(ABC):
    pass

@dataclass
class IRVar(IRExpression):
    reg:str


@dataclass
class IRConst(IRExpression):
    n:int

@dataclass
class IRArray:
    # Since these are literally supposed to take on values that the same aspects in the blocks will take on they can have the same type, the IRBlockNames will match the block names of blocks etc
    vals:list[Union[str,IRConst]]
    name:str

@dataclass
class IRBasicBlock:
    name:str
    statements:list[IRStatement]
    ctl_trans:IRControlTransfer

    def add_statement(self,stmt:IRStatement):
        self.statements.append(stmt)

    def add_ctl_trans(self,trans:IRControlTransfer):
        self.ctl_trans=trans

NONGLOBALS = Union[IRVar,IRConst]
GLOBALS = Union[NONGLOBALS,IRArray]

@dataclass
class IROperation(IRExpression):
    l:NONGLOBALS
    op:str
    r:NONGLOBALS

@dataclass
class IRCall(IRExpression):
    c:IRVar
    r:IRVar
    args:list[NONGLOBALS]

@dataclass
class IRPhi(IRExpression):
    block_names:list[str]
    vars:list[IRVar]

@dataclass
class IRAlloc(IRExpression):
    n:IRConst

@dataclass
class IROp(IRExpression):
    l:NONGLOBALS
    op:str
    r:NONGLOBALS

@dataclass
class IRGetELT(IRExpression):
    base:IRVar
    i:NONGLOBALS

@dataclass
class IRLoad(IRExpression):
    base:IRVar

@dataclass
class IRStore(IRStatement):
    base:IRVar
    i:GLOBALS

@dataclass
class IRSetELT(IRStatement):
    base:IRVar
    i:GLOBALS
    i2:GLOBALS

@dataclass
class IRPrint(IRStatement):
    v:NONGLOBALS

@dataclass
class IRAssign(IRStatement):
    v:IRVar
    val:IRExpression

@dataclass
class IRIf(IRControlTransfer):
    v:IRVar
    b_true:str
    b_false:str

@dataclass
class IRJump(IRControlTransfer):
    b:str

@dataclass
class IRRet(IRControlTransfer):
    v:NONGLOBALS

@dataclass
class IRFail(IRControlTransfer):
    m:str  # For the moment who knows

@dataclass
class IRProgram:
    vtbls: list[IRArray]
    field_maps: list[IRArray]
    field_name_to_map_index: dict[str, int]
    blocks: list[IRBasicBlock] = field(default_factory=list)
    curr_block:IRBasicBlock = None

    def add_block(self,block_name):
        self.curr_block = IRBasicBlock(block_name,[],[])
        self.blocks.append(self.curr_block)
        return self.curr_block

    def get_block(self,block_name):
        return self.curr_block

    def add_stmt(self,stmt:IRStatement):
        self.curr_block.add_statement(stmt)

class ASTNode(ABC):
    # to_ir()
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

    def to_ir(prog:IRProgram):
        for s in statements:
            s.to_ir(IRProgram)


@dataclass
class Class(ASTNode):
    class_name:str
    fields:list[str]
    methods:list[Method]

    def to_ir(self,prog:IRProgram):
        for m in self.methods:
            prog.add_block(self.class_name,m.method_name)
            m.to_ir()



@dataclass
class Program(ASTNode):
    classes:list[Class]
    local_vars:list[str]
    statements:list[Statement]
    
    def to_ir_program(self):
        field_map = {}
        counter = 0
        for c in self.classes:
            for field in c.fields:
                if field not in field_map:
                    field_map[field] = counter
                    counter += 1

        vtbls = []
        class_field_maps = []
        for c in self.classes:

            counter = 2 # first field offset
            class_map = []
            for i in range(len(field_map)):
                class_map.append(0)

            for field in c.fields:
                class_map[field_map[field]] = counter
                counter += 1
            class_field_maps.append(IRArray(class_map))

            vtbl = []
            for m in c.methods:
                vtbl.append(c.class_name + mthd.method_name)
            vtbls.append(IRArray(vtbl))

        prog = IRProgram(vtbls,class_field_maps,field_map)
        return self.to_ir(prog)

    def to_ir(prog:IRProgram):
        for c in self.classes:
            c.to_ir(prog)

        
        prog.add_block("main")
        for stmt in stmts:
            stmt.to_ir(prog)

        return prog

@dataclass
class NumExpression(Expression):
    num:int
    def __post_init__(self):
        self.num = int(self.num)
    def to_ir(self,counter):
        return [],IRConst(self.num),counter


@dataclass
class VarExpression(Expression):
    var_name:str
    def to_ir(self,counter):
        return [],IRVar(self.var_name),counter
    

def is_flat(Expression):
    return isinstance(Expression, (NumExpression,VarExpression))

@dataclass
class ParenExpression(Expression):
    left:Expression
    op:str
    right:Expression
    def to_ir(self,counter):
        print("nested")
        stmts=[]
        if not is_flat(self.left):
            s,expr,counter = self.left.to_ir(counter)
            stmts.extend(s)
            tmp = f"tmp{counter}"
            counter+=1
            s = IRAssign(IRVar(tmp),expr)
            stmts.append(s)
            left = IRVar(tmp)
        else:
            _, left, _=self.left.to_ir(counter)

        if not is_flat(self.right):
            s,expr,counter = self.right.to_ir(counter)
            stmts.extend(s)
            tmp = f"tmp{counter}"
            counter+=1
            s = IRAssign(IRVar(tmp),expr)
            stmts.append(s)
            right = IRVar(tmp)
        else:
            _, right, _ = self.right.to_ir(counter)
        ret= stmts,IROperation(left,self.op,right), counter
        print(ret)
        return ret

@dataclass
class MethodExpression(Expression):
    expr:Expression
    method_name:str
    args:list[str]
    def to_ir():
        pass

@dataclass
class FieldReadExpression(Expression):
    expr:Expression
    field_name:str
    def to_ir():
        pass

@dataclass
class NewObjExpression(Expression):
    class_name:str
    def to_ir():
        pass

@dataclass
class ThisExpression(Expression):
    def to_ir():
        pass

@dataclass
class AssignVarStatement(Statement):
    var_name:str
    val:Expression
    def to_ir(self,prog:IRProgram):
        stmts, expr, _ = self.val.to_ir(0)
        for stmt in stmts:
            prog.add_stmt(stmt)
        s = IRAssign(IRVar(self.var_name),expr)
        prog.add_stmt(s)


@dataclass
class AssignFieldStatement(Statement):
    class_name:str
    field_name:str
    val:Expression
    def to_ir():
        pass

@dataclass
class IfStatement(Statement):
    condition:Expression
    statements_true:list[Statement]
    statements_false:list[Statement]
    def to_ir():
        pass

@dataclass
class IfOnlyStatement(Statement):
    condition:Expression
    statements:list[Statement]
    def to_ir():
        pass

@dataclass
class WhileStatement(Statement):
    condition:Expression
    statements:list[Statement]
    def to_ir():
        pass

@dataclass
class ReturnStatement(Statement):
    val:Expression
    def to_ir():
        pass

@dataclass
class PrintStatement(Statement):
    val:Expression
    def to_ir():
        pass


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
                ret.append(tok.lexeme)
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
                return VarExpression(tok.lexeme)
            case TokenType.NUMBER:
                return NumExpression(tok.lexeme)
            case TokenType.CARET:
                e, _, method_name, _ = self.parse(Expression,TokenType.DOT,[TokenType.IDENTIFIER,TokenType.THIS],TokenType.LPAREN)
                args = []
                t = self.t.peek()
                if t.type != TokenType.RPAREN:
                    args.append(self.parse_expr())
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
                cl = self.parse(TokenType.IDENTIFIER)[0]
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
                return AssignVarStatement(tok.lexeme,expr)
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
                identifiers.append(name.lexeme)
        return identifiers


    def parse_cls(self):
        _, ident, _, _, _ = self.parse(TokenType.CLASS,TokenType.IDENTIFIER,TokenType.LSBRAC,TokenType.NEWLINE,TokenType.FIELDS)
        field_names = self.parse_identifier_list()
        self.parse(TokenType.NEWLINE)
        mths_nested = self.parse_until(TokenType.RSBRAC,Method) # parse_until returns list-of-lists (one list per typeset entry)
        methods = mths_nested[0]
        return Class(ident,field_names,methods)


    def parse_mthd(self):
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

            stmt = self.parse_stmt()
            stmts.append(stmt)
        return Program(cls,locs,stmts)



#TODO flatten math
# convert to ir_context for purpose of uniform interface
# to string methods
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
