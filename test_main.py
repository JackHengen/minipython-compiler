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
    method pop() with locals tmp:
        if (&this.list == 0): {
            return 0
        } else {
            tmp = ^this.getVal()
            !this.list = ^this.getNext()
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
    method pop() with locals tmp:
        if (&this.list == 0): {
            return 0
        } else {
            tmp = ^this.getVal()
            !this.list = ^this.getNext()
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
    _ = ^stkr.do(stk)"""

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
    assert isinstance(tree, AssignFieldStatement) and tree.class_name == "x" and tree.field_name == "y"
    assert isinstance(tree.val, NumExpression) and tree.val.num == 3

    tree = p3.parse_stmt()
    assert isinstance(tree, AssignFieldStatement) and tree.class_name == "name" and tree.field_name == "other"
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
    assert isinstance(tree.statements_false[0], AssignFieldStatement) and tree.statements_false[0].class_name == "name" and tree.statements_false[0].field_name == "other"

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

def test_cfg_of_paren_exprs_and_assign():
    snippet = """x = (5 / (3+4))"""
    t1 = Tokenizer(snippet)
    p1 = Parser(t1)

    ast = p1.parse_stmt()
    prog = IRProgram([],[],{})
    prog.add_block("foo")
    ast.to_ir(prog)
    stmts = prog.curr_block.statements
    print(stmts)
    assert len(stmts) == 2

    final_assign = stmts[-1]
    assert isinstance(final_assign, IRAssign)
    assert isinstance(final_assign.v, IRVar) and final_assign.v.reg == "x"
    assert isinstance(final_assign.val, IROperation) and final_assign.val.op == "/"
    assert isinstance(final_assign.val.r, IRVar) and final_assign.val.r.reg == "tmp0"
    assert isinstance(final_assign.val.l, IRConst) and final_assign.val.l.n == 5

