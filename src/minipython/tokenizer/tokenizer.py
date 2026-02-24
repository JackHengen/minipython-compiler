from __future__ import annotations
from .tokens import Token,TokenType

class Tokenizer:
    def __init__(self,s:str):
        self.s = s # modified as we tokenize the string
        self.pos = 0 # position in tokens if we tokenized all in one go and are now walking through stored tokens 
        self.toks = []

        self.index = 0
        self.line = 1 # how many lines down in input
        self.col = 0 # how many columns into line

    def advance(self):
        c = self.s[self.index]
        self.index += 1

        if c == "\n":
            self.line += 1
            self.col = 0
        else:
            self.col += 1

        return c

    def reset(self):
        self.pos = 0
        self.line = 0
        self.col = 0
        self.index = 0

    def peek(self) -> Token:
        tok = self.get_next()
        self.pos -= 1
        return tok

    def get_next(self) -> Token:
        if len(self.toks) > self.pos: # TODO set line and col to that stored in the token
            tok = self.toks[self.pos]
            self.pos += 1
            return tok

        while(self.index < len(self.s) and (c := self.advance()) in ["\t"," "]):
            pass

        if self.index >= len(self.s):
            return None

        tok = None
        s = c
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
            if self.s[self.index] == "=":
                s += self.advance()
                tok = Token(TokenType.NEQUAL,s)
            else:
                tok = Token(TokenType.EXCLAM, s)
        if c == "+":
            tok = Token(TokenType.PLUS, "+")
        if c == "-":
            tok = Token(TokenType.MINUS, "-")
        if c == "*":
            tok = Token(TokenType.ASTER, "*")
        if c == "/":
            tok = Token(TokenType.SLASH, "/")
        if c == "<":
            tok = Token(TokenType.LABRAC, "<")
        if c == ">":
            tok = Token(TokenType.RABRAC, ">")
        if c == "=":
            if self.s[self.index] == "=":
                s += self.advance()
                tok = Token(TokenType.DEQUAL,s)
            else:
                tok = Token(TokenType.EQUAL,s)
        if c == "_":
            tok = Token(TokenType.UNDER, "_")
        if c.isdigit():
            while self.index < len(self.s) and (c:= self.s[self.index]).isdigit():
                s += str(self.advance())
            tok = Token(TokenType.NUMBER,s)

        if c.isalpha():
            while self.index < len(self.s) and (c := self.s[self.index]).isalpha():
                s += self.advance()

            if s[0].isupper() or s == "int":
                tok = Token(TokenType.TYPE,s)
            else:
                tok = Token(TokenType.IDENTIFIER,s)
        if s == "if":
            tok = Token(TokenType.IF,s)
        if s == "else":
            tok = Token(TokenType.ELSE,s)
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
        if s == "main":
            tok = Token(TokenType.MAIN,s)
        if s == "returning":
            tok = Token(TokenType.RETURNING,s)
        if s == "null":
            tok = Token(TokenType.NULL,s)

        if s == "\n":
            while self.index < len(self.s) and (self.s[self.index]) in ["\t"," "]:
                s += self.advance()
            if self.index >= len(self.s) or self.s[self.index] != "\n":
                tok = Token(TokenType.NEWLINE,"\n")
            else:
                while self.index < len(self.s) and (self.s[self.index]) in ["\t"," "]:
                    s += self.advance()
                while self.index < len(self.s) and (self.s[self.index]) == "\n":
                    s += self.advance()
                    while self.index < len(self.s) and (c := self.s[self.index]) in ["\t"," "]:
                        s += self.advance()
                tok = Token(TokenType.NEWLINES,s)

        if tok is None:
            raise ValueError(f"Inappropriate symbol {c}")
        else:
            self.pos +=1 # global token position
            self.toks.append(tok)
            return tok


    def tokenize(self):
        while(self.get_next()):
            pass
        self.pos = 0
        return self.toks
