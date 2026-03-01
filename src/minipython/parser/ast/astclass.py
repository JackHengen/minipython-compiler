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
    methods:dict[str, Method]

    def to_ir(self,prog:IRProgram):
        prog.curr_class = self
        for m in self.methods.values():
            prog.add_block(self.class_name+m.method_name,["this"]+list(m.args.keys()))
            m.to_ir(prog)
            if not prog.curr_block.ctl_tsf:
                prog.add_ctl_tsf(IRRet(IRConst(0)))

    def validate_types(self,classes:dict[str,Class]):
        var_map = {"this":self.class_name}
        var_map.update(self.fields)
        for m in self.methods.values():
            m.validate_types(var_map,classes,self)
