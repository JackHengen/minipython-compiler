from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass
from .ast_node import ASTNode

if TYPE_CHECKING:
    from .statements import Statement
    from ...ir.program import IRProgram

@dataclass
class Method(ASTNode):
    method_name:str
    args:dict[str, str]
    local_vars:dict[str, str]
    statements:list[Statement]
    return_t:str

    def to_ir(self,prog:IRProgram):
        prog.curr_types.update(self.args)
        prog.curr_types.update(self.local_vars)
        for s in self.statements:
            s.to_ir(prog)

    def validate_types(self,var_map:dict[str,str],classes:dict[str,Class],curr_class:Class):
        clone = {}
        clone.update(var_map)
        clone.update(self.args)
        clone.update(self.local_vars)
        for s in self.statements:
            s.validate_types(clone,classes,curr_class,self)
        return True
