from __future__ import annotations
from .ast_node import ASTNode
from dataclasses import dataclass
from abc import abstractmethod
from ...ir.expressions import IRAlloc, IRBlockName, IRCall, IRConst, IRGetELT, IRLoad, IROperation, IRVar, NONGLOBALS
from ...ir.statements import IRStore
from typing import get_args, TYPE_CHECKING

if TYPE_CHECKING:
    from ...ir.program import IRProgram
    from ...ir.expressions import IRExpression

class Expression(ASTNode):
    @abstractmethod
    def to_ir(self,prog:IRProgram) -> IRExpression:
        pass

@dataclass
class NullExpression(Expression):
    class_name:str
    def to_ir(self,prog:IRProgram):
        return IRConst(0)

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
        getelt = prog.mk_tmp(IRGetELT(base,IRConst(i)))

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

        class_field_ind = prog.mk_tmp(IRGetELT(base,IRConst(field_ind))) # grab field from fields

        return IRGetELT(expr,IRConst(class_field_ind))

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

        alloc = prog.mk_tmp(IRAlloc(2+len(field_map.vals)))
        prog.add_stmt(IRStore(alloc,IRBlockName(f"vtbl{self.class_name}")))

        tmp2 = f"tmp{prog.use_tmp()}"
        addaddr = prog.mk_tmp(IROperation(alloc,"+",IRConst(8)))
        prog.add_stmt(IRStore(addaddr,IRBlockName(f"fields{self.class_name}")) )


        return alloc


@dataclass
class ThisExpression(Expression):
    def to_ir(self,prog:IRProgram):
        return IRVar("this")
