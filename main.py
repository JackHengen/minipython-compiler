import re
import argparse
import sys
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Union, get_args

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
    b_before:"IRBasicBlock" = None

    @abstractmethod
    def successors() -> tuple["IRBasicBlock"]:
        pass


@dataclass
class IRVar(IRExpression):
    reg:str
    def __str__(self):
        return f"%{self.reg}"


@dataclass
class IRConst(IRExpression):
    n:int
    def __str__(self):
        return f"{self.n}"

@dataclass
class IRArray:
    vals:list[Union[str,IRConst]]
    name:str
    def __str__(self):
        s = f"global array {self.name}: {{"
        start = True
        if self.vals:
            s+=" "
            for val in self.vals:
                if start:
                    start = False
                else:
                    s += ", "
                s += f"{val}"
            s+=" "
        s+="}"
        return s

@dataclass(eq=False)
class IRBasicBlock:
    name:str
    statements:list[IRStatement]
    ctl_tsf:IRControlTransfer
    input_names:list[str]
    successors:list["IRBasicBlock"] = field(default_factory=list)
    predecessors:list["IRBasicBlock"] = field(default_factory=list)
    phis:list["IRPhi"] = field(default_factory=dict)

    def __post_init__(self):
        if self.ctl_tsf:
            self.add_ctl_tsf(self.ctl_tsf)

    def add_statement(self,stmt:IRStatement):
        self.statements.append(stmt)

    def add_ctl_tsf(self,trans:IRControlTransfer):
        trans.b_before = self
        self.ctl_tsf=trans
        for s in self.ctl_tsf.successors():
            s.predecessors.append(self)
            self.successors.append(s)

    def __eq__(self, other):
        if not isinstance(other, IRBasicBlock):
            return NotImplemented
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        s = f"{self.name}"
        if self.input_names:
            s+="("
            start = True
            for i in self.input_names:
                if start:
                    start = False
                else:
                    s+=", "
                s+=i
            s+=")"
        s+=":\n"
        for phi in self.phis:
            s==f"{phi}\n"
        for stmt in self.statements:
            s+=f"{stmt}\n"
        s+=f"{self.ctl_tsf}"
        return s

@dataclass
class IRBlockName:
    name:str
    def __str__(self):
        return f"@{self.name}"

NONGLOBALS = Union[IRVar,IRConst]
GLOBALS = Union[NONGLOBALS,IRBlockName]

@dataclass
class IROperation(IRExpression):
    l:NONGLOBALS
    op:str
    r:NONGLOBALS
    def __str__(self):
        return f"{self.l} {self.op} {self.r}"

    def calculate(self):
        if isinstance(self.l,IRConst) and isinstance(self.r,IRConst):
            match self.op:
                case "+":
                    return self.l.n + self.r.n
                case "-":
                    return self.l.n - self.r.n
                case "/":
                    return self.l.n // self.r.n
                case "*":
                    return self.l.n * self.r.n
                case ">":
                    return int(self.l.n > self.r.n)
                case "<":
                    return int(self.l.n < self.r.n)
                case "==":
                    return int(self.l.n == self.r.n)
                case _:
                    return None

@dataclass
class IRCall(IRExpression):
    c:IRVar
    r:IRVar
    args:list[NONGLOBALS]
    def __str__(self):
        s = f"call({self.c}, {self.r}"
        for a in self.args:
            s+= f", {a}"
        s+=")"
        return s

@dataclass
class IRPhi(IRStatement):
    orig_name:str
    assign_var:IRVar
    names:dict[IRVar,IRBasicBlock]=field(default_factory=dict)

    def add(self,var:IRVar,block:IRBasicBlock):
        self.names[var]=block

    def __str__(self):
        s = f'{self.assign_var} = phi('
        start = True
        for var,block in self.names:
            if start:
                start = False
            else:
                s+=", "
            s+=f"{block}, {var}"
        s += ')'
        return s

@dataclass
class IRAlloc(IRExpression):
    n:IRConst
    def __str__(self):
        return f"alloc({self.n})"


@dataclass
class IRGetELT(IRExpression):
    base:IRVar
    i:NONGLOBALS
    def __str__(self):
        return f"getelt({self.base}, {self.i})"

@dataclass
class IRLoad(IRExpression):
    base:IRVar
    def __str__(self):
        return f"load({self.base})"

@dataclass
class IRStore(IRStatement):
    base:IRVar
    i:GLOBALS
    def __str__(self):
        return f"store({self.base}, {self.i})"

@dataclass
class IRSetELT(IRStatement):
    base:IRVar
    i:GLOBALS
    i2:GLOBALS
    def __str__(self):
        return f"setelt({self.base}, {self.i}, {self.i2})"

@dataclass
class IRPrint(IRStatement):
    v:NONGLOBALS
    def __str__(self):
        return f"print({self.v})"

@dataclass
class IRAssign(IRStatement):
    v:IRVar
    val:IRExpression
    def __str__(self):
        return f"{self.v} = {self.val}"

@dataclass
class IRIf(IRControlTransfer):
    v:IRVar
    b_true:IRBasicBlock
    b_false:IRBasicBlock
    def successors(self):
        return (self.b_true,self.b_false)
    def __str__(self):
        return f"if {self.v} then {self.b_true.name} else {self.b_false.name}"

@dataclass
class IRJump(IRControlTransfer):
    b_after:IRBasicBlock
    def successors(self):
        return (self.b_after,)
    def __str__(self):
        return f"jump {self.b_after.name}"

@dataclass
class IRRet(IRControlTransfer):
    v:NONGLOBALS
    def successors(self):
        return ()
    def __str__(self):
        return f"ret {self.v}"

@dataclass
class IRFail(IRControlTransfer):
    m:str  # For the moment who knows
    def __str__(self):
        pass

@dataclass
class IRProgram:
    vtbls: list[IRArray]
    field_maps: list[IRArray]
    field_name_to_map_index: dict[str, int]
    mthd_name_to_vtbl_index: dict[str, int]
    blocks: list[IRBasicBlock] = field(default_factory=list)
    curr_block:IRBasicBlock = None
    tmp_count:int = 0

    def add_block(self,block_name:str,args:list=None):
        if args is None:
            args = []
        self.curr_block = IRBasicBlock(block_name,[],[],args)
        self.blocks.append(self.curr_block)
        return self.curr_block

    def use_tmp(self):
        ret = self.tmp_count
        self.tmp_count+=1
        return ret

    def mk_tmp(self,expr:IRExpression):
        tmp = f"tmp{self.use_tmp()}"
        self.add_stmt(IRAssign(IRVar(tmp),expr))
        return IRVar(tmp)

    def add_stmt(self,stmt:IRStatement):
        self.curr_block.add_statement(stmt)

    def add_ctl_tsf(self,ctl_tsf:IRControlTransfer):
        self.curr_block.add_ctl_tsf(ctl_tsf)

    def __str__(self):
        s = "data:\n"
        order = [item for pair in zip(self.vtbls,self.field_maps) for item in pair]
        for arr in order:
            s+=f"{arr}\n"
        s += "code:\n\n"
        for b in self.blocks:
            if b.input_names or b.name == "main":
                s+="\n"
            s+= f"{b}\n"
        return s




class ASTNode(ABC):
    # to_ir()
    pass

class Statement(ASTNode):
    @abstractmethod
    def to_ir(self,prog:IRProgram):
        pass

class Expression(ASTNode):
    @abstractmethod
    def to_ir(self,prog:IRProgram) -> IRExpression:
        pass

@dataclass
class Method(ASTNode):
    method_name:str
    args:list[str]
    local_vars:list[str]
    statements:list[Statement]

    def to_ir(self,prog:IRProgram):
        for s in self.statements:
            s.to_ir(prog)


@dataclass
class Class(ASTNode):
    class_name:str
    fields:list[str]
    methods:list[Method]

    def to_ir(self,prog:IRProgram):
        for m in self.methods:
            prog.add_block(self.class_name+m.method_name,["this"]+m.args)
            m.to_ir(prog)
            if not prog.curr_block.ctl_tsf:
                prog.add_ctl_tsf(IRRet(IRConst(0)))



@dataclass
class Program(ASTNode):
    classes:list[Class]
    local_vars:list[str]
    statements:list[Statement]

    def to_ir_program(self):
        field_map = {}
        mthd_map = {}
        fcounter = 0
        vcounter = 0
        for c in self.classes:
            for f in c.fields:
                if f not in field_map:
                    field_map[f] = fcounter
                    fcounter += 1
            for m in c.methods:
                n = m.method_name
                if n not in mthd_map:
                    mthd_map[n] = vcounter
                    vcounter += 1


        vtbls = []
        class_field_maps = []
        for c in self.classes:
            counter = 2  # first field offset
            class_map = []
            for i in range(len(field_map)):
                class_map.append(0)

            vtbl = []
            for i in range(len(mthd_map)):
                vtbl.append(0)

            for f in c.fields:
                class_map[field_map[f]] = counter
                counter += 1
            class_field_maps.append(IRArray(class_map,f"fields{c.class_name}"))

            for m in c.methods:
                vtbl[mthd_map[m.method_name]] = (c.class_name + m.method_name)
            vtbls.append(IRArray(vtbl,f"vtbl{c.class_name}"))

        prog = IRProgram(vtbls,class_field_maps,field_map,mthd_map)
        return self.to_ir(prog)

    def to_ir(self,prog:IRProgram):
        for c in self.classes:
            c.to_ir(prog)

        prog.add_block("main")
        for stmt in self.statements:
            stmt.to_ir(prog)
        if not prog.curr_block.ctl_tsf:
            prog.add_ctl_tsf(IRRet(IRConst(0)))

        return prog

@dataclass
class NumExpression(Expression):
    num:int
    def __post_init__(self):
        self.num = int(self.num)
    def to_ir(self,prog:IRProgram):
        return IRConst(self.num)


@dataclass
class VarExpression(Expression):
    var_name:str
    def to_ir(self,prog:IRProgram):
        return IRVar(self.var_name)


@dataclass
class ParenExpression(Expression):
    left:Expression
    op:str
    right:Expression
    def to_ir(self,prog:IRProgram):
        left = self.left.to_ir(prog)
        if not isinstance(left,get_args(NONGLOBALS)):
            left = prog.mk_tmp(left)

        right = self.right.to_ir(prog)
        if not isinstance(right,get_args(NONGLOBALS)):
            right = prog.mk_tmp(right)

        return IROperation(left,self.op,right)

@dataclass
class MethodExpression(Expression):
    expr:Expression
    method_name:str
    args:list[Expression]
    def to_ir(self,prog:IRProgram):
        args = [a.to_ir(prog) for a in self.args]
        for i in range(len(args)):
            a = args[i]
            if not isinstance(a,NONGLOBALS):
                args[i] = prog.mk_tmp(a)

        expr = self.expr.to_ir(prog)
        if not isinstance(expr,IRVar):
            expr = prog.mk_tmp(expr)
        load = prog.mk_tmp(IRLoad(expr))
        
        base = load
        i = prog.mthd_name_to_vtbl_index[self.method_name]
        getelt = prog.mk_tmp(IRGetELT(base,i))

        return IRCall(getelt,expr,args)


@dataclass
class FieldReadExpression(Expression):
    expr:Expression
    field_name:str
    def to_ir(self,prog:IRProgram):
        expr = self.expr.to_ir(prog)
        if not isinstance(expr,IRVar):
            expr = prog.mk_tmp(expr)

        addr = prog.mk_tmp(IROperation(expr,"+",IRConst(8)))

        load = prog.mk_tmp(IRLoad(addr)) # load in fields for class

        base = load
        field_ind = prog.field_name_to_map_index[self.field_name] 

        class_field_ind = prog.mk_tmp(IRGetELT(base,field_ind)) # grab field from fields

        return IRGetELT(expr,class_field_ind)
        

@dataclass
class NewObjExpression(Expression):
    class_name:str
    def to_ir(self,prog:IRProgram):
        field_map = None
        for fm in prog.field_maps:
            if fm.name.endswith(self.class_name):
                field_map = fm

        if not field_map:
            raise NameError(f"No such class {self.class_name}")

        tmp = f"tmp{prog.use_tmp()}"
        alloc = IRAssign(IRVar(tmp),IRAlloc(2+len(field_map.vals)))
        addvtbl = IRStore(IRVar(tmp),IRBlockName(f"vtbl{self.class_name}"))

        tmp2 = f"tmp{prog.use_tmp()}"
        addaddr = IRAssign(IRVar(tmp2),IROperation(IRVar(tmp),"+",IRConst(8)))
        addfields = IRStore(IRVar(tmp2),IRBlockName(f"fields{self.class_name}")) 

        prog.add_stmt(alloc)
        prog.add_stmt(addvtbl)
        prog.add_stmt(addaddr)
        prog.add_stmt(addfields)

        return IRVar(tmp)


@dataclass
class ThisExpression(Expression):
    def to_ir(self,prog:IRProgram):
        return IRVar("this")

@dataclass
class AssignVarStatement(Statement):
    var_name:str
    val:Expression
    def to_ir(self,prog:IRProgram):
        expr = self.val.to_ir(prog)
        if self.var_name == "_":
            prog.mk_tmp(expr)
        else:
            s = IRAssign(IRVar(self.var_name),expr) 
            prog.add_stmt(s)


@dataclass
class AssignFieldStatement(Statement):
    obj_expr:Expression
    field_name:str
    val:Expression
    def to_ir(self,prog:IRProgram):
        obj_expr = self.obj_expr.to_ir(prog)
        if not isinstance(obj_expr,IRVar):
            obj_expr = prog.mk_tmp(obj_expr)

        addr = prog.mk_tmp(IROperation(obj_expr,"+",IRConst(8)))

        load = prog.mk_tmp(IRLoad(addr)) # load in fields for class

        base = load
        field_ind = prog.field_name_to_map_index[self.field_name] 

        class_field_ind = prog.mk_tmp(IRGetELT(base,field_ind)) # grab field from fields

        val = self.val.to_ir(prog)
        if not isinstance(val,IRVar):
            val = prog.mk_tmp(val)

        prog.add_stmt(IRSetELT(obj_expr,class_field_ind,val))

@dataclass
class IfStatement(Statement):
    condition:Expression
    statements_true:list[Statement]
    statements_false:list[Statement]
    def to_ir(self,prog:IRProgram):
        true = f"true{prog.use_tmp()}"
        false = f"false{prog.use_tmp()}"
        after = f"after{prog.use_tmp()}"

        expr = self.condition.to_ir(prog)
        if not isinstance(expr,IRVar):
            expr = prog.mk_tmp(expr)

        currblock = prog.curr_block

        prog.add_block(true)
        trueblock = prog.curr_block
        for s in self.statements_true:
            s.to_ir(prog)
        endtrueblock = prog.curr_block

        prog.add_block(false)
        falseblock = prog.curr_block
        for s in self.statements_false:
            s.to_ir(prog)
        endfalseblock = prog.curr_block

        prog.add_block(after)
        afterblock = prog.curr_block

        currblock.add_ctl_tsf(IRIf(expr,trueblock,falseblock))
        if not endtrueblock.ctl_tsf:
            endtrueblock.add_ctl_tsf(IRJump(afterblock))
        if not endfalseblock.ctl_tsf:
            endfalseblock.add_ctl_tsf(IRJump(afterblock))

@dataclass
class IfOnlyStatement(Statement):
    condition:Expression
    statements:list[Statement]
    def to_ir(self,prog:IRProgram):
        true = f"true{prog.use_tmp()}"
        after = f"after{prog.use_tmp()}"

        expr = self.condition.to_ir(prog)
        if not isinstance(expr,IRVar):
            expr = prog.mk_tmp(expr)

        currblock = prog.curr_block

        prog.add_block(true)
        trueblock = prog.curr_block
        for s in self.statements:
            s.to_ir(prog)
        endtrueblock = prog.curr_block

        prog.add_block(after)
        afterblock = prog.curr_block

        currblock.add_ctl_tsf(IRIf(expr,trueblock,afterblock))
        if not endtrueblock.ctl_tsf: #theoretically the only thing this should not be true on is a return
            endtrueblock.add_ctl_tsf(IRJump(afterblock))

@dataclass
class WhileStatement(Statement):
    condition:Expression
    statements:list[Statement]
    def to_ir(self,prog:IRProgram):
        cond = f"cond{prog.use_tmp()}"
        true = f"true{prog.use_tmp()}"
        after = f"after{prog.use_tmp()}"

        currblock = prog.curr_block
        prog.add_block(cond)
        condblock = prog.curr_block

        currblock.add_ctl_tsf(IRJump(condblock))

        expr = self.condition.to_ir(prog)
        if not isinstance(expr,IRVar):
            expr = prog.mk_tmp(expr)

        prog.add_block(true)
        trueblock = prog.curr_block
        for s in self.statements:
            s.to_ir(prog)
        endtrueblock = prog.curr_block

        if not endtrueblock.ctl_tsf:
            endtrueblock.add_ctl_tsf(IRJump(condblock))
        

        prog.add_block(after)
        afterblock = prog.curr_block

        condblock.add_ctl_tsf(IRIf(expr,trueblock,afterblock))

@dataclass
class ReturnStatement(Statement):
    val:Expression
    def to_ir(self,prog:IRProgram):
        expr = self.val.to_ir(prog)
        if isinstance(expr,get_args(NONGLOBALS)):
            stmt = IRRet(expr)
        else:
            stmt = IRRet(prog.mk_tmp(expr))
        prog.add_ctl_tsf(stmt)

@dataclass
class PrintStatement(Statement):
    val:Expression
    def to_ir(self,prog:IRProgram):
        expr = self.val.to_ir(prog)
        if isinstance(expr,get_args(NONGLOBALS)):
            stmt = IRPrint(expr)
        else:
            stmt = IRPrint(prog.mk_tmp(expr))
        prog.add_stmt(stmt)

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
                obj, _, field_name, _, expr = self.parse(Expression,TokenType.DOT,TokenType.IDENTIFIER,TokenType.EQUAL,Expression)
                return AssignFieldStatement(obj,field_name,expr)
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
        self.parse_error(f"Incorrect token for start of statement: {tok}")

    def parse_identifier_list(self):
        identifiers = []
        if self.t.peek().type == TokenType.IDENTIFIER:
            identifiers.append(self.parse(TokenType.IDENTIFIER)[0])
            while(self.t.peek().type == TokenType.COMMA):
                self.t.get_next()
                identifiers.append(self.parse(TokenType.IDENTIFIER)[0])
        return identifiers


    def parse_cls(self):
        _, ident, _, _, _ = self.parse(TokenType.CLASS,TokenType.IDENTIFIER,TokenType.LSBRAC,TokenType.NEWLINE,TokenType.FIELDS)
        field_names = self.parse_identifier_list()
        self.parse(TokenType.NEWLINE)
        mths_nested = self.parse_until(TokenType.RSBRAC,Method)  # parse_until returns list-of-lists (even though we only have one nested list)
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

def pre_eval_opt(prog:IRProgram):
    for block in prog.blocks:
        for i,stmt in enumerate(block.statements):
            if isinstance(stmt,IRAssign):
                if isinstance(stmt.val, IROperation):
                    const = stmt.val.calculate()
                    if const is not None:
                        stmt.val = IRConst(const)

def iterative_dom(prog:IRProgram) -> dict[IRBasicBlock,list[IRBasicBlock]]:
    dom = {prog.blocks[0]:{prog.blocks[0]}}
    for b in prog.blocks[1:]:
        dom[b] = {b for b in prog.blocks}

    changed = True
    while changed:
        changed = False
        for b in prog.blocks:
            if b.predecessors:
                bs = {b for b in prog.blocks}
                for bb in b.predecessors:
                    bs &= dom[bb]
            else:
                bs = set()
            tmp = {b} | bs
            if tmp != dom[b]:
                dom[b] = tmp
                changed = True
    return dom

def idom(domsets:dict[IRBasicBlock,set[IRBasicBlock]]) -> dict[IRBasicBlock,IRBasicBlock]:
    idominated={}
    for b,doms in domsets.items():
        idominated[b] = None  # for the first one which only dominates itself
        goal = domsets[b] - {b}
        for bb in doms:
            if domsets[bb] == goal:
                idominated[b] = bb
                break
    return idominated

def dom_frontier(prog:IRProgram) -> dict[IRBasicBlock,set[IRBasicBlock]]:
    df = {b:set() for b in prog.blocks}
    idominated=idom(iterative_dom(prog))
    for b in prog.blocks:
        if len(b.predecessors) > 1:
            for p in b.predecessors:
                parent = p
                while parent != idominated[b]:
                    df[parent].add(b)
                    parent = idominated[parent]
    return df


def mk_ssa(prog:IRProgram):
    df = dom_frontier(prog)
    globs = set()
    blocks = {b:set() for b in prog.blocks}
    for b in prog.blocks:
        varkill = set()
        for s in b:
            if isinstance(s,IRAssign):
                # var = re.sub("[1234567890]+",'',s.v.reg)
                varkill.add(s.v)
                if isinstance(s.val,IROperation):
                    if isinstance(s.val.l,IRVar):
                        globs.add(s.val.l)
                    if isinstance(s.val.r,IRVar):
                        globs.add(s.val.r)
                elif isinstance(s.val,IRVar):
                    globs.add(s.val)
                blocks[s.v] = blocks[s.v] | b


    var_nums = {}
    for g in globs:
        worklist = blocks[g]
        for b in worklist:
            for d in df[b]:
                num = var_nums.setdefault(g,0)
                d.phis.append(IRPhi(s.v,s.v+str(num)))
                var_nums[g] = num + 1
                worklist = worklist | d

    var_maps = {}
    for b in prog.blocks:
        m = var_maps.setdefault(b,dict())
        for phi in b.phis:
            m[phi.orig_name] = (phi.assign_var,b)
        for s in b.statements:
            if isinstance(s,IRAssign):
                num = var_nums.set_default(s.v,0)
                orig = s.v.reg
                s.v.reg = s.v.reg + num
                m[orig] = (s.v.reg,b)
        for p in b.successors:
            pm = var_maps.setdefault(p,dict())
            for orig_name,var_info in m.items():
                new_name,_ = var_info
                if orig_name not in pm:
                    pm[orig_name] = (new_name,b)

    for b in prog.blocks:
        for phi in b.phis:
            infos = var_maps[b][phi.orig_name]
            for name,block in infos:
                phi.add(name,block)



# change order of args in IRPROG
# validate things like never ending loops
# validate early returns and still more statements
# tests for evaluation right now i just eyeball it
# validate operators once i find out which are permitted according to the ir
# should we be validating if methods exist or fields exist or vars exist?
# regression tests for returns before other stmts working, and not overwriting the blocks control transfers if a while
# or if or ifonly

# ssa AND phi to str
# tagging numbers


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="MiniPython Compiler")
    parser.add_argument("file", nargs="?", help="Input file (default if --str/--stdin) not set manually")
    input_group = parser.add_mutually_exclusive_group(required=False)

    input_group.add_argument("--str","--string",help="Input provided as arg through commandline", action='store_true')
    input_group.add_argument("--stdin",help="Input provided through stdin", action='store_true')

    stage_group = parser.add_mutually_exclusive_group()
    stage_group.add_argument("-t","--tokenize", help='Execute through tokenize stage', action='store_true')
    stage_group.add_argument("-p","--parse",help="Execute through parse stage",action='store_true')
    stage_group.add_argument("-c","-noopt","--noopt","--cfg",help="Execute through IR cfg stage",action='store_true')
    stage_group.add_argument("-o","--opt","--optimize","--optimization",help="Execute through IR optimization stage",action='store_true')
    stage_group.add_argument("-s","--ssa",help="Execute through IR ssa stage",action="store_true")
    args = parser.parse_args()


    if not any([args.file, args.str, args.stdin]):
        parser.error("Must provide input: filename, --str, or --stdin")

    if not any([args.tokenize, args.parse, args.noopt, args.ssa]):
        args.opt = True

    if args.str:
        inp = args.str
    elif args.stdin:
        inp = sys.stdin.read()
    else:
        with open(args.file) as f:
            inp = f.read()

    t = Tokenizer(inp)
    toks = t.tokenize()
    if args.tokenize:
        print(toks)
        sys.exit()

    p = Parser(t)
    parse_tree = p.parse_program()
    if args.parse:
        print(parse_tree)
        sys.exit()

    prog = parse_tree.to_ir_program()
    if args.noopt:
        print(prog)
        sys.exit()

    pre_eval_opt(prog)
    if args.opt:
        print(prog)
        sys.exit()

    mk_ssa(prog)
    if args.ssa:
        print("not implemented yet")
        sys.exit()
        print(prog)
