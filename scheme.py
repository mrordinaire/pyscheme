﻿## a subset of scheme

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
    except (StopIteration, IndexError):
        return

    if tok == '(':
        return parse_list(tokens)
    else:
        return parse_atom(tok)

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

def primitiveadd(*args):
    return sum(args)

def primitivemult(*args):
    retval = 1
    for i in args:
        retval *= i
    return retval

def primitivediff(*args):
    length = len(args)
    if length < 1:
        raise TypeError("Expected at least 1 arguments ({0} provided)".format(len(args)))
    # inversion
    elif length == 1:
        return -args[0]

    retval = args[0]
    for i in args[1:]:
        retval -= i
    return retval

def primitivediv(*args):
    if len(args) < 1:
        raise TypeError("Expected at least 1 arguments ({0} provided)".format(len(args)))
    retval = args[0]
    for i in args[1:]:
        retval /= i
    return retval

def primitivelt(a, b):
    return a < b

def primitivegt(a, b):
    return a > b

def primitivenot(a):
    return not a

def primitiveeqn(a, b):
    return a == b

def primitivezerop(a):
    return a == 0

def primitivenullp(a):
    return a == []

def primitivecons(a, b):
    retval = [a]
    retval.extend(b)
    return retval

def primitivecar(a):
    return a[0]

def primitivecdr(a):
    return a[1:]

def primitiveatomp(a):
    return isinstance(a, str)

def makeenv(outer=None):
    """
    Make an empty environment with the outer environment specified
    """

    retval = {'outer': outer}
    return retval

def addtoglobal(globalenv):
    globalenv.update({
        'quit': primitivequit,
        '+': primitiveadd,
        '*': primitivemult,
        '-': primitivediff,
        '/': primitivediv,
        '<': primitivelt,
        '>': primitivegt,
        '=': primitiveeqn,
        'eq?': primitiveeqn,
        'zero?': primitivezerop,
        'null?': primitivenullp,
        'atom?': primitiveatomp,
        'not': primitivenot,
        'cons': primitivecons,
        'car': primitivecar,
        'cdr': primitivecdr,
        'else': True
        })
    return globalenv

evalto = makeenv()
globalenv = addtoglobal(makeenv(evalto))

def evalbegin(sexp, env=globalenv):
    for exp in sexp[1:-1]:
        eval(exp, env)
    return eval(sexp[-1], env)

def evalquote(sexp, env=globalenv):
    return sexp[1]

def evallambda(sexp, env=globalenv):
    exps = sexp[2:]
    exps.insert(0, 'begin')
    return Lambda(env, sexp[1], exps)

def evalcond(sexp, env=globalenv):
    for cond_exp in sexp[1:]:
        cond = cond_exp[0]
        exp = cond_exp[1:]
        if eval(cond, env):
            exp.insert(0, 'begin')
            return eval(exp, env)

def evaldefine(sexp, env=globalenv):
    defn = eval(sexp[2], env)
    env.update({
        sexp[1]: defn
        })
    return defn

def evaland(sexp, env=globalenv):
    for exp in sexp[1:]:
        if not eval(exp, env):
            return False
    return True

def evalor(sexp, env=globalenv):
    for exp in sexp[1:]:
        if eval(exp, env):
            return True
    return False

evalto.update({
        'begin': evalbegin,
        'quote': evalquote,
        'lambda': evallambda,
        'cond': evalcond,
        'define': evaldefine,
        'and': evaland,
        'or': evalor
        })

def apply(sexp, env=globalenv):
    op = eval(sexp[0], env)
    args = []
    for exp in sexp[1:]:
        args.append(eval(exp, env))
    return op(*args)

def eval(sexp, env=globalenv):
    if islist(sexp):
        try:
            func = evalto[sexp[0]]
            return func(sexp, env)
        except (KeyError, TypeError):
            return apply(sexp, env)
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
        return '<function <lambda> at 0x{0:x}>'.format(id(self))
    def __call__(self, *arg, **kwarg):
        if len(arg) != len(self.arglist):
            raise TypeError("Expected {0} arguments ({1} provided)".format(len(self.arglist), len(arg)))
        localenv = makeenv(self.outerenv)
        localenv.update(dict(zip(self.arglist, arg)))
        return eval(self.sexp, localenv)

def error(s):
    print('ERROR:', s)

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
    try:
        while True:
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

if __name__ == '__main__':
    REPL()
