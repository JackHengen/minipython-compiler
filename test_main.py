from main import Tokenizer, Parser
import time

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
    stk.push(1)
    stk.push(3)
    stk.push(5)
    stk.push(9)
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
            stk.push(x)
            x = (x - 1)
        }
        v = ^stk.pop()
        while (v != 0): {
            print(v)
            v = ^stk.pop()
        }

main with stk, stkr:
    stk = @Stack
    !stk.list = 0
    stkr = @Stacker
    _ = ^stkr.do(stk)"""

# This code is a kind of *negative* test: value number should not do *anything* with the code for these methods!
# In general, they have code which could be recognized and optimized in some way (e.g., via code motion), but
# will not be be handled by global value numbering, because the definitions do not dominate the uses.
nothing = """
class Foo [
    fields
    method doStuff(x,y,z) with locals r:
        if (x < y) {
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
    assert tok.type == tok2.type
    assert tok.lexeme == tok2.lexeme
    print(tok,tok2)

def test_tokenize():
    t = Tokenizer(first_example)
    print(t.tokenize())


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

    print(f"time1: {time1}, time2: {time2}")
    assert time1 > time2


def test_parse_paren_expr():
    t1 = Tokenizer("(9 + 10)")
    t2 = Tokenizer("(this + (9 * 10))")
    t3 = Tokenizer("((111 - 17) / variable)")
    
    p1 = Parser(t1)
    p2 = Parser(t2)
    p3 = Parser(t3)

    tree = p1.parse_expr()
    print(tree)
    tree = p2.parse_expr()
    print(tree)
    tree = p3.parse_expr()
    print(tree)
    
def test_parse_method_expr():
    t1 = Tokenizer("^3.methodname()")
    t2 = Tokenizer("^h.y(8,(3*9),variablename)")
    t3 = Tokenizer("^^obj.x().l()")

    p1 = Parser(t1)
    p2 = Parser(t2)
    p3 = Parser(t3)

    tree = p1.parse_expr()
    print(tree)
    tree = p2.parse_expr()
    print(tree)
    tree = p3.parse_expr()
    print(tree)

def test_parse_field_read_expr():
    t1 = Tokenizer("&e.a")
    t2 = Tokenizer("&(x / (3+4)).bar")
    t3 = Tokenizer("&&abc.def.ghi")

    p1 = Parser(t1)
    p2 = Parser(t2)
    p3 = Parser(t3)

    tree = p1.parse_expr()
    print(tree)
    tree = p2.parse_expr()
    print(tree)
    tree = p3.parse_expr()
    print(tree)
    

def test_parse_class_instantiation_expr():
    t1 = Tokenizer("@CLASS")
    t2 = Tokenizer("@BAZ")

    p1 = Parser(t1)
    p2 = Parser(t2)

    tree = p1.parse_expr()
    print(tree)
    tree = p2.parse_expr()
    print(tree)

def test_parse_this_expr():
    tree = Parser(Tokenizer("this")).parse_expr()
    print(tree)

def test_parse_assignment_stmt():
    t1 = Tokenizer("x = 3")
    t2 = Tokenizer("y = (14 * 79)")
    t3 = Tokenizer("_ = ^z.f(3)")

    p1 = Parser(t1)
    p2 = Parser(t2)
    p3 = Parser(t3)

    tree = p1.parse_stmt()
    print(tree)
    tree = p2.parse_stmt()
    print(tree)
    tree = p3.parse_stmt()
    print(tree)

def test_parse_field_update_stmt():
    t1 = Tokenizer("!x.y = 3")
    # is this allowed? if so should it be only for fields, like exprs can't be assigned bc we don't know if they come
    # from something which exists in scope or will be thrown away
    #t2 = Tokenizer("!&x.y.z = (14 * 79)")
    t3 = Tokenizer("!name.other = ^z.f(3)")

    p1 = Parser(t1)
    p3 = Parser(t3)

    tree = p1.parse_stmt()
    print(tree)
    tree = p3.parse_stmt()
    print(tree)

#TODO include newline formatting
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

    p1 = Parser(t1)
    p2 = Parser(t2)

    tree = p1.parse_stmt()
    print(tree)
    tree = p2.parse_stmt()
    print(tree)

#TODO include newline formatting
def test_parse_if_only_stmt():
    pass

#TODO include newline formatting
def test_while_stmt():
    pass

def test_parse_return_stmt():
    pass

def test_parse_print_stmt():
    pass

#TODO include newline formatting
def test_parse_class_declaration():
    pass

#TODO include newline formatting
def test_parse_method_declaration():
    pass

#TODO include newline formatting
def test_parse_program_declaration():
    pass
