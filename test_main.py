from main import *
import time
import pytest

first_example = """class A [
    fields x
    method m() with locals:
      return &this.x
]
class B [
    fields y
    method m() with locals:
      return 0
]

main with x:
x = @A
!x.x = 3
print(^x.m())"""

# This code pushes a few values on a stack, then pops and prints in reverse order
# So this should print 9, then 5, then 3, then 1, then 0 (which is the default the stack returns when popping an empty stack)
# Global value numbering on the main routine should remove a lot of pointer tag checks, and consequently result in fewer basic blocks for main.
# If you have implemented value numbering for field map and vtbl lookups, most of those will also be removed.
# A smaller number of tag checks will be removed from the code of the stack methods.
simple_stack = """class ListNode [
    fields val, next
    method getNext() with locals:
        return &this.next
    method getVal() with locals:
        return &this.val
]
class Stack [
    fields list
    method push(v) with locals tmp:
        tmp = @ListNode
	!tmp.val = v
	!tmp.next = &this.list
	!this.list = tmp
	return 0
    method pop() with locals tmp, head:
        if (&this.list == 0): {
            return 0
        } else {
            head = &this.list
            tmp = ^head.getVal()
            !this.list = ^head.getNext()
            return tmp
        }
]

main with stk:
    stk = @Stack
    !stk.list = 0
    _ = ^stk.push(1)
    _ = ^stk.push(3)
    _ = ^stk.push(5)
    _ = ^stk.push(9)
    print(^stk.pop())
    print(^stk.pop())
    print(^stk.pop())
    print(^stk.pop())
    print(^stk.pop())
    """

# Slightly more complex stack use, with a loop.
# In the *second* loop, the tag check on the stack should be removed by some optimization in a later milestone, because the loop body is dominated by the tag check for the initial pre-loop pop
# In the *first* loop, the tag check must stay, because the first loop is not dominated by a tag check on the stack reference.
# Code motion could move the tag check from inside the loop to outside, but recall that GVN does not move evaluations, it only replaces redundant computations with references to earlier results
# Note: the reason the stack manipulation was moved into a method was explicitly to hide dominance of the first loop by a tag check. If we left the loops in main, then both loops *would* be dominated by the pointer check arising from initializing stk.list to 0.
complex_stack = """class ListNode [
    fields val, next
    method getNext() with locals:
        return &this.next
    method getVal() with locals:
        return &this.val
]
class Stack [
    fields list
    method push(v) with locals tmp:
        tmp = @ListNode
	!tmp.val = v
	!tmp.next = &this.list
	!this.list = tmp
	return 0
    method pop() with locals tmp, head:
        if (&this.list == 0): {
            return 0
        } else {
            head = &this.list
            tmp = ^head.getVal()
            !this.list = ^head.getNext()
            return tmp
        }
]
class Stacker [
    fields
    method do(stk) with locals x, v:
        x = 20
        while (x > 0): {
            _ = ^stk.push(x)
            x = (x - 1)
        }
        v = ^stk.pop()
        while (v != 0): {
            print(v)
            v = ^stk.pop()
        }
]

main with stk, stkr:
    stk = @Stack
    !stk.list = 0
    stkr = @Stacker
    _ = ^stkr.do(stk)
"""

# This code is a kind of *negative* test: value number should not do *anything* with the code for these methods!
# In general, they have code which could be recognized and optimized in some way (e.g., via code motion), but
# will not be be handled by global value numbering, because the definitions do not dominate the uses.
nothing = """class Foo [
    fields
    method doStuff(x,y,z) with locals r:
        if (x < y): {
            r = ((x + y) + z)
        } else {
            r = ((x + y) + z)
        }
        print(r)
        return ((x + y) + z)
]

main with:"""

# This code basically plays to the best-case scenario for global value numbering
# Because GVN will run on SSA form, the initial 4+5 computation should be reused for the later cases, even though it's overwritten at the source level.
optimal = """main with x, y, z:
    x = (4 + 5)
    x = 73
    y = (4 + 5)
    print(y)
    z = (4 + 5)
    print(z)
"""
def test_tokenize_peek():
    t = Tokenizer(optimal)
    tok = t.peek()
    tok2 = t.peek()
    assert tok.type == tok2.type and tok.lexeme == tok2.lexeme

def test_tokenize_cache():
    t = Tokenizer(first_example)

    start_time = time.perf_counter()
    t.tokenize()
    end_time = time.perf_counter()
    time1 = end_time - start_time

    start_time = time.perf_counter()
    t.tokenize()
    end_time = time.perf_counter()
    time2 = end_time - start_time

    assert time1 > time2


def test_parse_paren_expr():
    t1 = Tokenizer("(9 + 10)")
    t2 = Tokenizer("(this + (9 * 10))")
    t3 = Tokenizer("((111 - 17) / variable)")
    p1 = Parser(t1)
    p2 = Parser(t2)
    p3 = Parser(t3)

    tree = p1.parse_expr()
    assert isinstance(tree, ParenExpression) and tree.op == "+"
    assert isinstance(tree.left, NumExpression) and tree.left.num == 9
    assert isinstance(tree.right, NumExpression) and tree.right.num == 10

    tree = p2.parse_expr()
    # "this" is parsed as ThisExpression, not VarExpression
    assert isinstance(tree, ParenExpression) and tree.op == "+"
    assert isinstance(tree.left, ThisExpression)
    assert isinstance(tree.right, ParenExpression) and tree.right.op == "*"
    assert isinstance(tree.right.left, NumExpression) and tree.right.left.num == 9
    assert isinstance(tree.right.right, NumExpression) and tree.right.right.num == 10

    tree = p3.parse_expr()
    assert isinstance(tree, ParenExpression) and tree.op == "/"
    assert isinstance(tree.left, ParenExpression) and tree.left.op == "-"
    assert isinstance(tree.left.left, NumExpression) and tree.left.left.num == 111
    assert isinstance(tree.left.right, NumExpression) and tree.left.right.num == 17
    assert isinstance(tree.right, VarExpression) and tree.right.var_name == "variable"
    
def test_parse_method_expr():
    t1 = Tokenizer("^3.methodname()")
    t2 = Tokenizer("^h.y(8,(3*9),variablename)")
    t3 = Tokenizer("^^obj.x().l()")

    p1 = Parser(t1)
    p2 = Parser(t2)
    p3 = Parser(t3)

    tree = p1.parse_expr()
    assert isinstance(tree, MethodExpression) and tree.method_name == "methodname" and tree.args == []
    assert isinstance(tree.expr, NumExpression) and tree.expr.num == 3

    tree = p2.parse_expr()
    assert isinstance(tree, MethodExpression) and tree.method_name == "y" and len(tree.args) == 3 
    assert isinstance(tree.expr, (VarExpression))
    assert isinstance(tree.args[0], NumExpression) and tree.args[0].num == 8
    assert isinstance(tree.args[1], ParenExpression) and tree.args[1].op == "*"
    assert isinstance(tree.args[2], VarExpression) and tree.args[2].var_name == "variablename"

    tree = p3.parse_expr()
    assert isinstance(tree, MethodExpression) and tree.method_name == "l"
    assert isinstance(tree.expr, MethodExpression) and tree.expr.method_name == "x"
    assert isinstance(tree.expr.expr, VarExpression) and tree.expr.expr.var_name == "obj"

def test_parse_field_read_expr():
    t1 = Tokenizer("&e.a")
    t2 = Tokenizer("&(x / (3+4)).bar")
    t3 = Tokenizer("&&abc.def.ghi")

    p1 = Parser(t1)
    p2 = Parser(t2)
    p3 = Parser(t3)

    tree = p1.parse_expr()
    assert isinstance(tree, FieldReadExpression) and tree.field_name == "a"
    assert isinstance(tree.expr, VarExpression) and tree.expr.var_name == "e"

    tree = p2.parse_expr()
    assert isinstance(tree, FieldReadExpression) and tree.field_name == "bar"
    assert isinstance(tree.expr, ParenExpression) and tree.expr.op == "/"

    tree = p3.parse_expr()
    assert isinstance(tree, FieldReadExpression) and tree.field_name == "ghi"
    assert isinstance(tree.expr, FieldReadExpression) and tree.expr.field_name == "def"
    assert isinstance(tree.expr.expr, VarExpression) and tree.expr.expr.var_name == "abc"
    

def test_parse_class_instantiation_expr():
    t1 = Tokenizer("@CLASS")
    t2 = Tokenizer("@BAZ")

    p1 = Parser(t1)
    p2 = Parser(t2)

    tree = p1.parse_expr()
    assert isinstance(tree, NewObjExpression) and tree.class_name == "CLASS"

    tree = p2.parse_expr()
    assert isinstance(tree, NewObjExpression) and tree.class_name == "BAZ"

def test_parse_this_expr():
    tree = Parser(Tokenizer("this")).parse_expr()
    assert isinstance(tree, ThisExpression)

def test_parse_assignment_stmt():
    t1 = Tokenizer("x = 3")
    t2 = Tokenizer("y = (14 * 79)")
    t3 = Tokenizer("_ = ^z.f(3)")

    p1 = Parser(t1)
    p2 = Parser(t2)
    p3 = Parser(t3)

    tree = p1.parse_stmt()
    assert isinstance(tree, AssignVarStatement) and tree.var_name == "x"
    assert isinstance(tree.val, NumExpression) and tree.val.num == 3

    tree = p2.parse_stmt()
    assert isinstance(tree, AssignVarStatement) and tree.var_name == "y"
    assert isinstance(tree.val, ParenExpression) and tree.val.op == "*"

    tree = p3.parse_stmt()
    assert isinstance(tree, AssignVarStatement) and tree.var_name == "_"
    assert isinstance(tree.val, MethodExpression) and tree.val.method_name == "f" and len(tree.val.args) == 1
    assert isinstance(tree.val.args[0], NumExpression)
    assert isinstance(tree.val.expr, VarExpression)

def test_parse_field_update_stmt():
    t1 = Tokenizer("!x.y = 3")
    # is this allowed? if so should it be only for fields, like exprs can't be assigned bc we don't know if they come
    # from something which exists in scope or will be thrown away
    #t2 = Tokenizer("!&x.y.z = (14 * 79)")
    t3 = Tokenizer("!name.other = ^z.f(3)")

    p1 = Parser(t1)
    p3 = Parser(t3)

    tree = p1.parse_stmt()
    assert isinstance(tree, AssignFieldStatement) and tree.obj_expr.var_name == "x" and tree.field_name == "y"
    assert isinstance(tree.val, NumExpression) and tree.val.num == 3

    tree = p3.parse_stmt()
    assert isinstance(tree, AssignFieldStatement) and tree.obj_expr.var_name == "name" and tree.field_name == "other"
    assert isinstance(tree.val, MethodExpression) and tree.val.method_name == "f" and len(tree.val.args) == 1
    assert isinstance(tree.val.args[0], NumExpression) and tree.val.args[0].num == 3
    assert isinstance(tree.val.expr, VarExpression) and tree.val.expr.var_name == "z"

def test_parse_if_stmt():
    t1 = Tokenizer("""if hi:{
    x = 9
    _ = &f.y
    } else {
    !name.other = (14 + 20)
    }""")
    t2 = Tokenizer("""if ^four.five(): {
    x = 9
    } else {
    x = 10
    }""")
    t3 = Tokenizer("""if ^four.five(): {x = 9
    } else {
    x = 10
    }""")
    t4 = Tokenizer("""if ^four.five(): {
    x = 9
    } else {x = 10
    }""")

    p1 = Parser(t1)
    p2 = Parser(t2)
    p3 = Parser(t3)
    p4 = Parser(t4)

    tree = p1.parse_stmt()
    assert isinstance(tree, IfStatement) and len(tree.statements_true) == 2 and len(tree.statements_false) == 1
    assert isinstance(tree.condition, VarExpression) and tree.condition.var_name == "hi"
    assert isinstance(tree.statements_true[0], AssignVarStatement) and tree.statements_true[0].var_name == "x"
    assert isinstance(tree.statements_false[0], AssignFieldStatement) and tree.statements_false[0].obj_expr.var_name == "name" and tree.statements_false[0].field_name == "other"

    tree = p2.parse_stmt()
    assert isinstance(tree, IfStatement) and len(tree.statements_true) == 1 and len(tree.statements_false) == 1
    assert isinstance(tree.condition, MethodExpression) and tree.condition.method_name == "five"

    with pytest.raises(SyntaxError):
        tree = p3.parse_stmt()

    with pytest.raises(SyntaxError):
        tree = p4.parse_stmt()

def test_parse_if_only_stmt():
    t1 = Tokenizer("""ifonly c  :{
    _ = ^z.w()
    !f.t = (9 * 10)
    }""")
    t2 = Tokenizer("""ifonly ^four.five(): {
    x = 9
    }""")
    t3 = Tokenizer("""ifonly ^four.five(): {x = 9
    }""")
    p1 = Parser(t1)
    p2 = Parser(t2)
    p3 = Parser(t3)

    tree = p1.parse_stmt()
    assert isinstance(tree, IfOnlyStatement) and len(tree.statements) == 2
    assert isinstance(tree.statements[0], AssignVarStatement) and tree.statements[0].var_name == "_"
    assert isinstance(tree.condition, VarExpression) and tree.condition.var_name == "c"

    tree = p2.parse_stmt()
    assert isinstance(tree, IfOnlyStatement) and len(tree.statements) == 1
    assert isinstance(tree.condition, MethodExpression) and tree.condition.method_name == "five"

    with pytest.raises(SyntaxError):
        tree = p3.parse_stmt()


def test_while_stmt():
    t1 = Tokenizer("""while c  :{
    _ = ^z.w()
    !f.t = (9 * 10)
    }""")
    t2 = Tokenizer("""while ^four.five(): {
    x = 9
    }""")
    t3 = Tokenizer("""while ^four.five(): {x = 9
    }""")
    p1 = Parser(t1)
    p2 = Parser(t2)
    p3 = Parser(t3)

    tree = p1.parse_stmt()
    assert isinstance(tree, WhileStatement)
    assert isinstance(tree.condition, VarExpression) and tree.condition.var_name == "c"
    assert len(tree.statements) == 2
    assert isinstance(tree.statements[0], AssignVarStatement) and tree.statements[0].var_name == "_"

    tree = p2.parse_stmt()
    assert isinstance(tree, WhileStatement)
    assert isinstance(tree.condition, MethodExpression) and tree.condition.method_name == "five"
    assert len(tree.statements) == 1
    assert isinstance(tree.statements[0], AssignVarStatement) and tree.statements[0].var_name == "x"

    with pytest.raises(SyntaxError):
        tree = p3.parse_stmt()

def test_parse_return_stmt():
    t1 = Tokenizer("""return 0""")
    t2 = Tokenizer("""return (4*(7+9))""")
    p1 = Parser(t1)
    p2 = Parser(t2)

    tree = p1.parse_stmt()
    assert isinstance(tree, ReturnStatement)
    assert isinstance(tree.val, NumExpression) and tree.val.num == 0

    tree = p2.parse_stmt()
    assert isinstance(tree, ReturnStatement)
    assert isinstance(tree.val, ParenExpression) and tree.val.op == "*"


def test_parse_print_stmt():
    t1 = Tokenizer("""print(0)""")
    t2 = Tokenizer("""print((4*(7+9)))""")
    p1 = Parser(t1)
    p2 = Parser(t2)

    tree = p1.parse_stmt()
    assert isinstance(tree, PrintStatement)
    assert isinstance(tree.val, NumExpression) and tree.val.num == 0

    tree = p2.parse_stmt()
    assert isinstance(tree, PrintStatement)
    assert isinstance(tree.val, ParenExpression) and tree.val.op == "*"

def test_parse_method_declaration():
    t1 = Tokenizer("""method doStuff(s,t,uv) with locals r:
        if (x < y): {
            r = ((x + y) + z)
        } else {
            r = ((x + y) + z)
        }
        print(r)
        return ((x + y) + z)
        method""")
    t2 = Tokenizer("""method pop() with locals tmp:
        if (&this.list == 0): {
            return 0
        } else {
            tmp = ^this.getVal()
            !this.list = ^this.getNext()
            return tmp
        }
        ]""")
    t3 = Tokenizer("""    method pop() with locals tmp: if (&this.list == 0): {
            return 0
        } else {
            tmp = ^this.getVal()
            !this.list = ^this.getNext()
            return tmp
        }
        ]""")
    p1 = Parser(t1)
    p2 = Parser(t2)
    p3 = Parser(t3)

    tree = p1.parse_mthd()
    assert isinstance(tree, Method) and tree.method_name == "doStuff" and len(tree.statements) >= 3  

    tree = p2.parse_mthd()
    assert isinstance(tree, Method) and tree.method_name == "pop" and len(tree.statements) >= 1
    assert isinstance(tree.statements[0], IfStatement)

    with pytest.raises(SyntaxError):
        tree = p3.parse_mthd()


def test_parse_class_declaration():
    t1 = Tokenizer("""class Foo [
    fields x,y,z
        method doStuff(s,t,uv) with locals r:
        if (x < y): {
            r = ((x + y) + z)
        } else {
            r = ((x + y) + z)
        }
        print(r)
        return ((x + y) + z)
    method pop() with locals tmp:
        if (&this.list == 0): {
            return 0
        } else {
            tmp = ^this.getVal()
            !this.list = ^this.getNext()
            return tmp
        }
    ]""")
    t2 = Tokenizer("""class Foo [
    fields
    ]""")
    t3 = Tokenizer("""class Foo [ fields x,y,z
        method doStuff(s,t,uv) with locals r:
                if (x < y): {
                    r = ((x + y) + z)
                } else {
                    r = ((x + y) + z)
                }
                print(r)
                return ((x + y) + z)
            method pop() with locals tmp:
                if (&this.list == 0): {
                    return 0
                } else {
                    tmp = ^this.getVal()
                    !this.list = ^this.getNext()
                    return tmp
                }
        ]""")
    p1 = Parser(t1)
    p2 = Parser(t2)
    p3 = Parser(t3)

    tree = p1.parse_cls()
    assert isinstance(tree, Class) and tree.class_name == "Foo" and len(tree.fields) == 3
    assert all(isinstance(m, Method) for m in tree.methods) and len(tree.methods) == 2
    assert tree.methods[0].method_name == "doStuff" and tree.methods[1].method_name == "pop"

    tree = p2.parse_cls()
    assert isinstance(tree, Class) and tree.class_name == "Foo" and tree.fields == [] and len(tree.methods) == 0

    with pytest.raises(SyntaxError):
        tree = p3.parse_cls()


def test_parse_program_declaration():
    # get no errors from parsing for all of the example programs
    for prg in [nothing, optimal, first_example, simple_stack, complex_stack]:
        tree = Parser(Tokenizer(prg)).parse_program()
        assert isinstance(tree, Program) and isinstance(tree.classes, list) and isinstance(tree.local_vars, list) and isinstance(tree.statements, list)
    
    # better tests for a few of the example programs
    tree = Parser(Tokenizer(optimal)).parse_program()
    assert len(tree.classes) == 0 and len(tree.statements) >= 3  
    tree = Parser(Tokenizer(first_example)).parse_program()
    assert len(tree.classes) == 2 and tree.classes[0].class_name == "A" and tree.classes[1].class_name == "B"

    
def test_cfg_paren_exprs_and_assign():
    t1 = Tokenizer("""x = (5 / (3+4))""")
    p1 = Parser(t1)


    prog = IRProgram([],[],{},{})
    prog.add_block("foo")
    ast1 = p1.parse_stmt()
    ast1.to_ir(prog)

    stmts = prog.curr_block.statements
    assert len(stmts) == 2

    final_assign = stmts[-1]
    assert isinstance(final_assign, IRAssign)
    assert isinstance(final_assign.v, IRVar) and final_assign.v.reg == "x"
    assert isinstance(final_assign.val, IROperation) and final_assign.val.op == "/"
    assert isinstance(final_assign.val.r, IRVar) and final_assign.val.r.reg == "tmp0"
    assert isinstance(final_assign.val.l, IRConst) and final_assign.val.l.n == 5

def test_cfg_vtbls_and_fields():
    ast1 = Program([
        Class("foo",["x","y"],[Method("a",[],[],[AssignVarStatement("w",ParenExpression(NumExpression(2),"+",NumExpression(3)))])]),
        Class("bar",["y","x"],[Method("b",[],[],[AssignVarStatement("w",ParenExpression(NumExpression(2),"+",NumExpression(3)))]),Method("a",[],[],[AssignVarStatement("w",ParenExpression(NumExpression(2),"+",NumExpression(3)))])])
             ],
        [],[])

    ir1 = ast1.to_ir_program()

    v1 = ir1.vtbls[0]
    v2 = ir1.vtbls[1]
    assert isinstance(v1, IRArray) and v1.name == "vtblfoo" and len(v1.vals) == 2 and v1.vals[0]  == "fooa" and v1.vals[1] == 0
    assert isinstance(v2, IRArray) and v2.name == "vtblbar" and len(v2.vals) == 2 and v2.vals[0]  == "bara" and v2.vals[1] == "barb"

    f1 = ir1.field_maps[0]
    f2 = ir1.field_maps[1]
    assert isinstance(f1, IRArray) and f1.name == "fieldsfoo" and len(f1.vals) == 2 and f1.vals[0] == 2 and f1.vals[1] == 3
    assert isinstance(f2, IRArray) and f2.name == "fieldsbar" and len(f2.vals) == 2 and f2.vals[0] == 3 and f2.vals[1] == 2
    
def test_cfg_new_class():
    ast1 = Program([Class("x",["x"],[])],[],[AssignVarStatement("y",NewObjExpression("x"))])
    ast2 = Program([Class("cls",["fldone","fldtwo"],[])],[],[AssignVarStatement("var",ParenExpression(NumExpression(0),"+",NewObjExpression("cls")))])

    ir1 = ast1.to_ir_program()
    ir2 = ast2.to_ir_program()

    stmts = ir1.curr_block.statements
    assert len(stmts) == 5
    assert isinstance(stmts[0],IRAssign) and stmts[0].v.reg == "tmp0" and stmts[0].val.n == 3
    assert isinstance(stmts[1],IRStore) and stmts[1].base.reg == "tmp0" and stmts[1].i.name == "vtblx"
    assert isinstance(stmts[2],IRAssign) and stmts[2].v.reg == "tmp1" and stmts[2].val.l.reg == "tmp0" and stmts[2].val.r.n == 8
    assert isinstance(stmts[3],IRStore) and stmts[3].base.reg == "tmp1" and stmts[3].i.name == "fieldsx"
    assert isinstance(stmts[4], IRAssign) and stmts[4].v.reg == "y" and stmts[4].val.reg == "tmp0"

    stmts = ir2.curr_block.statements
    assert len(stmts) == 5 
    assert isinstance(stmts[0],IRAssign) and stmts[0].v.reg == "tmp0" and stmts[0].val.n == 4
    assert isinstance(stmts[1],IRStore) and stmts[1].base.reg == "tmp0" and stmts[1].i.name == "vtblcls"
    assert isinstance(stmts[2],IRAssign) and stmts[2].v.reg == "tmp1" and stmts[2].val.l.reg == "tmp0" and stmts[2].val.r.n == 8
    assert isinstance(stmts[3],IRStore) and stmts[3].base.reg == "tmp1" and stmts[3].i.name == "fieldscls"
    assert isinstance(stmts[4],IRAssign) and stmts[4].v.reg=="var" and stmts[4].val.l.n == 0 and stmts[4].val.r.reg == "tmp0"

def test_cfg_if_only():
    ast1 = Program([],[],[IfOnlyStatement(ParenExpression(NumExpression(2),"+",NumExpression(3)),[AssignVarStatement("y",NumExpression(1))])])
    ir1 = ast1.to_ir_program()

    assert len(ir1.blocks) == 3 #start block is the conditional, true block, after block
    before = ir1.blocks[0]
    true = ir1.blocks[1]
    after = ir1.blocks[2]
    assert len(before.statements) == 1 #assignment to tmp0

    assert isinstance(before.statements[0],IRAssign) and before.statements[0].v.reg == "tmp2" and before.statements[0].val.op == "+"
    assert isinstance(before.ctl_tsf,IRIf) and before.ctl_tsf.v.reg == "tmp2" and "true" in before.ctl_tsf.b_true.name and "after" in before.ctl_tsf.b_false.name
    assert len(true.statements) == 1
    assert isinstance(true.ctl_tsf,IRJump) and "after" in true.ctl_tsf.b_after.name
    assert len(after.statements) == 0

def test_cfg_if():
    ast1 = Program([],[],[IfStatement(VarExpression("x"),[AssignVarStatement("y",NumExpression(1))],[AssignVarStatement("z",NumExpression(2))])])
    ir1 = ast1.to_ir_program()

    assert len(ir1.blocks) == 4 #start block is the conditional, true block, false block, after block
    before = ir1.blocks[0]
    true = ir1.blocks[1]
    false = ir1.blocks[2]
    after = ir1.blocks[3]
    
    assert len(before.statements) == 0
    assert isinstance(before.ctl_tsf,IRIf) and "false" in before.ctl_tsf.b_false.name and "true" in before.ctl_tsf.b_true.name and before.ctl_tsf.v.reg == "x"
    assert len(true.statements) == 1
    assert isinstance(true.ctl_tsf,IRJump) and "after" in true.ctl_tsf.b_after.name
    assert len(false.statements) == 1
    assert isinstance(false.ctl_tsf,IRJump) and "after" in false.ctl_tsf.b_after.name
    assert len(after.statements) == 0

def test_cfg_print():
    ast1 = Program([],[],[PrintStatement(ParenExpression(NumExpression(8),"-",NumExpression(2)))])
    ast2 = Program([],[],[PrintStatement(VarExpression("var"))])

    ir1 = ast1.to_ir_program()
    ir2 = ast2.to_ir_program()

    stmts = ir1.curr_block.statements
    assert len(stmts) == 2
    assert isinstance(stmts[0],IRAssign) and stmts[0].val.op == "-"
    assert isinstance(stmts[1],IRPrint) and stmts[0].v.reg == "tmp0"

    stmts = ir2.curr_block.statements
    assert len(stmts) == 1
    assert isinstance(stmts[0],IRPrint) and stmts[0].v.reg == "var"

def test_cfg_while():
    ast1 = Program([Class("x",[],[])],[],[PrintStatement(NumExpression(9)),WhileStatement(NewObjExpression("x"),[PrintStatement(VarExpression("pickles")),PrintStatement(VarExpression("pickles"))]),PrintStatement(NumExpression(9)),PrintStatement(NumExpression(9)),PrintStatement(NumExpression(9))])

    ir1 = ast1.to_ir_program()
    assert len(ir1.blocks) == 4 #start block, check conditional block, true block, false block
    before = ir1.blocks[0]
    cond = ir1.blocks[1]
    true = ir1.blocks[2]
    false = ir1.blocks[3]
    
    assert len(before.statements) == 1
    assert isinstance(before.ctl_tsf,IRJump) and "cond" in before.ctl_tsf.b_after.name
    assert len(cond.statements) == 4
    assert isinstance(cond.ctl_tsf,IRIf) and "after" in cond.ctl_tsf.b_false.name and "true" in cond.ctl_tsf.b_true.name
    assert len(true.statements) == 2
    assert isinstance(true.ctl_tsf,IRJump) and "cond" in true.ctl_tsf.b_after.name
    assert len(false.statements) == 3

def test_cfg_return():
    ast1 = Program([],[],[ReturnStatement(NumExpression(9))])
    ir1 = ast1.to_ir_program()
    block = ir1.blocks[0]
    assert len(block.statements) == 0
    assert len(ir1.blocks) == 1
    assert isinstance(block.ctl_tsf, IRRet) and block.ctl_tsf.v.n == 9

    ast2 = Program([],[],[ReturnStatement(ParenExpression(NumExpression(2),"+",ParenExpression(NumExpression(3),"+",NumExpression(4))))])
    ir2 = ast2.to_ir_program()
    block = ir2.blocks[0]
    assert len(ir2.blocks) == 1
    stmts = block.statements
    assert isinstance(stmts[0],IRAssign) and stmts[0].v.reg == "tmp0" and stmts[0].val.op == "+"
    assert isinstance(stmts[1],IRAssign) and stmts[1].v.reg == "tmp1" and stmts[1].val.op == "+"
    assert isinstance(block.ctl_tsf,IRRet) and block.ctl_tsf.v.reg == "tmp1"

def test_cfg_this_expr():
    ast1 = Program([],[],[AssignVarStatement("x",ThisExpression())])
    ir1 = ast1.to_ir_program()
    block = ir1.blocks[0]
    stmt = block.statements[0]
    assert len(ir1.blocks) == 1
    assert isinstance(stmt, IRAssign) and stmt.v.reg == "x" and stmt.val.reg == "this"

def test_cfg_method_use():
    # ignore method statements bc we will test later for appropriate creation of methods, fake the creation of the vtbl and fields instead
    ast1 = Program([],[],[AssignVarStatement("z",NewObjExpression("x")),AssignVarStatement("y",MethodExpression(VarExpression("z"),"a",[NumExpression(1),NumExpression(2)]))])
    prog = IRProgram([IRArray(["xb","xa"],"vtblx")],[IRArray([],"fieldsx")],{},{"b":0,"a":1})

    ir1 = ast1.to_ir(prog)
    block = ir1.blocks[0]
    stmts = block.statements
    assert len(ir1.blocks) == 1
    assert len(stmts) == 8 

    #creating object
    assert isinstance(stmts[0],IRAssign) #tmp0
    assert isinstance(stmts[1],IRStore)
    assert isinstance(stmts[2],IRAssign) #tmp1
    assert isinstance(stmts[3],IRStore)
    assert isinstance(stmts[4],IRAssign) and stmts[4].val.reg == "tmp0" and stmts[4].v.reg =="z"

    #grab vtbl
    assert isinstance(stmts[5],IRAssign) and stmts[5].v.reg == "tmp2"
    load = stmts[5].val
    assert isinstance(load,IRLoad) and load.base.reg == "z" 

    #grab mthd
    assert isinstance(stmts[6],IRAssign)  and stmts[6].v.reg == "tmp3"
    get_mthd = stmts[6].val
    assert isinstance(get_mthd,IRGetELT) and get_mthd.base.reg == "tmp2" and get_mthd.i == 1 # bc we are calling the second method in the vtable

    #call mthd
    call = stmts[7].val
    assert isinstance(call,IRCall) and call.c.reg == "tmp3" and call.r.reg =="z" and len(call.args) == 2

    #Now onto a little more complicated version of above
    ast2 = Program([],[],[AssignVarStatement("z",MethodExpression(NewObjExpression("x"),"a",[NumExpression(1),ParenExpression(NumExpression(11),"+",NumExpression(2))]))])
    prog = IRProgram([IRArray(["xa","xb"],"vtblx")],[IRArray([],"fieldsx")],{},{"a":0,"b":1})

    ir2 = ast2.to_ir(prog)
    block = ir2.blocks[0]
    stmts = block.statements

    assert len(ir2.blocks) == 1
    assert len(stmts) == 8 

    #assigning paren arg to tmp0
    assert isinstance(stmts[0],IRAssign) and isinstance(stmts[0].val,IROperation) 

    #creating object
    assert isinstance(stmts[1],IRAssign) #tmp1
    assert isinstance(stmts[2],IRStore)
    assert isinstance(stmts[3],IRAssign) #tmp2
    assert isinstance(stmts[4],IRStore)

    #grab vtbl
    assert isinstance(stmts[5],IRAssign) and stmts[5].v.reg == "tmp3"
    load = stmts[5].val
    assert isinstance(load,IRLoad) and load.base.reg == "tmp1"

    #grab mthd
    assert isinstance(stmts[6],IRAssign)  and stmts[6].v.reg == "tmp4"
    get_mthd = stmts[6].val
    assert isinstance(get_mthd,IRGetELT) and get_mthd.base.reg == "tmp3" and get_mthd.i == 0 # bc we are calling the first method in the vtable

    #call mthd
    call = stmts[7].val
    assert isinstance(call,IRCall) and call.c.reg == "tmp4" and call.r.reg =="tmp1" and len(call.args) == 2


def test_cfg_field_access():
    ast1 = Program([],[],[PrintStatement(FieldReadExpression(NewObjExpression("x"),"a"))])
    prog = IRProgram([IRArray([],"vtblx")],[IRArray([2,3,4],"fieldsx")],{"foo":0,"a":1,"bar":2},{})
    ir1 = ast1.to_ir(prog)
    assert len(ir1.blocks) == 1
    stmts = ir1.blocks[0].statements
    assert len(stmts) == 9

    #creating object
    assert isinstance(stmts[0],IRAssign) #tmp0
    assert isinstance(stmts[1],IRStore)
    assert isinstance(stmts[2],IRAssign) #tmp1
    assert isinstance(stmts[3],IRStore)

    #point to fields
    assert isinstance(stmts[4],IRAssign) #tmp2
    op = stmts[4].val
    assert isinstance(op,IROperation) and op.l.reg == "tmp0" and op.r.n == 8

    #grab fields for this obj
    assert isinstance(stmts[5],IRAssign) #tmp3
    load = stmts[5].val
    assert isinstance(load,IRLoad) and load.base.reg == "tmp2"

    #grab field index for this field on this obj
    assert isinstance(stmts[6],IRAssign) #tmp4
    get_field_ind = stmts[6].val
    assert isinstance(get_field_ind,IRGetELT) and get_field_ind.base.reg == "tmp3" and get_field_ind.i == 1

    #grab field from field index
    assert isinstance(stmts[7],IRAssign) #tmp5
    get_field = stmts[7].val
    assert isinstance(get_field,IRGetELT) and get_field.base.reg == "tmp0" and get_field.i.reg == "tmp4"

    assert isinstance(stmts[8],IRPrint) and stmts[8].v.reg == "tmp5"

    
def test_cfg_field_assign():
    ast1 = Program([],[],[AssignFieldStatement(NewObjExpression("x"),"a",ParenExpression(NumExpression(5),"*",NumExpression(14)))])
    prog = IRProgram([IRArray([],"vtblx")],[IRArray([2,3,4],"fieldsx")],{"foo":0,"a":1,"bar":2},{})
    ir1 = ast1.to_ir(prog)
    assert len(ir1.blocks) == 1
    stmts = ir1.blocks[0].statements
    assert len(stmts) == 9

    #creating object
    assert isinstance(stmts[0],IRAssign) #tmp0
    assert isinstance(stmts[1],IRStore)
    assert isinstance(stmts[2],IRAssign) #tmp1
    assert isinstance(stmts[3],IRStore)

    #point to fields
    assert isinstance(stmts[4],IRAssign) #tmp2
    op = stmts[4].val
    assert isinstance(op,IROperation) and op.l.reg == "tmp0" and op.r.n == 8

    #grab fields for this obj
    assert isinstance(stmts[5],IRAssign) #tmp3
    load = stmts[5].val
    assert isinstance(load,IRLoad) and load.base.reg == "tmp2"

    #grab field index for this field on this obj
    assert isinstance(stmts[6],IRAssign) #tmp4
    get_field_ind = stmts[6].val
    assert isinstance(get_field_ind,IRGetELT) and get_field_ind.base.reg == "tmp3" and get_field_ind.i == 1

    #handle expression of assignment
    assert isinstance(stmts[7],IRAssign) #tmp5
    op = stmts[7].val
    assert isinstance(op,IROperation) and op.op == "*"

    assert isinstance(stmts[8],IRSetELT) and stmts[8].base.reg == "tmp0" and stmts[8].i.reg == "tmp4" and stmts[8].i2.reg == "tmp5"

def test_cfg_method_blocks():
    ast1 = Program([
        Class("hello",[],[
            Method("world",["a"],[],[
                PrintStatement(NumExpression(7)),
                PrintStatement(NumExpression(5))
                ])
            ]),
        Class("foo",[],[
            Method("bar",["a","b"],[],[
                PrintStatement(NumExpression(7)),
                ])
            ])],
        [],
        []
        )
    prog = ast1.to_ir_program()
    assert len(prog.blocks) == 3
    h = prog.blocks[0]
    assert len(h.statements) == 2 and h.name == "helloworld" and h.input_names == ["this","a"]
    f = prog.blocks[1]
    assert len(f.statements) == 1 and f.name == "foobar" and f.input_names == ["this","a","b"]
    m = prog.blocks[2]
    assert len(m.statements) == 0 and m.name == "main"


def test_ir_to_str():
    ast1 = Program([
        Class("hello",[],[
            Method("world",["a"],[],[
                PrintStatement(NumExpression(7)),
                PrintStatement(NumExpression(5))
                ])
            ]),
        Class("foo",[],[
            Method("bar",["a","b"],[],[
                PrintStatement(NumExpression(7)),
                ])
            ])],
        [],
        []
        )
    prog = ast1.to_ir_program()
    #print(prog)

    for prg in [nothing, optimal, first_example, simple_stack, complex_stack]:
        #print(prg)
        tree = Parser(Tokenizer(prg)).parse_program()
        #print(tree.to_ir_program())

def test_successor_predecessor():
    main = [IfStatement(NumExpression(1),
                        [
                            IfStatement(NumExpression(1),
                                        [
                                            PrintStatement(NumExpression(2))
                                        ],
                                        [
                                            PrintStatement(NumExpression(3))
                                        ])
                        ],
                        [
                            PrintStatement(NumExpression(4))
                        ]),
            PrintStatement(NumExpression(5))
            ]
    prog = Program([],[],main)
    ir = prog.to_ir_program()
    main = ir.blocks[0]
    t = main.ctl_tsf.b_true
    f = main.ctl_tsf.b_false

    t2 = t.ctl_tsf.b_true
    f2 = t.ctl_tsf.b_false

    after = f.ctl_tsf.b_after

    assert len(main.successors) == 2
    assert t in main.successors and f in main.successors and main in t.predecessors and main in f.predecessors
    assert len(after.predecessors) == 2

def test_dominators():
    a = IRBasicBlock("after",[],IRRet(0),[])
    t2 = IRBasicBlock("t2",[],IRJump(a),[])
    t = IRBasicBlock("t",[],IRJump(t2),[])
    af = IRBasicBlock("af",[],IRJump(a),[])
    ft = IRBasicBlock("ft",[],IRJump(af),[])
    ff = IRBasicBlock("ff",[],IRJump(af),[])
    f = IRBasicBlock("f",[],IRIf(IRVar("bye"),ft,ff),[])
    b=IRBasicBlock("before",[],IRIf(IRVar("hi"),t,f),[])
    
    prog = IRProgram([],[],dict(),dict(),[b,t,f,a,t2,ff,ft,af])
    doms = iterative_dom(prog)

    assert doms[b] == {b}
    assert doms[t] == {b,t}
    assert doms[t2] == {b,t,t2}
    assert doms[f] == {b,f}
    assert doms[ft] == {b,f,ft}
    assert doms[ff] == {b,f,ff}
    assert doms[af] == {b,f,af}
    assert doms[a] == {b,a}
    
def test_idom():
    a = IRBasicBlock("after",[],IRRet(0),[])
    t2 = IRBasicBlock("t2",[],IRJump(a),[])
    t = IRBasicBlock("t",[],IRJump(t2),[])
    af = IRBasicBlock("af",[],IRJump(a),[])
    ft = IRBasicBlock("ft",[],IRJump(af),[])
    ff = IRBasicBlock("ff",[],IRJump(af),[])
    f = IRBasicBlock("f",[],IRIf(IRVar("bye"),ft,ff),[])
    b=IRBasicBlock("before",[],IRIf(IRVar("hi"),t,f),[])
    
    prog = IRProgram([],[],dict(),dict(),[b,t,f,a,t2,ff,ft,af])
    i = idom(iterative_dom(prog))

    assert i[b] == None
    assert i[t] == b
    assert i[t2] == t
    assert i[f] == b
    assert i[ft] == f
    assert i[ff] == f
    assert i[af] == f
    assert i[a] == b

def test_df():
    a = IRBasicBlock("after",[],IRRet(0),[])
    t2 = IRBasicBlock("t2",[],IRJump(a),[])
    fboth = IRBasicBlock("fboth",[],IRRet(0),[])
    t = IRBasicBlock("t",[],IRIf(IRVar("bye"),t2,fboth),[])
    f = IRBasicBlock("f",[],IRIf(IRVar("bye"),a,fboth),[])
    b=IRBasicBlock("before",[],IRIf(IRVar("hi"),t,f),[])
    
    prog = IRProgram([],[],dict(),dict(),[a,t2,fboth,t,f,b])
    df = dom_frontier(prog)

    assert df[b] == set()
    assert df[t] == {a,fboth}
    assert df[f] == {a,fboth}
    assert df[fboth] == set()
    assert df[t2] == {a}
    assert df[a] == set()

def test_cfg_to_ssa():
    a = IRBasicBlock("after",[IRPrint(IRVar("b"))],IRRet(0),[])
    t2 = IRBasicBlock("t2",[IRAssign(IRVar("b"),IRConst(4)),IRPrint(IRVar("b"))],IRJump(a),[])
    fboth = IRBasicBlock("fboth",[IRPrint(IRVar("x"))],IRRet(0),[])
    t = IRBasicBlock("t",[IRAssign(IRVar("x"),IRConst(6)),IRPrint(IRVar("x"))],IRIf(IRVar("bye"),t2,fboth),[])
    f = IRBasicBlock("f",[IRAssign(IRVar("a"),IRConst(7)),IRAssign(IRVar("b"),IRVar("a")),IRPrint(IRVar("x")),IRPrint(IRVar("b"))],IRIf(IRVar("bye"),a,fboth),[])
    b=IRBasicBlock("before",[IRAssign(IRVar("x"),IRConst(5)),IRPrint(IRVar("x"))],IRIf(IRVar("hi"),t,f),[])

    prog = IRProgram([],[],dict(),dict(),[a,t2,fboth,t,f,b])
    mk_ssa(prog)
    print(prog)

    seen = set()
    for b in prog.blocks:
        for s in b.statements:
            if isinstance(s,IRAssign):
                assigned = s.v.reg
                assert assigned not in seen
                seen.add(assigned)
