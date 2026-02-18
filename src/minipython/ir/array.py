from __future__ import annotations
from dataclasses import dataclass

@dataclass
class IRArray:
    vals:list[Union[str,IRConst]]
    name:str
    def __str__(self):
        s = f"global array {self.name}: {{"
        start = True
        if self.vals:
            s+=" "
            for val in self.vals:
                if start:
                    start = False
                else:
                    s += ", "
                s += f"{val}"
            s+=" "
        s+="}"
        return s


