﻿## a subset of scheme

from __future__ import division
from functools import reduce

try:
    input = raw_input
except NameError:
    pass

class Tokenizer:
    """
    Turn a string into a list of tokens
    Have the ability to rollback using the rollback instance method
    """
    def __init__(self, s):
        # separating open and close parens
        s = s.replace('(', ' ( ').replace(')', ' ) ')
        # separating quotes
        s = s.replace("'", " ' ")

        self.tokens = s.split()
        self.counter = 0

    def __next__(self):
        self.counter += 1
        try:
            return self.tokens[self.counter - 1]
        except IndexError:
            raise StopIteration

    # for compatibility
    next = __next__

    def __iter__(self):
        return self

    def rollback(self):
        """
        Rollback one token
        """
        self.counter -= 1
        return self

def parse_list(tokens):
    """
    Input: a stream of tokens that contains the content of a list
    Output: a list representing that Scheme list
    Exceptions: when reaching the end of token stream, raise SyntaxError since the close parens token is missing
    """

    retval = []
    for tok in tokens:
        if tok == ')':
            return retval
        else:
            retval.append(parse_sexp(tokens.rollback()))
    raise SyntaxError("Unexpected end of token stream")

def parse_atom(token):
    """
    Input: a token
    Output: an represented atom

    Try to turn the token into a number, else just return it
    """
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return token
    return token
    

def parse_sexp(tokens):
    """
    Input: a stream of tokens
    Output: an atom if first of stream represents a token
            a list if first of stream represents a list
    """
    try:
        tok = next(tokens)
        if tok == '(':
            return parse_list(tokens)
        if tok == "'":
            retval = ['quote']
            retval.append(parse_sexp(tokens))
            return retval
        else:
            return parse_atom(tok)
    except (StopIteration, IndexError):
        raise SyntaxError("Unexpected end of token stream")

def isatom(a):
    if isinstance(a, int):
        return True
    else:
        return isinstance(a, str)

def isnumber(a):
    return isinstance(a, int) or isinstance(a, float)

def islist(l):
    return isinstance(l, list)

def primitivequit():
    raise KeyboardInterrupt

def primitivecons(a, b):
    retval = [a]
    retval.extend(b)
    return retval

def makeenv(outer=None):
    """
    Make an empty environment with the outer environment specified
    """

    retval = {'outer': outer}
    return retval

def addtoglobal(env):
    env.update({
        'quit': primitivequit,
        '+': lambda *args: sum(args),
        '*': lambda *args: reduce(lambda x, y: x * y, args, 1),
        '-': lambda *args: -args[0] if len(args) == 0 else args[0] - sum(args[1:]),
        '/': lambda *args: reduce(lambda x, y: x / y, args[1:], args[0]),
        '<': lambda x, y: x < y,
        '>': lambda x, y: x > y,
        '=': lambda x, y: x == y,
        'eq?': lambda x, y: x == y,
        'zero?': lambda x: x == 0,
        'null?': lambda x: x == [],
        'atom?': lambda x: isinstance(x, str),
        'not': lambda x: not x,
        'cons': primitivecons,
        'car': lambda l: l[0],
        'cdr': lambda l: l[1:],
        'else': True
        })
    return env

globalenv = addtoglobal(makeenv())

def eval(sexp, env=globalenv):
    if islist(sexp):
        op = sexp[0]
        if op == 'begin':
            for exp in sexp[1:-1]:
                eval(exp, env)
            return eval(sexp[-1], env)
        elif op == 'quote':
            return sexp[1]
        elif op == 'lambda':
            exps = sexp[2:]
            exps.insert(0, 'begin')
            return Lambda(env, sexp[1], exps)
        elif op == 'cond':
            for cond_exp in sexp[1:]:
                cond = cond_exp[0]
                exp = cond_exp[1:]
                if eval(cond, env):
                    exp.insert(0, 'begin')
                    return eval(exp, env)
        elif op == 'define':
            defn = eval(sexp[2], env)
            env.update({
                sexp[1]: defn
                })
            return defn
        elif op == 'and':
            for exp in sexp[1:]:
                if not eval(exp, env):
                    return False
            return True
        elif op == 'or':
            for exp in sexp[1:]:
                if eval(exp, env):
                    return True
            return False
        else: # apply
            op = eval(sexp[0], env)
            args = []
            for exp in sexp[1:]:
                args.append(eval(exp, env))
            return op(*args)
    elif sexp == '#t':
        return True
    elif sexp == '#f':
        return False
    elif isnumber(sexp):
        return sexp
    else:
        return find(sexp, env)

class Lambda:
    def __init__(self, env, arglist, sexp):
        self.arglist = arglist
        self.sexp = sexp
        self.outerenv = env
    def __repr__(self):
        return '<compound function at 0x{0:x}>'.format(id(self))
    def __call__(self, *arg, **kwarg):
        if len(arg) != len(self.arglist):
            raise TypeError("Expected {0} arguments ({1} provided)".format(len(self.arglist), len(arg)))
        localenv = makeenv(self.outerenv)
        localenv.update(dict(zip(self.arglist, arg)))
        return eval(self.sexp, localenv)

def find(sym, env):
    """
    Find a symbol in env
    If symbol not in env or any of its outer, return None
    """

    try:
        if sym in env:
            return env[sym]
        else:
            return find(sym, env['outer'])
    except TypeError:
        # once hit here, sym is nowhere to be found
        raise NameError("Undefined atom {0!r}".format(sym))

def REPL():
    while True:
        try:
            inp = input('* ')
            while True:
                tokens = Tokenizer(inp)
                try:
                    sexp = parse_sexp(tokens)
                    break
                except SyntaxError:
                    inp += ' ' + input('  ')
            print(eval(sexp))
        except (KeyboardInterrupt, EOFError):
            print("Exiting... Bye!")
            return
        except Exception as e:
            print(str(e))

if __name__ == '__main__':
    REPL()
