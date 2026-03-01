from minipython.ir.array import *
from minipython.ir.basic_block import *
from minipython.ir.control_transfer import *
from minipython.ir.expressions import *
from minipython.ir.phi import *
from minipython.ir.program import *
from minipython.ir.statements import *
from minipython.optimizations.optimizations import *
from minipython.parser.ast.ast_node import *
from minipython.parser.ast.astclass import *
from minipython.parser.ast.expressions import *
from minipython.parser.ast.method import *
from minipython.parser.ast.program import *
from minipython.parser.ast.statements import *
from minipython.parser.parser import *
from minipython.tokenizer.tokens import *
from minipython.tokenizer.tokenizer import *
import pytest

def test_newobjexpr_type():
    expr = NewObjExpression("Object")
    assert expr.get_type({},{"Object":Class("Object",{},{})}) == "Object"

def test_varexpr_type():
    klass = Class("Klass",{},{})
    var1 = VarExpression("i")
    var2 = VarExpression("c")
    classes = {"Klass":klass}
    var_map = {"i":"int","c":"Klass"}
    assert var1.get_type(var_map,classes) == "int"
    assert var2.get_type(var_map,classes) == "Klass"

def test_constexpr_type():
    c = NumExpression(6)
    assert c.get_type({},{}) == "int"

def test_nullexpr_type():
    n = NullExpression("Klass")
    klass = Class("Klass",{},{})
    classes = {"Klass":klass}
    assert n.get_type({},classes) == "Klass"

def test_parenexpr_types():
    par1 = ParenExpression(NumExpression(9),"+",NumExpression(6))
    par2 = ParenExpression(VarExpression("c"),"+",VarExpression("c"))
    klass = Class("Klass",{},{})
    classes = {"Klass":klass}
    var_map = {"c":"Klass"}

    assert par1.get_type({},{}) == "int"
    with pytest.raises(Exception):
        par2.get_type(var_map,classes)

def test_methodexpr_type():
    klass1 = Class("Klassone", {"a":"int","b":"Klassone"},{"meth":Method("meth",{},{},[],"Klassone")})
    klass2 = Class("Klasstwo", {"a":"int","b":"Klasstwo"},{"meth":Method("meth",{},{},[],"int")})
    classes = {"Klassone":klass1,"Klasstwo":klass2}
    var_map = {"kone":"Klassone","ktwo":"Klasstwo"}

    expr1 = MethodExpression(MethodExpression(VarExpression("kone"),"meth",[]),"meth",[])
    expr2 = MethodExpression(VarExpression("ktwo"),"meth",[])

    assert expr1.get_type(var_map,classes) == "Klassone"
    assert expr2.get_type(var_map,classes) == "int"

def test_fieldreadexpr_type():
    klass1 = Class("Klassone", {"a":"int","b":"Klassone"},{"meth":Method("meth",{},{},[],"Klassone")})
    classes = {"Klassone":klass1}
    var_map = {"kone":"Klassone"}

    expr1 = FieldReadExpression(VarExpression("kone"),"a")
    expr2 = FieldReadExpression(MethodExpression(VarExpression("kone"),"meth",[]),"b")

    assert expr1.get_type(var_map,classes) == "int"
    assert expr2.get_type(var_map,classes) == "Klassone"

def test_thisexpr_type():
    klass1 = Class("Klassone",{},{})
    classes = {"Klassone":klass1}
    var_map = {"this":"Klassone"}

    expr1 = ThisExpression()
    
    assert expr1.get_type(var_map,classes) == "Klassone"

def test_assignvar_valid():
    klass1 = Class("Klassone", {"a":"int","b":"Klassone"},{"meth":Method("meth",{},{},[],"Klassone")})
    classes = {"Klassone":klass1}
    var_map = {"x":"Klassone","y":"int","hello":"int"}

    meth = MethodExpression(VarExpression("x"),"meth",[])
    expr1 = AssignVarStatement("x",meth)

    expr2 = AssignVarStatement("x",NewObjExpression("Klassone"))
    expr3 = AssignVarStatement("y",VarExpression("hello"))
    expr4 = AssignVarStatement("hello",NumExpression(6))

    expr5 = AssignVarStatement("y",VarExpression("x"))

    assert expr1.validate_types(var_map,classes,"Main","main")
    assert expr2.validate_types(var_map,classes,"Klassone","meth")
    assert expr3.validate_types(var_map,classes,"Klassone","meth")
    assert expr4.validate_types(var_map,classes,"Main","main")

    with pytest.raises(Exception):
        expr5.validate_types(var_map,classes,"Main","main")
    

def test_assignfield_valid():
    klass1 = Class("Klassone", {"a":"int","b":"Klassone"},{"meth":Method("meth",{},{},[],"Klassone")})
    classes = {"Klassone":klass1}
    var_map = {"x":"Klassone","y":"int","hello":"int"}

    expr1 = AssignFieldStatement(VarExpression("x"),"a",VarExpression("y"))
    expr2 = AssignFieldStatement(NewObjExpression("Klassone"),"a",VarExpression("x"))
    expr2 = AssignFieldStatement(NewObjExpression("Klassone"),"a",VarExpression("hello"))

    assert expr1.validate_types(var_map,classes,"Main","main")
    assert expr2.validate_types(var_map,classes,"Main","main")

    with pytest.raises(Exception):
        expr3.validate_types(var_map,classes,"Main","main")

def test_if_valid():
    klass1 = Class("Klassone", {"a":"int","b":"Klassone"},{"meth":Method("meth",{},{},[],"Klassone")})
    classes = {"Klassone":klass1}
    var_map = {"x":"Klassone","y":"int","hello":"int"}
    expr1 = IfStatement(VarExpression("hello"),[AssignVarStatement("hello",NumExpression(0))],[AssignVarStatement("hello",NumExpression(0))])
    expr2 = IfStatement(NumExpression(1),[AssignVarStatement("hello",NumExpression(0))],[AssignVarStatement("hello",NumExpression(0))])
    
    # fail bc assignment inside true side fails
    expr3 = IfStatement(NumExpression(1),[AssignVarStatement("x",NumExpression(0))],[AssignVarStatement("hello",NumExpression(0))])

    # fail bc not an int conditional
    expr4 = IfStatement(VarExpression("x"),[AssignVarStatement("hello",NumExpression(0))],[AssignVarStatement("hello",NumExpression(0))])
    
    assert expr1.validate_types(var_map,classes,"Main","main")
    assert expr2.validate_types(var_map,classes,"Main","main")

    with pytest.raises(Exception):
        assert expr3.validate_types(var_map,classes,"Main","main")

    with pytest.raises(Exception):
        assert expr4.validate_types(var_map,classes,"Main","main")

def test_ifonly_valid():
    klass1 = Class("Klassone", {"a":"int","b":"Klassone"},{"meth":Method("meth",{},{},[],"Klassone")})
    classes = {"Klassone":klass1}
    var_map = {"x":"Klassone","y":"int","hello":"int"}
    expr1 = IfOnlyStatement(VarExpression("hello"),[AssignVarStatement("hello",NumExpression(0))])
    expr2 = IfOnlyStatement(NumExpression(1),[AssignVarStatement("hello",NumExpression(0))])
    
    # fail bc assignment inside true side fails
    expr3 = IfOnlyStatement(NumExpression(1),[AssignVarStatement("x",NumExpression(0))])

    # fail bc not an int conditional
    expr4 = IfOnlyStatement(VarExpression("x"),[AssignVarStatement("hello",NumExpression(0))])
    
    assert expr1.validate_types(var_map,classes,"Main","main")
    assert expr2.validate_types(var_map,classes,"Main","main")

    with pytest.raises(Exception):
        assert expr3.validate_types(var_map,classes,"Main","main")

    with pytest.raises(Exception):
        assert expr4.validate_types(var_map,classes,"Main","main")

def test_while_valid():
    klass1 = Class("Klassone", {"a":"int","b":"Klassone"},{"meth":Method("meth",{},{},[],"Klassone")})
    classes = {"Klassone":klass1}
    var_map = {"x":"Klassone","y":"int","hello":"int"}
    expr1 = WhileStatement(VarExpression("hello"),[AssignVarStatement("hello",NumExpression(0))])
    expr2 = WhileStatement(NumExpression(1),[AssignVarStatement("hello",NumExpression(0))])
    
    # fail bc assignment inside true side fails
    expr3 = WhileStatement(NumExpression(1),[AssignVarStatement("x",NumExpression(0))])

    # fail bc not an int conditional
    expr4 = WhileStatement(VarExpression("x"),[AssignVarStatement("hello",NumExpression(0))])
    
    assert expr1.validate_types(var_map,classes,"Main","main")
    assert expr2.validate_types(var_map,classes,"Main","main")

    with pytest.raises(Exception):
        assert expr3.validate_types(var_map,classes,"Main","main")

    with pytest.raises(Exception):
        assert expr4.validate_types(var_map,classes,"Main","main")

def test_print_valid():
    klass1 = Class("Klassone", {"a":"int","b":"Klassone"},{"meth":Method("meth",{},{},[],"Klassone")})
    classes = {"Klassone":klass1}
    var_map = {"x":"Klassone","y":"int","hello":"int"}

    expr1 = PrintStatement(VarExpression("y"))
    expr2 = PrintStatement(NumExpression(3))
    expr3 = PrintStatement(VarExpression("x"))

    assert expr1.validate_types(var_map,classes,"Main","main")
    assert expr2.validate_types(var_map,classes,"Main","main")

    with pytest.raises(Exception):
        assert expr3.validate_types(var_map,classes,"Main","main")
                        


def test_return_statement():
    m = Method("methone",{},{},[],"Klassone")
    klass1 = Class("Klassone",{"a":"int","b":"Klassone"},{"methone":m})
    classes = {"Klassone":klass1}
    var_map = {"x":"Klassone","y":"int","hello":"int"}
    
    expr1 = ReturnStatement(NumExpression(8))
    expr2 = ReturnStatement(NewObjExpression("Klassone"))
    expr3 = ReturnStatement(VarExpression("y"))
    expr4 = ReturnStatement(VarExpression("x"))

    assert expr1.validate_types(var_map,classes,"Main","main")
    assert expr2.validate_types(var_map,classes,klass1,m)
    assert expr3.validate_types(var_map,classes,"Main","main")
    assert expr4.validate_types(var_map,classes,klass1,m)

    with pytest.raises(Exception):
        expr1.validate_types(var_map,classes,klass1,m)
    with pytest.raises(Exception):
        expr2.validate_types(var_map,classes,"Main","main")
    with pytest.raises(Exception):
        expr3.validate_types(var_map,classes,klass1,m)
    with pytest.raises(Exception):
        expr4.validate_types(var_map,classes,"Main","main")

