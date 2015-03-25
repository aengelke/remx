# The ReMX regular expression library for Python

# Differences of ReMX to the re library of Python:
#  - ReMX supports tuples as regex and objects as checkables
#  - ReMX is lightweight and deterministic
#  - ReMX has a linear runtime
#  - ReMX only supports a subset of regular
#    expressions that are supported in re.
#  - ReMX does not fully support extractions.

# Usage:
# ```python
# import remx
# remx.compile(r"[a-zA-Z0-9_]+")                  # => <remx.remx at ...>
# remx.match(r"hello( world)?", "hello day")      # => hello
# remx.extract(r"hello ([a-z]+)", "hello world!") # => "hello world", ["world"]
# ```


def memodict(f):
    """ Memoization decorator for a function taking a single argument """
    class memodict(dict):
        __slots__ = ()
        def __missing__(self, key):
            self[key] = ret = f(key)
            return ret
    return memodict().__getitem__

class remx:
    def __init__(self, parsedRegex, definitions=None):
        self.data = parsedRegex
        self.definitions = {} if not definitions else definitions
        self.extractfn = lambda x, y : x
    def define(self, name, value):
        self.definitions[name] = value
    def match(self, string):
        return self.extract(string)[0]
    def extract(self, string):
        d = self.data
        sub = string
        extract = []
        for part in d:
            if type(part) == list:
                result, subextract = remx(part, self.definitions).extract(sub)
                if result is None:
                    return None, []
                sub = sub[len(result):]
                extract.append(result)
                extract += subextract
            elif part[0] == "?":
                result, subextract = remx(part[1], self.definitions).extract(sub)
                if result is not None:
                    sub = sub[len(result):]
                    extract += subextract
            elif part[0] == "$":
                if len(sub) != 0:
                    return None, []
            elif part[0] == "*":
                while True:
                    result, subextract = remx(part[1], self.definitions).extract(sub)
                    if result is None:
                        break
                    extract += subextract
                    sub = sub[len(result):]
            elif len(sub) == 0:
                return None, []
            elif part[0] == "|":
                result, subextract = remx(part[1], self.definitions).extract(sub)
                if result is None:
                    result, subextract = remx(part[2], self.definitions).extract(sub)
                    if result is None:
                        return None, []
                extract += subextract
                sub = sub[len(result):]
            elif part[0] == "]":
                result = True
                for p in part[1]:
                    d = self.definitions[p] if p in self.definitions else None
                    if not d and str(sub[0]) == p:
                        result = False
                        break
                    elif d:
                        if type(d) == remx:
                            result, _ = d.extract(sub)
                            if result is None:
                                break
                if not result:
                    return None, []
                sub = sub[1:]
            elif part[0] == "[":
                result = None
                for p in part[1]:
                    d = self.definitions[p] if p in self.definitions else None
                    if not d and str(sub[0]) == p:
                        result = True
                        sub = sub[1:]
                        break
                    elif d:
                        if isinstance(d, remx):
                            result, subextract = d.extract(sub)
                            if result is not None:
                                extract.append(("sub", p, subextract))
                                sub = sub[len(result):]
                                break
                # if str(sub[0]) not in part[1]:
                if result is None:
                    return None, []
                #sub = sub[1:]
            else:
                return None, []
        result = (string[:-len(sub)] if len(sub) > 0 else string)
        return result, self.extractfn(extract, result)

    SMALL_LITERAL = "abcdefghijklmnopqrstuvwxyz"
    BIG_LITERAL = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    NUMERIC = "0123456789"
    NEWLINE = "\n\r"
    WHITESPACE = " \t"
    TABULATOR = "\t"

    @staticmethod
    @memodict
    def _compile(regex):
        parsedRegex = []
        sub = regex
        while len(sub) > 0:
            if sub[0] == "[":
                inner = []
                reverse = sub[1] == "^"
                isub = sub[2 if reverse else 1:]
                while len(isub) > 0:
                    if len(isub) > 2 and isub[1] == "-":
                        charset = None
                        if isub[0] in remx.SMALL_LITERAL:
                            charset = remx.SMALL_LITERAL
                        if isub[0] in remx.BIG_LITERAL:
                            charset = remx.BIG_LITERAL
                        if isub[0] in remx.NUMERIC:
                            charset = remx.NUMERIC
                        if charset and isub[2] in charset:
                            indexa = charset.find(isub[0])
                            indexb = charset.find(isub[2])
                            if indexa < indexb:
                                inner.append(charset[indexa:indexb+1])
                                isub = isub[3:]
                                continue
                    if isub[0] == "\\" and len(isub) > 1:
                        if isub[1] == "n":
                            inner.append(remx.NEWLINE)
                        elif isub[1] == "w":
                            inner.append(remx.WHITESPACE)
                        elif isub[1] == "t":
                            inner.append(remx.TABULATOR)
                        elif isub[1] == "\\":
                            inner.append("\\")
                        elif isub[1] == "^":
                            inner.append("^")
                        elif isub[1] == "]":
                            inner.append("]")
                        elif isub[1] == "[":
                            inner.append("[")
                        else:
                            print "Unknown replacement " + isub[1]
                            return None
                        isub = isub[2:]
                        continue
                    if isub[0] == "]":
                        break
                    inner.append(isub[0])
                    isub = isub[1:]
                sub = sub[len(sub) - len(isub) + 1:]#len(sub) -
                inner = "".join(inner) if type(regex) == str else inner
                parsedRegex.append(("]" if reverse else "[", inner))
            elif sub[0] == "(":
                newparsed, newsub = remx._compile(sub[1:])
                parsedRegex.append(newparsed.data)
                if newsub[0] != ")":
                    return None
                sub = newsub[1:]
            elif sub[0] == "]":
                return None
            elif sub[0] == ")":
                return remx(parsedRegex), sub
            elif sub[0] == "+":
                parsedRegex.append(("*", [parsedRegex[-1]]))
                sub = sub[1:]
            elif sub[0] == "*":
                parsedRegex.append(("*", [parsedRegex.pop()]))
                sub = sub[1:]
            elif sub[0] == "$":
                parsedRegex.append(("$",))
                if len(sub) != 1:
                    return None
                sub = ""
            elif sub[0] == "?":
                parsedRegex.append(("?", [parsedRegex.pop()]))
                sub = sub[1:]
            elif sub[0] == ".":
                parsedRegex.append(("]", ""))
                sub = sub[1:]
            elif sub[0] == "|":
                newparsed, newsub = remx._compile(sub[1:])
                parsedRegex = [("|", parsedRegex, newparsed.data)]
                sub = newsub
            elif sub[0] == "\\":
                if sub[1] in ".*+?|()[]\\":
                    parsedRegex.append(("[", sub[1]))
                elif sub[1] == "w":
                    parsedRegex.append(("[", remx.WHITESPACE))
                elif sub[1] == "n":
                    parsedRegex.append(("[", remx.NEWLINE))
                elif sub[1] == "t":
                    parsedRegex.append(("[", remx.TABULATOR))
                sub = sub[2:]
            else:
                parsedRegex.append(("[", sub[0:1]))
                sub = sub[1:]
        return remx(parsedRegex), ""

def compile(regex, extractfn=None):
    parsedRegex, remaining = remx._compile(regex)
    if len(remaining) > 0 or not parsedRegex:
        return None
    if extractfn:
        parsedRegex.extractfn = extractfn
    return parsedRegex

def match(regex, string):
    return compile(regex).match(string)

def extract(regex, string):
    return compile(regex).extract(string)
