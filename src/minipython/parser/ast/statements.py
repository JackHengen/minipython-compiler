from __future__ import annotations
from typing import TYPE_CHECKING
from .ast_node import ASTNode
from abc import abstractmethod
from dataclasses import dataclass
from typing import get_args
from .expressions import Expression
from ...ir.expressions import IRVar, IROperation, IRConst, IRLoad, IRGetELT, NONGLOBALS
from ...ir.statements import IRAssign, IRPrint, IRSetELT
from ...ir.control_transfer import IRIf, IRJump, IRRet

if TYPE_CHECKING:
    from ...ir.program import IRProgram
    from .method import Method
    from .astclass import Class

class Statement(ASTNode):
    @abstractmethod
    def to_ir(self,prog:IRProgram):
        pass

    @abstractmethod
    def validate_types(self,var_map:dict[str,str],classes:dict[str,Class],curr_class:Class,curr_method:Method):
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

    def validate_types(self,var_map:dict[str,str],classes:dict[str,Class],curr_class:Class,curr_method:Method):
        if self.var_name in var_map:
            var_t = var_map[self.var_name]
            val_t = self.val.get_type(var_map,classes)
            if var_t == val_t:
                return True
            else:
                raise Exception(f"Invalid type for variable assignment: variable {self.var_name} has type {var_t}, {val_t} was provided instead")


@dataclass
class AssignFieldStatement(Statement):
    obj_expr:Expression
    field_name:str
    val:Expression
    def to_ir(self,prog:IRProgram):
        obj_expr = self.obj_expr.to_ir(prog)
        if not isinstance(obj_expr,IRVar):
            obj_expr = prog.mk_tmp(obj_expr)

        obj_class = prog.classes[self.obj_expr.get_type(prog.curr_types,prog.classes)]
        i = obj_class.get_field_index(self.field_name) 

        val = self.val.to_ir(prog)
        if not isinstance(val,IRVar):
            val = prog.mk_tmp(val)

        prog.add_stmt(IRSetELT(obj_expr,IRConst(1+i),val))

    def validate_types(self,var_map:dict[str,str],classes:dict[str,Class],curr_class:Class,curr_method:Method):
        class_name = self.obj_expr.get_type(var_map,classes)
        if class_name in classes:
            klass = classes[class_name]
            if self.field_name in klass.fields:
                field_t = klass.fields[self.field_name]
                assign_t = self.val.get_type(var_map,classes)
                if field_t == assign_t:
                    return True
                else:
                    raise Exception(f"Invalid type for field assignment: {class_name}.{self.field_name} of type {field_t}, {assign_t} was provided instead")
            else:
                raise Exception(f"Field: {class_name}.{field_name} does not exist, from {self}")
        else:
            raise Exception(f"Class: {class_name} does not exist, from {self}")

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

    def validate_types(self,var_map:dict[str,str],classes:dict[str,Class],curr_class:Class,curr_method:Method):
        cond_t = self.condition.get_type(var_map,classes)
        if cond_t != "int":
            raise Exception(f"Invalid conditional type: {cond_t}, must be int")

        else:
            for s in self.statements_true:
                s.validate_types(var_map,classes,curr_class,curr_method)
            for s in self.statements_false:
                s.validate_types(var_map,classes,curr_class,curr_method)
            return True

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

    def validate_types(self,var_map:dict[str,str],classes:dict[str,Class],curr_class:Class,curr_method:Method):
        cond_t = self.condition.get_type(var_map,classes)
        if cond_t != "int":
            raise Exception(f"Invalid conditional type: {cond_t}, must be int")

        else:
            for s in self.statements:
                s.validate_types(var_map,classes,curr_class,curr_method)
            return True

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

    def validate_types(self,var_map:dict[str,str],classes:dict[str,Class],curr_class:Class,curr_method:Method):
        cond_t = self.condition.get_type(var_map,classes)
        if cond_t != "int":
            raise Exception(f"Invalid conditional type: {cond_t}, must be int")

        else:
            for s in self.statements:
                s.validate_types(var_map,classes,curr_class,curr_method)
            return True
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

    def validate_types(self,var_map:dict[str,str],classes:dict[str,Class],curr_class:Class,curr_method:Method):
        ret_t = self.val.get_type(var_map,classes)
        if curr_class != "Main":
            expect_t = curr_method.return_t
        else:
            expect_t = "int"


        if ret_t == expect_t:
            return True
        else:
            raise Exception(f"Invalid return type: {ret_t} for Method: {curr_method.method_name}, should be {expect_t}")

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

    def validate_types(self,var_map:dict[str,str],classes:dict[str,Class],curr_class:Class,curr_method:Method):
        print_t = self.val.get_type(var_map,classes)
        if print_t == "int":
            return True
        else:
            raise Exception(f"Invalid type for printing: {print_t}, can only print int")
