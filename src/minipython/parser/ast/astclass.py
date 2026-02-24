from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass
from .ast_node import ASTNode
from ...ir.control_transfer import IRRet
from ...ir.expressions import IRConst

if TYPE_CHECKING:
    from .method import Method
    from ...ir.program import IRProgram

@dataclass
class Class(ASTNode):
    class_name:str
    fields:dict[str, str]
    methods:list[Method]

    def to_ir(self,prog:IRProgram):
        for m in self.methods:
            prog.add_block(self.class_name+m.method_name,{"this":self.class_name}.update(m.args))
            m.to_ir(prog)
            if not prog.curr_block.ctl_tsf:
                prog.add_ctl_tsf(IRRet(IRConst(0)))
