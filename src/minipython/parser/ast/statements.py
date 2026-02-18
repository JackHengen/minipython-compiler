from __future__ import annotations
from .ast_node import ASTNode
from abc import abstractmethod
from dataclasses import dataclass
from typing import get_args
from ...ir.expressions import IRVar, IROperation, IRConst, IRLoad, IRGetELT, NONGLOBALS
from ...ir.statements import IRAssign, IRPrint, IRSetELT
from ...ir.control_transfer import IRIf, IRJump, IRRet


class Statement(ASTNode):
    @abstractmethod
    def to_ir(self,prog:IRProgram):
        pass

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

        class_field_ind = prog.mk_tmp(IRGetELT(base,IRConst(field_ind))) # grab field from fields

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
