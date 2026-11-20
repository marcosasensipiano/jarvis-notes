"""Static guardrail for skills Jarvis writes itself.

This is NOT a sandbox. It blocks the obvious dangerous things (process spawning, sockets,
dynamic code execution) so a bad generation fails fast. The real safety net is that learned
skills land as git commits you can review, and big builds wait for `jarvis approve`."""
import ast

FORBIDDEN_IMPORTS = {
    "subprocess", "socket", "ctypes", "shutil", "multiprocessing", "importlib", "pickle",
    "marshal", "http", "urllib", "requests", "os", "sys", "builtins", "pty", "signal",
    "asyncio", "threading", "webbrowser", "smtplib", "ftplib", "telnetlib",
}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__", "globals", "locals", "vars", "input"}
FORBIDDEN_ATTRS = {"__subclasses__", "__globals__", "__builtins__", "__code__", "__bases__", "__mro__"}


def check_source(src: str, filename: str = "<skill>") -> list:
    try:
        tree = ast.parse(src, filename)
    except SyntaxError as e:
        return [f"{filename}: syntax error: {e}"]
    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] in FORBIDDEN_IMPORTS:
                    problems.append(f"{filename}:{node.lineno}: import of '{a.name}' is not allowed")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in FORBIDDEN_IMPORTS:
                problems.append(f"{filename}:{node.lineno}: import from '{node.module}' is not allowed")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                problems.append(f"{filename}:{node.lineno}: call to '{node.func.id}' is not allowed")
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRS:
            problems.append(f"{filename}:{node.lineno}: access to '{node.attr}' is not allowed")
    return problems
