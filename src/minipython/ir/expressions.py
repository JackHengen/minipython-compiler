from abc import ABC
from dataclasses import dataclass, abstractmethod
from typing import Union

class IRExpression(ABC):
    @abstractmethod
    def get_type(self,type_map:dict[str,str]):
        pass

@dataclass
class IRVar(IRExpression):
    reg:str
    istmp:bool = False
    def __str__(self):
        return f"%{self.reg}"

    def change_vars(self,var_map:dict[str,str]):
        if self.istmp:
            return
        if self.reg in var_map:
            self.reg = var_map[self.reg]

    def get_vars(self):
        return [self]

    def get_type(self,type_map:dict[str,str]):
        pass


@dataclass
class IRConst(IRExpression):
    n:int
    def __str__(self):
        return f"{self.n}"

    def change_vars(self,var_map:dict[str,str]):
        return

    def get_vars(self):
        return []

    def get_type(self,type_map:dict[str,str]):
        pass

@dataclass
class IRBlockName(IRExpression):
    name:str
    def __str__(self):
        return f"@{self.name}"

    def change_vars(self,var_map:dict[str,str]):
        return

    def get_vars(self):
        return []

    def get_type(self,type_map:dict[str,str]):
        pass

NONGLOBALS = Union[IRVar,IRConst]
GLOBALS = Union[NONGLOBALS,IRBlockName]

@dataclass
class IROperation(IRExpression):
    l:NONGLOBALS
    op:str
    r:NONGLOBALS
    def __str__(self):
        return f"{self.l} {self.op} {self.r}"

    def calculate(self):
        if isinstance(self.l,IRConst) and isinstance(self.r,IRConst):
            match self.op:
                case "+":
                    return self.l.n + self.r.n
                case "-":
                    return self.l.n - self.r.n
                case "/":
                    return self.l.n // self.r.n
                case "*":
                    return self.l.n * self.r.n
                case ">":
                    return int(self.l.n > self.r.n)
                case "<":
                    return int(self.l.n < self.r.n)
                case "==":
                    return int(self.l.n == self.r.n)
                case _:
                    return None

    def change_vars(self,var_map:dict[str,str]):
        if isinstance(self.l,IRVar):
            if self.l.reg in var_map:
                self.l.reg = var_map[self.l.reg]

        if isinstance(self.r,IRVar):
            if self.r.reg in var_map:
                self.r.reg = var_map[self.r.reg]

    def get_vars(self):
        return [*self.l.get_vars(),*self.r.get_vars()]

    def get_type(self,type_map:dict[str,str]):
        pass


@dataclass
class IRCall(IRExpression):
    c:IRVar
    r:IRVar
    args:list[NONGLOBALS]
    def __str__(self):
        s = f"call({self.c}, {self.r}"
        for a in self.args:
            s+= f", {a}"
        s+=")"
        return s

    def change_vars(self,var_map:dict[str,str]):
        self.c.change_vars(var_map)
        self.r.change_vars(var_map)
        for arg in self.args:
            arg.change_vars(var_map)

    def get_vars(self):
        return [*self.c.get_vars(),*self.r.get_vars()]

    def get_type(self,type_map:dict[str,str]):
        pass

@dataclass
class IRAlloc(IRExpression):
    n:IRConst
    def __str__(self):
        return f"alloc({self.n})"

    def change_vars(self,var_map:dict[str,str]):
        return

    def get_vars(self):
        return []

    def get_type(self,type_map:dict[str,str]):
        pass


@dataclass
class IRGetELT(IRExpression):
    base:IRVar
    i:NONGLOBALS
    def __str__(self):
        return f"getelt({self.base}, {self.i})"

    def change_vars(self,var_map:dict[str,str]):
        self.base.change_vars(var_map)
        self.i.change_vars(var_map)

    def get_vars(self):
        return [*self.base.get_vars(),*self.i.get_vars()]

    def get_type(self,type_map:dict[str,str]):
        pass

@dataclass
class IRLoad(IRExpression):
    base:IRVar
    def __str__(self):
        return f"load({self.base})"

    def change_vars(self,var_map:dict[str,str]):
        self.base.change_vars(var_map)

    def get_vars(self):
        return self.base.get_vars()

    def get_type(self,type_map:dict[str,str]):
        pass
