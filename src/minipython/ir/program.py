from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass, field
from .statements import IRAssign
from .expressions import IRVar
from .basic_block import IRBasicBlock

if TYPE_CHECKING:
    from .expressions import IRExpression
    from .statements import IRStatement
    from .array import IRArray
    from .control_transfer import IRControlTransfer

@dataclass
class IRProgram:
    vtbls: list[IRArray]
    field_maps: list[IRArray]
    field_name_to_map_index: dict[str, int]
    mthd_name_to_vtbl_index: dict[str, int]
    blocks: list[IRBasicBlock] = field(default_factory=list)
    curr_block:IRBasicBlock = None
    tmp_count:int = 0
    curr_class:Class= None

    def add_block(self,block_name:str,args:list=None):
        if args is None:
            args = []
        self.curr_block = IRBasicBlock(block_name,[],[],args)
        self.blocks.append(self.curr_block)
        return self.curr_block

    def use_tmp(self):
        ret = self.tmp_count
        self.tmp_count+=1
        return ret

    def mk_tmp(self,expr:IRExpression):
        tmp = f"tmp{self.use_tmp()}"
        self.add_stmt(IRAssign(IRVar(tmp,True),expr))
        return IRVar(tmp)

    def add_stmt(self,stmt:IRStatement):
        self.curr_block.add_statement(stmt)

    def add_ctl_tsf(self,ctl_tsf:IRControlTransfer):
        self.curr_block.add_ctl_tsf(ctl_tsf)

    def __str__(self):
        s = "data:\n"
        order = [item for pair in zip(self.vtbls,self.field_maps) for item in pair]
        for arr in order:
            s+=f"{arr}\n"
        s += "code:\n\n"
        for b in self.blocks:
            if b.input_names or b.name == "main":
                s+="\n"
            s+= f"{b}\n"
        return s
