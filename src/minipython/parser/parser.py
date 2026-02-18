from __future__ import annotations
from ..tokenizer.tokens import TokenType, OPERATORS
from .ast.expressions import Expression, FieldReadExpression, MethodExpression, NewObjExpression, NumExpression, ParenExpression, ThisExpression, VarExpression
from .ast.statements import Statement, AssignFieldStatement, AssignVarStatement, IfOnlyStatement, IfStatement, PrintStatement, ReturnStatement, WhileStatement
from .ast.method import Method
from .ast.astclass import Class
from .ast.program import Program

class Parser:
    def __init__(self,t:Tokenizer):
        self.t = t
        self.line_number = 1

    def get_next(self):
        if self.t.peek() is None:
            raise SyntaxError("Expected a token but got end of file")
        tok = self.t.get_next()
        if tok.type == TokenType.NEWLINE:
            self.line_number += 1
        return tok

    def parse(self,*typeset):
        ret = []
        for t in typeset:
            if t is Expression:
                expr = self.parse_expr()
                ret.append(expr)
            elif t is Statement:
                stmt = self.parse_stmt()
                ret.append(stmt)
            elif t is Method:
                mth = self.parse_mthd()
                ret.append(mth)
            elif t is Class:
                cls = self.parse_cls()
                ret.append(cls)
            else:
                tok = self.get_next()
                if type(t) is list:
                    if tok.type not in t:
                        self.parse_error(f"Expected a token of types: {t}, instead got {tok.lexeme} of type {tok.type}")
                else:
                    if tok.type != t:
                        self.parse_error(f"Expected a token of type: {t}, instead got {tok.lexeme} of type {tok.type}")
                ret.append(tok.lexeme)
        return ret

    def parse_until(self, until, *typeset, grab_trail = True):
        ret = []
        for _ in range(len(typeset)):
            ret.append([])
        stop = (lambda: self.t.peek().type in until) if type(until) is list else (lambda: self.t.peek().type == until)
        while not stop():
            parsed = self.parse(*typeset)
            for i in range(len(typeset)):
                ret[i].append(parsed[i])

        if grab_trail:
            self.parse(until)
        return ret

    def parse_error(self,explaination):
        raise SyntaxError(f"Syntax Error on line: {self.line_number}\n{explaination}")

    def parse_expr(self) -> Expression:
        tok = self.t.get_next()
        match tok.type:
            case TokenType.LPAREN:
                left, op, right, _ = self.parse(Expression,OPERATORS,Expression,TokenType.RPAREN)
                return ParenExpression(left,op,right)
            case TokenType.IDENTIFIER:
                return VarExpression(tok.lexeme)
            case TokenType.NUMBER:
                return NumExpression(tok.lexeme)
            case TokenType.CARET:
                e, _, method_name, _ = self.parse(Expression,TokenType.DOT,[TokenType.IDENTIFIER,TokenType.THIS],TokenType.LPAREN)
                args = []
                t = self.t.peek()
                if t.type != TokenType.RPAREN:
                    args.append(self.parse_expr())
                    while((t := self.t.get_next()).type == TokenType.COMMA):
                        args.append(self.parse_expr())
                    if t.type != TokenType.RPAREN:
                        raise SyntaxError("Invalid argument structure to method")
                else:
                    self.t.get_next()

                return MethodExpression(e,method_name,args)
            case TokenType.AMP:
                e, _, field_name = self.parse(Expression,TokenType.DOT,TokenType.IDENTIFIER)
                return FieldReadExpression(e,field_name)
            case TokenType.AT:
                cl = self.parse(TokenType.IDENTIFIER)[0]
                return NewObjExpression(cl)
            case TokenType.THIS:
                return ThisExpression()
        raise SyntaxError(f"{tok.type}: {tok.lexeme} cannot start an expression")

    def parse_stmt(self):
        def parse_conditional_block():
            expr, _, _, _, s, _ = self.parse(Expression,TokenType.COLON,TokenType.LCBRAC,TokenType.NEWLINE, Statement, TokenType.NEWLINE)
            ss, _ = self.parse_until(TokenType.RCBRAC,Statement,TokenType.NEWLINE)
            return expr,[s,*ss]

        tok = self.t.get_next()
        match tok.type:
            case TokenType.IDENTIFIER | TokenType.UNDER:
                _, expr = self.parse(TokenType.EQUAL,Expression)
                return AssignVarStatement(tok.lexeme,expr)
            case TokenType.EXCLAM:
                obj, _, field_name, _, expr = self.parse(Expression,TokenType.DOT,TokenType.IDENTIFIER,TokenType.EQUAL,Expression)
                return AssignFieldStatement(obj,field_name,expr)
            case TokenType.IF:
                expr, stmts_if = parse_conditional_block()
                _,_,_,s,_ = self.parse(TokenType.ELSE,TokenType.LCBRAC,TokenType.NEWLINE,Statement,TokenType.NEWLINE)
                ss, _ = self.parse_until(TokenType.RCBRAC,Statement,TokenType.NEWLINE)
                return IfStatement(expr,stmts_if,[s,*ss])
            case TokenType.IFONLY:
                return IfOnlyStatement(*parse_conditional_block())
            case TokenType.WHILE:
                return WhileStatement(*parse_conditional_block())
            case TokenType.RETURN:
                expr = self.parse_expr()
                return ReturnStatement(expr)
            case TokenType.PRINT:
                _, expr, _ = self.parse(TokenType.LPAREN,Expression,TokenType.RPAREN)
                return PrintStatement(expr)
        self.parse_error(f"Incorrect token for start of statement: {tok}")

    def parse_identifier_list(self):
        identifiers = []
        if self.t.peek().type == TokenType.IDENTIFIER:
            identifiers.append(self.parse(TokenType.IDENTIFIER)[0])
            while(self.t.peek().type == TokenType.COMMA):
                self.t.get_next()
                identifiers.append(self.parse(TokenType.IDENTIFIER)[0])
        return identifiers


    def parse_cls(self):
        _, ident, _, _, _ = self.parse(TokenType.CLASS,TokenType.IDENTIFIER,TokenType.LSBRAC,[TokenType.NEWLINE,TokenType.NEWLINES],TokenType.FIELDS)
        field_names = self.parse_identifier_list()
        self.parse([TokenType.NEWLINE,TokenType.NEWLINES])
        mths_nested = self.parse_until(TokenType.RSBRAC,Method)  # parse_until returns list-of-lists (even though we only have one nested list)
        methods = mths_nested[0]
        return Class(ident,field_names,methods)


    def parse_mthd(self):
        mth, ident, _ = self.parse(TokenType.METHOD,TokenType.IDENTIFIER,TokenType.LPAREN)
        arg_names = self.parse_identifier_list()
        _, _, _ = self.parse(TokenType.RPAREN,TokenType.WITH,TokenType.LOCALS)
        local_names = self.parse_identifier_list()
        _, _, s, _ = self.parse(TokenType.COLON,[TokenType.NEWLINE,TokenType.NEWLINES],Statement,[TokenType.NEWLINE,TokenType.NEWLINES])
        ss, _ = self.parse_until([TokenType.METHOD,TokenType.RSBRAC],Statement,[TokenType.NEWLINE,TokenType.NEWLINES],grab_trail=False)

        return Method(ident,arg_names,local_names,[s,*ss])

    def parse_program(self):
        cls = []
        if self.t.peek().type in [TokenType.NEWLINE,TokenType.NEWLINES]:
            self.parse([TokenType.NEWLINE,TokenType.NEWLINES])
        if self.t.peek().type != TokenType.MAIN:
            cls, _ = self.parse_until(TokenType.MAIN,Class,[TokenType.NEWLINE,TokenType.NEWLINES],grab_trail=False)
        self.parse(TokenType.MAIN,TokenType.WITH)
        locs = self.parse_identifier_list()
        _ = self.parse(TokenType.COLON)

        stmts=[]
        while self.t.peek() is not None:
            nl = self.t.get_next()
            if nl.type not in {TokenType.NEWLINE,TokenType.NEWLINES}:
                self.parse_error("No newlines between statements in program entry point (main)")
            if self.t.peek() is None:
                break
            
            stmt = self.parse_stmt()
            stmts.append(stmt)
        return Program(cls,locs,stmts)

