"""GOMIKAMI.EXE のテスト実行と採点。

Pyodide（ブラウザ）と CPython（tools/check_stages.py）の両方から使う。
外部ライブラリには依存しない。
"""
import ast
import builtins
import contextlib
import copy
import importlib
import io
import json
import os
import re
import sys

PLAYER_MODULES = ("main", "legacy_util")

# ---------------------------------------------------------------- テスト実行


def _check_eq(actual, expected, source):
    # 型まで一致を要求する（__eq__/__ne__ を細工したオブジェクトで誤魔化されないように）
    if type(actual) is not type(expected) or actual != expected:
        raise AssertionError(
            f"{source}\n  期待値: {expected!r} ({type(expected).__name__})"
            f"\n  実際値: {actual!r} ({type(actual).__name__})"
        )


class _AssertRewriter(ast.NodeTransformer):
    """`assert a == b` を、期待値と実際値を表示する呼び出しに書き換える。"""

    def __init__(self, source):
        self.source = source

    def visit_Assert(self, node):
        test = node.test
        if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
            text = ast.get_source_segment(self.source, node) or "assert"
            call = ast.Call(
                func=ast.Name("__gk_check_eq", ast.Load()),
                args=[test.left, test.comparators[0], ast.Constant(text)],
                keywords=[],
            )
            return ast.copy_location(ast.Expr(call), node)
        return node


def _forget_player_modules():
    for name in PLAYER_MODULES:
        sys.modules.pop(name, None)
    importlib.invalidate_caches()


def _format_exc(exc):
    if isinstance(exc, AssertionError):
        return str(exc) or "assert に失敗"
    return f"{type(exc).__name__}: {exc}"


def run_tests(workdir, files, test_files):
    """files: {ファイル名: ソース}。test_files: {テストファイル名: ソース}。"""
    os.makedirs(workdir, exist_ok=True)
    for name, src in files.items():
        with open(os.path.join(workdir, name), "w", encoding="utf-8") as f:
            f.write(src)
    if workdir not in sys.path:
        sys.path.insert(0, workdir)

    results = []
    for test_name, test_src in test_files.items():
        _forget_player_modules()
        tree = _AssertRewriter(test_src).visit(ast.parse(test_src, test_name))
        ast.fix_missing_locations(tree)
        namespace = {"__name__": test_name.removesuffix(".py"), "__gk_check_eq": _check_eq}
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(tree, test_name, "exec"), namespace)
        except BaseException as exc:  # main.py の構文エラーや import 失敗
            results.append({"file": test_name, "name": "(読み込み)", "ok": False, "message": _format_exc(exc)})
            continue
        for name, fn in namespace.items():
            if not (name.startswith("test_") and callable(fn)):
                continue
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    fn()
                results.append({"file": test_name, "name": name[5:], "ok": True, "message": ""})
            except BaseException as exc:
                results.append({"file": test_name, "name": name[5:], "ok": False, "message": _format_exc(exc)})
    return results


# ---------------------------------------------------------------- 採点

ALLOWED_SHORT_NAMES = {"i", "j", "k", "n", "_"}
BAD_NAME_RE = re.compile(
    r"^(tmp|temp|data|flag|foo|bar|hoge|fuga|piyo|val|ret|res|obj|buf|work|aaa|xxx)\d*$"
    r"|^[a-z]{1,3}\d+$"
    r"|^(?P<ch>[a-z])(?P=ch)+\d*$"  # zzz, qqq
)
BUILTIN_NAMES = {n for n in dir(builtins) if not n.startswith("_")}
# 監査部: これらを使ったコードは実行させない（採点やテストの改ざん対策）。
# 方針は許可リスト。プレイヤーのコードから sys やフレームに手が届く経路を塞ぐ。
FORBIDDEN_NAMES = {
    "exec", "eval", "compile", "globals", "locals", "vars", "dir", "getattr", "setattr", "delattr",
    "type", "open", "input", "breakpoint", "memoryview", "help", "exit", "quit", "license", "credits",
    "copyright",
}
FORBIDDEN_ATTRS = {"modules", "sys", "builtins", "mro", "format_map"}
# ジェネレータ・コルーチン・フレーム・トレースバック・コードオブジェクトの属性
FORBIDDEN_ATTR_PREFIXES = ("_", "gi_", "cr_", "ag_", "f_", "tb_", "co_")
# 定型として許す dunder（比較の細工は _check_eq の型チェックで無効化している）
ALLOWED_DUNDER_NAMES = {"__name__"}
ALLOWED_DUNDER_STRINGS = {"__main__"}
ALLOWED_DUNDER_DEFS = {
    "__init__", "__repr__", "__str__", "__post_init__", "__eq__", "__ne__", "__lt__", "__le__",
    "__gt__", "__ge__", "__hash__", "__len__", "__iter__", "__contains__", "__bool__", "__getitem__",
    "__add__", "__sub__", "__mul__",
}
# 使ってよいモジュールと、その中で使ってよい名前（import M でも from M import N でも同じ表で判定）。
# None は「_ で始まらない名前なら何でも」。中に sys などのモジュールを抱えていないものだけ None にする。
MODULES = {
    "datetime": None,
    "math": None,
    "itertools": None,
    "decimal": None,
    "main": None,
    "legacy_util": None,
    "__future__": {"annotations"},
    "functools": {"reduce", "lru_cache", "cache", "partial", "total_ordering", "cached_property", "cmp_to_key"},
    "calendar": {
        "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY", "Day", "Month",
        "isleap", "monthrange", "weekday", "day_name", "month_name", "monthcalendar",
    },
    "collections": {"defaultdict", "Counter", "namedtuple", "OrderedDict", "deque", "ChainMap"},
    "enum": {"Enum", "IntEnum", "StrEnum", "Flag", "IntFlag", "auto", "unique"},
    "dataclasses": {"dataclass", "field", "replace", "asdict", "astuple"},
    "typing": {
        "Any", "Optional", "Union", "Callable", "Final", "Literal", "NamedTuple", "TypedDict",
        "Iterable", "Iterator", "Sequence", "Mapping", "ClassVar", "Protocol",
        "List", "Dict", "Tuple", "Set", "FrozenSet",
    },
    "fractions": {"Fraction"},
    "statistics": {"mean", "median", "mode", "stdev", "pstdev"},
    "string": {"ascii_letters", "ascii_lowercase", "ascii_uppercase", "digits", "punctuation"},
}
MAX_SOURCE_CHARS = 20000
LONG_LINE = 99
NESTING_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try, ast.Match)
FUNC_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)
DUP_MIN_NODES = 10
DUP_MAX_WINDOW = 3


def _is_constant_name(name):
    return name.isupper()


def _own_nodes(root):
    """root 以下のノード。ただし入れ子の関数・クラスの中には入らない。"""
    stack = list(ast.iter_child_nodes(root))
    while stack:
        node = stack.pop()
        yield node
        if not isinstance(node, (*FUNC_NODES, ast.ClassDef)):
            stack.extend(ast.iter_child_nodes(node))


def _complexity(unit):
    score = 1
    for node in _own_nodes(unit):
        if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.ExceptHandler, ast.match_case)):
            score += 1
        elif isinstance(node, ast.BoolOp):
            score += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            score += 1 + len(node.ifs)
    return score


def _is_elif(parent, child):
    return (
        isinstance(parent, ast.If)
        and len(parent.orelse) == 1
        and parent.orelse[0] is child
        and isinstance(child, ast.If)
        and child.col_offset == parent.col_offset
    )


def _nesting(node, depth=0):
    deepest = depth
    for field in ("body", "orelse", "finalbody", "handlers", "cases"):
        for child in getattr(node, field, []) or []:
            if isinstance(child, (*FUNC_NODES, ast.ClassDef)):
                # 関数の中に関数を入れてネストを隠すのは許さない
                if not isinstance(node, ast.Module):
                    deepest = max(deepest, _nesting(child, depth + 1))
                continue
            if isinstance(child, (ast.ExceptHandler, ast.match_case)):
                deepest = max(deepest, _nesting(child, depth))
            elif isinstance(child, NESTING_NODES):
                child_depth = depth if _is_elif(node, child) else depth + 1
                deepest = max(deepest, _nesting(child, child_depth))
    return deepest


class _Normalizer(ast.NodeTransformer):
    """名前と定数を潰して、コピペの「形」だけを比べられるようにする。"""

    def visit_Name(self, node):
        return ast.Name("_", node.ctx)

    def visit_arg(self, node):
        node.arg = "_"
        node.annotation = None
        return node

    def visit_Constant(self, node):
        return ast.Constant(type(node.value).__name__)


def _node_count(node):
    return sum(1 for n in ast.walk(node) if not isinstance(n, (ast.expr_context, ast.operator, ast.cmpop)))


def _duplicated_lines(tree):
    seen = {}
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            stmts = getattr(node, field, None)
            if not isinstance(stmts, list) or not stmts or not isinstance(stmts[0], ast.stmt):
                continue
            for size in range(1, DUP_MAX_WINDOW + 1):
                for start in range(len(stmts) - size + 1):
                    window = stmts[start:start + size]
                    if sum(_node_count(s) for s in window) < DUP_MIN_NODES:
                        continue
                    if any(isinstance(s, (*FUNC_NODES, ast.ClassDef)) for s in window):
                        continue
                    key = "|".join(ast.dump(_Normalizer().visit(copy.deepcopy(s))) for s in window)
                    lines = range(window[0].lineno, window[-1].end_lineno + 1)
                    seen.setdefault(key, []).append(lines)
    duplicated = set()
    for occurrences in seen.values():
        if len(occurrences) > 1:
            for lines in occurrences:
                duplicated.update(lines)
    return len(duplicated)


def _bad_names(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, FUNC_NODES):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
    bad = set()
    for name in names:
        if name in BUILTIN_NAMES:
            bad.add(name)
        elif len(name) == 1 and name not in ALLOWED_SHORT_NAMES:
            bad.add(name)
        elif BAD_NAME_RE.match(name.lower()):
            bad.add(name)
    return sorted(bad)


def _constant_definitions(tree):
    """モジュール直下の `UPPER = ...` の右辺（定数定義はマジックナンバー扱いしない）。"""
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and all(isinstance(t, ast.Name) and _is_constant_name(t.id) for t in stmt.targets):
            yield stmt.value
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and _is_constant_name(stmt.target.id):
            if stmt.value is not None:
                yield stmt.value


def _magic_numbers(tree):
    allowed = {id(n) for value in _constant_definitions(tree) for n in ast.walk(value)}
    count = 0
    for node in ast.walk(tree):
        if id(node) in allowed or not isinstance(node, ast.Constant):
            continue
        value = node.value
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value not in (0, 1):
            count += 1
    return count


def _global_state(tree):
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            count += len(node.names)
    for stmt in tree.body:
        targets = stmt.targets if isinstance(stmt, ast.Assign) else [getattr(stmt, "target", None)]
        if isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            count += sum(1 for t in targets if isinstance(t, ast.Name) and not _is_constant_name(t.id))
    return count


def _module_allows(module, name):
    if module not in MODULES or name.startswith("_"):
        return False
    allowed = MODULES[module]
    return allowed is None or name in allowed


def _bad_attr(name):
    return name.startswith(FORBIDDEN_ATTR_PREFIXES) or name in FORBIDDEN_ATTRS


def _audit(tree):
    """採点やテストを改ざんできそうな書き方を列挙する。"""
    found = []
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    module_aliases = {}  # import M as X の X → M
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name in MODULES:
                    module_aliases[a.asname or a.name] = a.name
                else:
                    found.append(f"import {a.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level or module not in MODULES:
                found.append(f"from {module} import")
            found += [f"from {module} import {a.name}" for a in node.names if not _module_allows(module, a.name)]

    # 文として置いただけの文字列（docstring など）は無害なので見ない
    bare_strings = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            name = node.id
            if name in FORBIDDEN_NAMES or "gk_" in name or (name.startswith("__") and name not in ALLOWED_DUNDER_NAMES):
                found.append(name)
            elif name in module_aliases:
                # モジュールは「M.名前」の形でしか使わせない（別名に入れて持ち回るのも不可）
                parent = parents.get(node)
                if not (isinstance(parent, ast.Attribute) and parent.value is node
                        and _module_allows(module_aliases[name], parent.attr)):
                    attr = parent.attr if isinstance(parent, ast.Attribute) else "?"
                    found.append(f"{module_aliases[name]}.{attr}")
        elif isinstance(node, ast.Attribute) and _bad_attr(node.attr):
            found.append(f".{node.attr}")
        elif isinstance(node, ast.MatchClass):
            found += [f"case (...{a}=)" for a in node.kwd_attrs if _bad_attr(a)]
        elif isinstance(node, FUNC_NODES) and node.name.startswith("__") and node.name not in ALLOWED_DUNDER_DEFS:
            found.append(f"def {node.name}")
        elif (isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in bare_strings
              and node.value not in ALLOWED_DUNDER_STRINGS and ("__" in node.value or "gk_" in node.value)):
            found.append(repr(node.value)[:30])
    return sorted(set(found))


def _tricks(tree):
    """読みにくい小細工: 定数リストを数値添字で引く、真偽値を掛け算に使う。"""
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            index = node.slice
            numeric = isinstance(index, ast.Constant) and isinstance(index.value, int) and not isinstance(index.value, bool)
            if numeric or isinstance(index, (ast.BinOp, ast.Compare, ast.BoolOp)):
                count += 1
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Add, ast.Sub)):
            if any(isinstance(side, (ast.Compare, ast.BoolOp)) or (isinstance(side, ast.UnaryOp) and isinstance(side.op, ast.Not))
                   for side in (node.left, node.right)):
                count += 1
    return count


def analyze(source):
    try:
        return _analyze(source)
    except (RecursionError, MemoryError):
        return {"error": "解析不能", "audit": ["解析不能なコード"]}


def _analyze(source):
    if len(source) > MAX_SOURCE_CHARS:
        return {"error": f"長すぎます（{MAX_SOURCE_CHARS}文字まで）", "audit": ["巨大なソース"]}
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {"error": f"SyntaxError: {exc.msg} ({exc.lineno}行目)"}
    units = [tree] + [n for n in ast.walk(tree) if isinstance(n, FUNC_NODES)]
    funcs = units[1:]
    bad_names = _bad_names(tree)
    return {
        "error": None,
        "metrics": {
            "complexity": max(_complexity(u) for u in units),
            "nesting": max(_nesting(u) for u in units),
            "duplication": _duplicated_lines(tree),
            "length": max((f.end_lineno - f.lineno + 1 for f in funcs), default=0),
            "naming": len(bad_names),
            "magic": _magic_numbers(tree),
            "globals": _global_state(tree),
            "longlines": sum(1 for line in source.splitlines() if len(line) > LONG_LINE),
            "tricks": _tricks(tree),
        },
        "bad_names": bad_names,
        "audit": _audit(tree),
    }


# ---------------------------------------------------------------- JS からの入口


def js_run(payload_json):
    payload = json.loads(payload_json)
    tests = run_tests(payload["workdir"], payload["files"], payload["tests"])
    return json.dumps(tests, ensure_ascii=False)


def js_analyze(source):
    return json.dumps(analyze(source), ensure_ascii=False)
