from __future__ import annotations
from dataclasses import dataclass
from .ast_node import ASTNode

@dataclass
class Method(ASTNode):
    method_name:str
    args:list[str]
    local_vars:list[str]
    statements:list[Statement]

    def to_ir(self,prog:IRProgram):
        for s in self.statements:
            s.to_ir(prog)


