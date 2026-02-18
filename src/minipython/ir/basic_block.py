from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(eq=False)
class IRBasicBlock:
    name:str
    statements:list[IRStatement]
    ctl_tsf:IRControlTransfer
    input_names:list[str]
    successors:list["IRBasicBlock"] = field(default_factory=list)
    predecessors:list["IRBasicBlock"] = field(default_factory=list)
    phis:list["IRPhi"] = field(default_factory=list)

    def __post_init__(self):
        if self.ctl_tsf:
            self.add_ctl_tsf(self.ctl_tsf)

    def add_statement(self,stmt:IRStatement):
        self.statements.append(stmt)

    def add_ctl_tsf(self,trans:IRControlTransfer):
        trans.b_before = self
        self.ctl_tsf=trans
        for s in self.ctl_tsf.successors():
            s.predecessors.append(self)
            self.successors.append(s)

    def __eq__(self, other):
        if not isinstance(other, IRBasicBlock):
            return NotImplemented
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        s = f"{self.name}"
        if self.input_names:
            s+="("
            start = True
            for i in self.input_names:
                if start:
                    start = False
                else:
                    s+=", "
                s+=i
            s+=")"
        s+=":\n"
        for phi in self.phis:
            s+=f"{phi}\n"
        for stmt in self.statements:
            s+=f"{stmt}\n"
        s+=f"{self.ctl_tsf}"
        return s

