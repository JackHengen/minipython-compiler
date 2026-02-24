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
        for s in self.statements:
            s.to_ir(prog)
