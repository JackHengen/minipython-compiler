from __future__ import annotations
from ..ir.statements import IRAssign
from ..ir.expressions import IROperation, IRConst, IRVar
from ..ir.phi import IRPhi

def pre_eval_opt(prog:IRProgram):
    for block in prog.blocks:
        for i,stmt in enumerate(block.statements):
            if isinstance(stmt,IRAssign):
                if isinstance(stmt.val, IROperation):
                    const = stmt.val.calculate()
                    if const is not None:
                        stmt.val = IRConst(const)

def iterative_dom(prog:IRProgram) -> dict[IRBasicBlock,list[IRBasicBlock]]:
    dom = {prog.blocks[0]:{prog.blocks[0]}}
    for b in prog.blocks[1:]:
        dom[b] = {b for b in prog.blocks}

    changed = True
    while changed:
        changed = False
        for b in prog.blocks:
            if b.predecessors:
                bs = {b for b in prog.blocks}
                for bb in b.predecessors:
                    bs &= dom[bb]
            else:
                bs = set()
            tmp = {b} | bs
            if tmp != dom[b]:
                dom[b] = tmp
                changed = True
    return dom

def idom(domsets:dict[IRBasicBlock,set[IRBasicBlock]]) -> dict[IRBasicBlock,IRBasicBlock]:
    idominated={}
    for b,doms in domsets.items():
        idominated[b] = None  # for the first one which only dominates itself
        goal = domsets[b] - {b}
        for bb in doms:
            if domsets[bb] == goal:
                idominated[b] = bb
                break
    return idominated

def dom_frontier(prog:IRProgram) -> dict[IRBasicBlock,set[IRBasicBlock]]:
    df = {b:set() for b in prog.blocks}
    idominated=idom(iterative_dom(prog))
    for b in prog.blocks:
        if len(b.predecessors) > 1:
            for p in b.predecessors:
                parent = p
                while parent != idominated[b]:
                    df[parent].add(b)
                    parent = idominated[parent]
    return df


def mk_ssa(prog:IRProgram):
    df = dom_frontier(prog)
    globs = set()
    blocks = {}
    for b in prog.blocks:
        varkill = set()
        for s in b.statements:
            if isinstance(s,IRAssign):
                varkill.add(s.v.reg)
                blocks.setdefault(s.v.reg,set())
                blocks[s.v.reg] |= {b}
            for var in s.get_vars():
                if var.reg == "this":
                    continue
                if var.reg not in varkill:
                    globs.add(var.reg)
        for iname in b.input_names:
            varkill.add(iname)
            blocks.setdefault(iname,set())
            blocks[iname] |= {b}


    var_nums = {"tmp":prog.tmp_count}
    for g in globs:
        worklist = set(blocks[g])
        while worklist:
            b = worklist.pop()
            for d in df[b]:
                add = True
                for phi in d.phis:
                    if phi.orig_name == g:
                        add = False
                        break
                
                if add:
                    num = var_nums.setdefault(g,0)
                    d.phis.append(IRPhi(g,IRVar(g+str(num))))
                    var_nums[g] = num + 1
                    worklist |= {d}

    # print("blocks:", {k: [b.name for b in v] for k,v in blocks.items()})
    # print("globs:", globs)
    # print("df:", {b.name: [d.name for d in v] for b,v in df.items()})

    # change variable names for assignments to unique ssa name, map assignment orig name -> block name
    var_maps = {}
    for b in prog.blocks:
        m = var_maps.setdefault(b, dict())
        for phi in b.phis:
            m[phi.orig_name] = phi.assign_var.reg
        for i,iname in enumerate(b.input_names):
            if iname == "this":
                continue
            num = var_nums.setdefault(iname, 0)
            orig = iname
            var_nums[orig] = num + 1
            iname = orig + str(num)
            m[orig] = iname
            b.input_names[i] = iname
        for s in b.statements:
            s.change_vars(m)
            if isinstance(s, IRAssign):
                if s.v.istmp:
                    continue
                num = var_nums.setdefault(s.v.reg, 0)
                orig = s.v.reg
                var_nums[orig] = num + 1
                s.v.reg = orig + str(num)
                m[orig] = s.v.reg
        b.ctl_tsf.change_vars(m)

    # propogate variable names from one block to another and insert appropriate phis
    worklist = list(prog.blocks)
    while worklist:
        b = worklist.pop() 
        m = var_maps[b]
        for s in b.successors:
            for phi in s.phis:
                if phi.orig_name in m and not phi.get_block(m[phi.orig_name]):
                    phi.add(m[phi.orig_name], b)

            sm = var_maps[s]
            changed = False
            for orig_name, new_name in m.items():
                if orig_name not in sm:
                    sm[orig_name] = new_name
                    changed = True
            if changed:
                worklist.append(s)

    for b in prog.blocks:
        in_map = {}
        for p in b.predecessors:
            m = var_maps[p]
            for orig,new in m.items():
                if not orig in b.phis:
                    in_map[orig]=new

        for s in b.statements:
            s.change_vars(in_map)
        b.ctl_tsf.change_vars(in_map)

def lvn(prog:IRProgram):
    for block in prog.blocks:
        vn = {}
        for s in block.statements:
            if isinstance(s,IRAssign):
                if isinstance(s.val,IROperation):
                    if isinstance(s.val.l,IRConst):
                        vl = s.val.l.n
                    else:
                        vl = s.val.l.reg
                    if isinstance(s.val.r,IRConst):
                        vr = s.val.r.n
                    else:
                        vr = s.val.r.reg
                    # the vn is the name but we still have to check if it falls under other names
                    vl = vn.get(vl,vl)
                    vr = vn.get(vr,vr)

                    if s.val.op in {"+","*","=="}:
                        if type(vl) == type(vr):
                            key = (s.val.op,tuple(sorted([vl,vr])))
                        else:
                            if type(vl) == int:
                                key = (s.val.op,(vl,vr))
                            else:
                                key = (s.val.op,(vr,vl))
                    else:
                        key = (s.val.op,(vl,vr))
                else:
                    if isinstance(s.val,IRConst):
                        val = s.val.n
                    elif isinstance(s.val,IRVar):
                        val = s.val.reg
                    else:
                        continue
                    
                    key = vn.get(val,val)

                if key in vn:
                    s.val = IRVar(vn[key])
                    vn[s.v.reg] = vn[key]
                else:
                    vn[s.v.reg] = s.v.reg
                    vn[key] = s.v.reg
