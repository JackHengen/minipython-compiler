from __future__ import annotations
from abc import ABC
from dataclasses import dataclass

class IRStatement(ABC):
    pass

@dataclass
class IRStore(IRStatement):
    base:IRVar
    i:GLOBALS
    def __str__(self):
        return f"store({self.base}, {self.i})"

    def change_vars(self,var_map:dict[str,str]):
        self.i.change_vars(var_map)
        self.base.change_vars(var_map)

    def get_vars(self):
        return [*self.base.get_vars(),*self.i.get_vars()]

@dataclass
class IRSetELT(IRStatement):
    base:IRVar
    i:GLOBALS
    i2:GLOBALS
    def __str__(self):
        return f"setelt({self.base}, {self.i}, {self.i2})"

    def change_vars(self,var_map:dict[str,str]):
        self.base.change_vars(var_map)
        self.i.change_vars(var_map)
        self.i2.change_vars(var_map)

    def get_vars(self):
        return [*self.base.get_vars(),*self.i.get_vars(),*self.i2.get_vars()]

@dataclass
class IRPrint(IRStatement):
    v:NONGLOBALS
    def __str__(self):
        return f"print({self.v})"

    def change_vars(self,var_map:dict[str,str]):
        self.v.change_vars(var_map)

    def get_vars(self):
        return self.v.get_vars()

@dataclass
class IRAssign(IRStatement):
    v:IRVar
    val:IRExpression
    def __str__(self):
        return f"{self.v} = {self.val}"

    def change_vars(self,var_map:dict[str,str]):
        self.val.change_vars(var_map)

    def get_vars(self): #DOES NOT INCLUDE THE V TO ASSIGN TO
        return self.val.get_vars()
