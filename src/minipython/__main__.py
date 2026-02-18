import argparse
import sys
from .parser.parser import Parser
from .tokenizer.tokenizer import Tokenizer
from .optimizations.optimzations import lvn, mk_ssa, pre_eval_opt




#TODO

# if vars come from some paths but not others check that

# refactor mk_ssa

# change order of args in IRPROG

# validate things like never ending loops

# validate early returns and still more statements

# validate operators once i find out which are permitted according to the ir

# should we be validating if methods exist or fields exist or vars exist?

# regression tests for returns before other stmts working, and not overwriting the blocks control transfers if a while
# or if or ifonly



if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="MiniPython Compiler")
    parser.add_argument("file", nargs="?", help="Input file (default if --str/--stdin) not set manually")
    input_group = parser.add_mutually_exclusive_group(required=False)

    input_group.add_argument("--str","--string",help="Input provided as arg through commandline", action='store_true')
    input_group.add_argument("--stdin",help="Input provided through stdin", action='store_true')

    stage_group = parser.add_mutually_exclusive_group()
    stage_group.add_argument("-t","--tokenize", help='Execute through tokenize stage', action='store_true')
    stage_group.add_argument("-p","--parse",help="Execute through parse stage",action='store_true')
    stage_group.add_argument("-c","--cfg",help="Execute through IR cfg stage",action='store_true')
    stage_group.add_argument("-o","--opt","--optimize","--optimization",help="Execute through IR optimization stage",action='store_true')
    stage_group.add_argument("-s","--ssa",help="Execute through IR ssa stage",action="store_true")
    stage_group.add_argument("-l","--vn","--lvn",help="Execute through IR ssa stage",action="store_true")

    parser.add_argument("--novn","--no-vn",help="skip the local version numbering step",action="store_true")
    parser.add_argument("--noopt","--no-opt",help="skip the peephold optimization step",action="store_true")
    args = parser.parse_args()


    if not any([args.file, args.str, args.stdin]):
        parser.error("Must provide input: filename, --str, or --stdin")

    if not any([args.tokenize, args.parse, args.opt, args.ssa, args.vn]):
        args.vn = True

    if args.str:
        inp = args.str
    elif args.stdin:
        inp = sys.stdin.read()
    else:
        with open(args.file) as f:
            inp = f.read()

    t = Tokenizer(inp)
    toks = t.tokenize()
    if args.tokenize:
        print(toks)
        sys.exit()

    p = Parser(t)
    parse_tree = p.parse_program()
    if args.parse:
        print(parse_tree)
        sys.exit()

    prog = parse_tree.to_ir_program()
    if args.cfg:
        print(prog)
        sys.exit()

    if not args.noopt:
        pre_eval_opt(prog)
    if args.opt:
        print(prog)
        sys.exit()

    mk_ssa(prog)
    if args.ssa:
        print(prog)
        sys.exit()

    if not args.novn:
        lvn(prog)
    if args.vn:
        print(prog)
        sys.exit()
