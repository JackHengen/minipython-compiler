from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass
from .ast_node import ASTNode
from ...ir.program import IRProgram
from ...ir.control_transfer import IRRet
from ...ir.expressions import IRConst
from ...ir.array import IRArray

if TYPE_CHECKING:
    from .astclass import Class
    from .statements import Statement

@dataclass
class Program(ASTNode):
    classes:dict[str,Class]
    local_vars:dict[str, str]
    statements:list[Statement]

    def to_ir_program(self):
        # TODO can prob refactor this into smth that is modifed each time we add a class
        field_map = {}
        mthd_map = {}
        fcounter = 0
        vcounter = 0
        for c in self.classes.values():
            for f in c.fields.keys():
                if f not in field_map:
                    field_map[f] = fcounter
                    fcounter += 1
            for m in c.methods.values():
                n = m.method_name
                if n not in mthd_map:
                    mthd_map[n] = vcounter
                    vcounter += 1


        vtbls = []
        class_field_maps = []
        for c in self.classes.values():
            counter = 2  # first field offset
            class_map = []
            for i in range(len(field_map)):
                class_map.append(0)

            vtbl = []
            for i in range(len(mthd_map)):
                vtbl.append(0)

            for f in c.fields.keys():
                class_map[field_map[f]] = counter
                counter += 1
            class_field_maps.append(IRArray(class_map,f"fields{c.class_name}"))

            for m in c.methods.values():
                vtbl[mthd_map[m.method_name]] = (c.class_name + m.method_name)
            vtbls.append(IRArray(vtbl,f"vtbl{c.class_name}"))

        prog = IRProgram(vtbls,class_field_maps,field_map,mthd_map)
        return self.to_ir(prog)

    def to_ir(self,prog:IRProgram):
        for c in self.classes.values():
            c.to_ir(prog)

        prog.add_block("main")
        for stmt in self.statements:
            stmt.to_ir(prog)
        if not prog.curr_block.ctl_tsf:
            prog.add_ctl_tsf(IRRet(IRConst(0)))

        return prog

    def validate_types(self):
        for c in self.classes.values():
            c.validate_types(self.classes)

        var_map = {}
        var_map.update(self.local_vars)
        for s in self.statements:
            s.validate_types(var_map,self.classes,"Main","main")

