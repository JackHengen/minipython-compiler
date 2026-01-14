import argparse
# objgraph

class Tokenizer:
    def __init__(self,s:str):
        self.s = s

    def get_next():
        pass

    def tokenize(): # grabs all tokens but don't increment tokenizer position in get_next, good if we want to grab all
                    # the tokens for something and then use something which uses the next api so we don't have to manage
                    # the counter in that thing
        pass

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
    args = parser.parse_args()
    print(args)

    if args.file:
        with open(args.file) as f:
            inp = f.read()
    elif args.str:
        inp = args.str

    stages = ["tokenize","parse","ast","cfg"]
    stage = float("inf") #by default we go to last stage
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

