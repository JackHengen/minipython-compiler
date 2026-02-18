from __future__ import annotations
from dataclasses import dataclass, field
from .expressions import IRVar

@dataclass
class IRPhi:
    orig_name:str
    assign_var:IRVar
    names:dict[str,IRBasicBlock]=field(default_factory=dict)

    def add(self,var_name:str,block:IRBasicBlock):
        self.names[var_name]=block

    def get_block(self,name):
        if name in self.names:
            return self.names[name]
        else:
            return None

    def __str__(self):
        s = f'{self.assign_var} = phi('
        start = True
        for var,block in self.names.items():
            if start:
                start = False
            else:
                s+=", "
            s+=f"{block.name}, {IRVar(var)}"
        s += ')'
        return s




