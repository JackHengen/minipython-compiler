from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass

class IRControlTransfer(ABC):
    b_before:"IRBasicBlock" = None

    @abstractmethod
    def successors() -> tuple["IRBasicBlock"]:
        pass

@dataclass
class IRIf(IRControlTransfer):
    v:IRVar
    b_true:IRBasicBlock
    b_false:IRBasicBlock
    def successors(self):
        return (self.b_true,self.b_false)
    def __str__(self):
        return f"if {self.v} then {self.b_true.name} else {self.b_false.name}"

    def change_vars(self,var_map:dict[str,str]):
        self.v.change_vars(var_map)

    def get_vars(self):
        return self.v.get_vars()

@dataclass
class IRJump(IRControlTransfer):
    b_after:IRBasicBlock
    def successors(self):
        return (self.b_after,)
    def __str__(self):
        return f"jump {self.b_after.name}"

    def change_vars(self,var_map:dict[str,str]):
        return

    def get_vars(self):
        return []

@dataclass
class IRRet(IRControlTransfer):
    v:NONGLOBALS
    def successors(self):
        return ()
    def __str__(self):
        return f"ret {self.v}"

    def change_vars(self,var_map:dict[str,str]):
        self.v.change_vars(var_map)

    def get_vars(self):
        return self.v.get_vars()

@dataclass
class IRFail(IRControlTransfer):
    m:str  # For the moment who knows
    def __str__(self):
        pass
