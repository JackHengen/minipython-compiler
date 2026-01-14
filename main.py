import argparse
from enum import Enum
from abc import ABC
import time
# objgraph

class TokenType(Enum):
    LPAREN = 0
    RPAREN = 1
    LSBRAC = 2
    RSBRAC = 3
    LCBRAC = 4
    RCBRAC = 5
    CARET = 6
    DOT = 7
    COMMA = 8
    COLON = 9
    AMP = 10
    AT = 11
    EXCLAM = 12
    PLUS = 13
    MINUS = 14
    ASTER = 15
    SLASH = 16
    EQUAL = 17
    IF = 18
    IFONLY = 19
    WHILE = 20
    RETURN = 21
    PRINT = 22
    THIS = 23
    CLASS = 24
    WITH = 25
    LOCALS = 26
    FIELDS = 27
    METHOD = 28
    DIGIT = 29
    IDENTIFIER = 30



class Token():
    def __init__(self,typ:TokenType,lexeme:str):
        self.type = typ
        self.lexeme = lexeme
    def __repr__(self):
        return str((self.type,self.lexeme))


class Tokenizer:
    def __init__(self,s:str):
        self.s = s
        self.pos = 0
        self.toks = []

    def get_next(self) -> Token:
        if len(self.toks) > self.pos:
            tok = self.toks[self.pos]
            self.pos += 1
            return tok

        while(self.pos < len(self.s) and (c := self.s[self.pos]).isspace()):
            self.pos += 1
        self.pos += 1

        if self.pos >= len(self.s):
            return None

        tok = None
        if c == "(":
            tok = Token(TokenType.LPAREN, "(")
        if c == ")":
            tok = Token(TokenType.RPAREN, ")")
        if c == "[":
            tok = Token(TokenType.LSBRAC, "[")
        if c == "]":
            tok = Token(TokenType.RSBRAC, "]")
        if c == "{":
            tok = Token(TokenType.LCBRAC, "{")
        if c == "}":
            tok = Token(TokenType.RCBRAC, "}")
        if c == "^":
            tok = Token(TokenType.CARET, "^")
        if c == ".":
            tok = Token(TokenType.DOT, ".")
        if c == ",":
            tok = Token(TokenType.COMMA, ",")
        if c == ":":
            tok = Token(TokenType.COLON, ":")
        if c == "&":
            tok = Token(TokenType.AMP, "&")
        if c == "@":
            tok = Token(TokenType.AT, "@")
        if c == "!":
            tok = Token(TokenType.EXCLAM, "!")
        if c == "+":
            tok = Token(TokenType.PLUS, "+")
        if c == "-":
            tok = Token(TokenType.MINUS, "-")
        if c == "*":
            tok = Token(TokenType.ASTER, "*")
        if c == "/":
            tok = Token(TokenType.SLASH, "/")
        if c == "=":
            tok = Token(TokenType.EQUAL, "=")

        s = str(c)
        if c.isdigit():
            while self.pos < len(self.s) and (c:= self.s[self.pos]).isdigit():
                s += str(c)
                self.pos += 1
            tok = Token(TokenType.DIGIT,s)

        if c.isalpha():
            while self.pos < len(self.s) and (c := self.s[self.pos]).isalpha():
                s += c
                self.pos += 1
            tok = Token(TokenType.IDENTIFIER,s)
        if s == "if":
            tok = Token(TokenType.IF,s)
        if s == "ifonly":
            tok = Token(TokenType.IFONLY,s)
        if s == "while":
            tok = Token(TokenType.WHILE,s)
        if s == "return":
            tok = Token(TokenType.RETURN,s)
        if s == "print":
            tok = Token(TokenType.PRINT,s)
        if s == "this":
            tok = Token(TokenType.THIS,s)
        if s == "class":
            tok = Token(TokenType.CLASS,s)
        if s == "with":
            tok = Token(TokenType.WITH,s)
        if s == "locals":
            tok = Token(TokenType.LOCALS,s)
        if s == "fields":
            tok = Token(TokenType.FIELDS,s)
        if s == "method":
            tok = Token(TokenType.METHOD,s)


        if tok is None:
            raise ValueError(f"Inappropriate symbol {c}")
        else:
            return tok


    def tokenize(self):
        while(tok := self.get_next()) is not None:
            self.toks.append(tok)
        return self.toks

class Parser:
    def __init__(self,t:Tokenizer):
        self.t = t

    def parse_expr():
        pass

    def parse_statement():
        pass

    def parse_class():
        pass

    def parse_program():
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="MiniPython Compiler")
    input_group = parser.add_mutually_exclusive_group(required=True)

    input_group.add_argument("-f","--file")
    input_group.add_argument("-s","--str","--string")

    stage_group = parser.add_mutually_exclusive_group()
    stage_group.add_argument("-t","--tokenize")
    stage_group.add_argument("-p","--parse")
    stage_group.add_argument("-a","--ast")
    stage_group.add_argument("-c","--cfg","--noopt")
    stage_group.add_argument("-o","--opt","--optimize","--optimization")
    args = parser.parse_args()

    if args.file:
        with open(args.file) as f:
            inp = f.read()
    elif args.str:
        inp = args.str

    stages = ["tokenize","parse","ast","cfg","opt"]
    stage = float("inf")  # by default we go to last stage
    for i,val in enumerate(stages):
        if val in args:
            stage=i
            break

    if stage >= 0:
        t = Tokenizer(inp)
        if args.tokenize:
            toks = t.tokenize()
            print(toks)

    if stage >= 1:
        p = Parser(t)
        parse_tree = p.parse_program()
        if args.parse:
            # use objgraph
            pass
