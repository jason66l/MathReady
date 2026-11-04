"""Turn LaTeX into plain English for screen readers.

  latex_to_speech(r"a = g \\sin \\theta")          -> "a equals g sine theta"
  latex_to_speech(r"\\int_0^{\\pi} x^2 \\sin x \\, dx")
      -> "the integral from 0 to pi of x squared sine x d x"

Deterministic, instant and free, so it can run on every edit.
"""
import re

GREEK = {
    "alpha": "alpha", "beta": "beta", "gamma": "gamma", "delta": "delta", "epsilon": "epsilon",
    "varepsilon": "epsilon", "zeta": "zeta", "eta": "eta", "theta": "theta", "vartheta": "theta",
    "iota": "iota", "kappa": "kappa", "lambda": "lambda", "mu": "mu", "nu": "nu", "xi": "xi",
    "pi": "pi", "rho": "rho", "sigma": "sigma", "tau": "tau", "upsilon": "upsilon", "phi": "phi",
    "varphi": "phi", "chi": "chi", "psi": "psi", "omega": "omega",
    "Gamma": "capital gamma", "Delta": "capital delta", "Theta": "capital theta",
    "Lambda": "capital lambda", "Xi": "capital xi", "Pi": "capital pi", "Sigma": "capital sigma",
    "Phi": "capital phi", "Psi": "capital psi", "Omega": "capital omega",
}
FUNCTIONS = {
    "sin": "sine", "cos": "cosine", "tan": "tangent", "sec": "secant", "csc": "cosecant",
    "cot": "cotangent", "arcsin": "arc sine", "arccos": "arc cosine", "arctan": "arc tangent",
    "sinh": "hyperbolic sine", "cosh": "hyperbolic cosine", "tanh": "hyperbolic tangent",
    "ln": "natural log of", "log": "log of", "exp": "exp of", "det": "determinant of",
    "max": "max", "min": "min",
}
SYMBOLS = {
    "=": "equals", "+": "plus", "-": "minus", "*": "times", "/": "divided by",
    "<": "is less than", ">": "is greater than", ",": ",", "!": "factorial", "'": "prime",
    ":": ":", "|": "absolute value", ".": ".",
    "(": "open paren", ")": "close paren", "[": "open bracket", "]": "close bracket",
    "lbrace": "open brace", "rbrace": "close brace",
    "cdot": "times", "times": "times", "div": "divided by", "pm": "plus or minus",
    "mp": "minus or plus", "le": "is less than or equal to", "leq": "is less than or equal to",
    "ge": "is greater than or equal to", "geq": "is greater than or equal to",
    "neq": "is not equal to", "ne": "is not equal to", "approx": "is approximately",
    "sim": "is similar to", "equiv": "is equivalent to", "propto": "is proportional to",
    "to": "approaches", "rightarrow": "goes to", "Rightarrow": "implies", "leftarrow": "from",
    "infty": "infinity", "partial": "partial", "nabla": "del", "circ": "degrees",
    "degree": "degrees", "in": "is in", "subset": "is a subset of", "cup": "union",
    "cap": "intersection", "forall": "for all", "exists": "there exists", "ldots": "dot dot dot",
    "cdots": "dot dot dot", "dots": "dot dot dot", "prime": "prime", "hbar": "h bar", "ell": "ell",
}
ACCENTS = {"vec": "vector {}", "hat": "{} hat", "bar": "{} bar", "dot": "{} dot",
           "ddot": "{} double dot", "tilde": "{} tilde", "overline": "{} bar"}
BIG_OPS = {"int": "integral", "iint": "double integral", "oint": "contour integral",
           "sum": "sum", "prod": "product"}
SKIP = {"left", "right", "big", "Big", "bigg", "Bigg", ",", ";", ":", "!", "quad", "qquad",
        "displaystyle", "textstyle", "limits", " ", "mathrm", "mathbf", "mathit", "boldsymbol"}
TEXT_COMMANDS = {"text", "textrm", "mathrm", "operatorname", "textbf", "mbox"}
POWER_WORDS = {"2": "squared", "3": "cubed"}

TOKEN = re.compile(r"\\[A-Za-z]+|\\.|\d+(?:\.\d+)?|[A-Za-z]|\S")


class _Parser:
    def __init__(self, latex: str):
        self.tokens = TOKEN.findall(latex)
        self.i = 0

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self):
        tok = self.peek()
        self.i += 1
        return tok

    # A "group" is {...} or a single token.
    def group_tokens(self) -> list[str]:
        if self.peek() == "{":
            self.take()
            depth, out = 1, []
            while self.peek() is not None:
                tok = self.take()
                if tok == "{":
                    depth += 1
                elif tok == "}":
                    depth -= 1
                    if depth == 0:
                        break
                out.append(tok)
            return out
        tok = self.take()
        return [tok] if tok is not None else []

    def group(self) -> str:
        return _speak_tokens(self.group_tokens())

    def raw_group(self) -> str:
        return "".join(t if t != "\\," else " " for t in self.group_tokens())

    def limits(self):
        """Read optional _{lower} and ^{upper} after a big operator."""
        lower = upper = None
        for _ in range(2):
            if self.peek() == "_":
                self.take()
                lower = self.group()
            elif self.peek() == "^":
                self.take()
                upper = self.group()
        return lower, upper

    def speak(self) -> list[str]:
        words: list[str] = []
        while self.peek() is not None:
            tok = self.take()
            if tok in ("{", "}"):
                continue
            if tok == "^":
                exp_tokens = self.group_tokens()
                exp = _speak_tokens(exp_tokens)
                if exp in POWER_WORDS:
                    words.append(POWER_WORDS[exp])
                elif exp == "degrees":
                    words.append("degrees")
                elif len(exp_tokens) == 1 and exp_tokens[0].replace(".", "").isdigit():
                    words.append(f"to the power {exp}")
                elif len(exp_tokens) == 1:
                    words.append(f"to the {exp}")
                else:
                    words.append(f"to the power {exp}, end power")
                continue
            if tok == "_":
                words.append(f"sub {self.group()}")
                continue
            if tok == "&":
                words.append(",")
                continue
            if tok == "\\\\":
                words.append(";")
                continue
            if not tok.startswith("\\"):
                words.append(SYMBOLS.get(tok, tok))
                continue

            name = tok[1:]
            if name in ("{", "}"):
                words.append("open brace" if name == "{" else "close brace")
                continue
            if name in SKIP:
                continue
            if name == "frac" or name in ("dfrac", "tfrac"):
                num_t, den_t = self.group_tokens(), self.group_tokens()
                num, den = _speak_tokens(num_t), _speak_tokens(den_t)
                if len(num_t) == 1 and len(den_t) == 1:
                    words.append(f"{num} over {den}")
                else:
                    words.append(f"the fraction {num}, over {den}, end fraction")
            elif name == "sqrt":
                index = None
                if self.peek() == "[":
                    self.take()
                    idx = []
                    while self.peek() not in (None, "]"):
                        idx.append(self.take())
                    self.take()
                    index = _speak_tokens(idx)
                inner = self.group()
                words.append(f"the {index}th root of {inner}, end root" if index else f"the square root of {inner}, end root")
            elif name in BIG_OPS:
                lower, upper = self.limits()
                phrase = f"the {BIG_OPS[name]}"
                if lower and upper:
                    phrase += f" from {lower} to {upper}"
                elif lower:
                    phrase += f" over {lower}"
                words.append(phrase + " of")
            elif name == "lim":
                lower, _ = self.limits()
                words.append(f"the limit as {lower} of" if lower else "the limit of")
            elif name in FUNCTIONS:
                words.append(FUNCTIONS[name])
            elif name in GREEK:
                words.append(GREEK[name])
            elif name in SYMBOLS:
                words.append(SYMBOLS[name])
            elif name in ACCENTS:
                words.append(ACCENTS[name].format(self.group()))
            elif name in TEXT_COMMANDS:
                words.append(self.raw_group().strip())
            elif name == "begin":
                env = self.raw_group()
                words.append("the matrix with rows:" if "matrix" in env else "")
            elif name == "end":
                env = self.raw_group()
                words.append("end matrix" if "matrix" in env else "")
            else:
                words.append(name)  # unknown command: say its name
        return words


def _speak_tokens(tokens: list[str]) -> str:
    p = _Parser("")
    p.tokens = tokens
    return _tidy(" ".join(w for w in p.speak() if w))


def _tidy(text: str) -> str:
    text = re.sub(r"\s+([,;.])", r"\1", text)
    text = re.sub(r"([,;])(?=[,;])", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ,;")


def latex_to_speech(latex: str) -> str:
    """Plain-English reading of a LaTeX expression. Never raises."""
    try:
        return _tidy(" ".join(w for w in _Parser(latex or "").speak() if w))
    except Exception:
        return latex or ""