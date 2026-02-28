# -*- coding: utf-8 -*-
"""
Name obfuscation transformer for PyObfuscator.

Provides capabilities for renaming variables, functions, classes,
and attributes with cross-file consistency.
"""

import ast
import random
import string
import hashlib
from typing import Dict, Set, Optional, List, Tuple, Union

from ..registry import TransformerRegistry
from .base import BaseTransformer
from ...constants import ReservedNames, FrameworkPresets


class NameGenerator:
    """
    Generates obfuscated names for identifiers.
    """

    def __init__(self, prefix: str = "_", style: str = "random"):
        self.prefix = prefix
        self.style = style
        self.counter = 0
        self.name_map: Dict[str, str] = {}
        self._used_names: Set[str] = set()
        self.method_names: Set[str] = set()
        self.class_attributes: Set[str] = set()

    def _generate_random_name(self, length: int = 8) -> str:
        chars = string.ascii_letters + string.digits
        while True:
            name = self.prefix + random.choice(string.ascii_letters)
            name += ''.join(random.choices(chars, k=length - 1))
            if name not in self._used_names:
                self._used_names.add(name)
                return name

    def _generate_hex_name(self) -> str:
        self.counter += 1
        name = f"{self.prefix}x{hex(self.counter)[2:]}"
        self._used_names.add(name)
        return name

    def _generate_hash_name(self, original: str) -> str:
        h = hashlib.md5(original.encode()).hexdigest()[:8]
        name = f"{self.prefix}{h}"
        if name in self._used_names:
            name = f"{name}_{self.counter}"
            self.counter += 1
        self._used_names.add(name)
        return name

    def get_name(self, original: str) -> str:
        if original in self.name_map:
            return self.name_map[original]

        if self.style == "random":
            new_name = self._generate_random_name()
        elif self.style == "hex":
            new_name = self._generate_hex_name()
        elif self.style == "hash":
            new_name = self._generate_hash_name(original)
        else:
            new_name = self._generate_random_name()

        self.name_map[original] = new_name
        return new_name

    def register_method(self, name: str) -> None:
        self.method_names.add(name)

    def register_class_attribute(self, name: str) -> None:
        self.class_attributes.add(name)

    def is_known_member(self, name: str) -> bool:
        return name in self.method_names or name in self.class_attributes

    def export_mapping(self) -> Dict[str, str]:
        return dict(self.name_map)

    def import_mapping(self, mapping: Dict[str, str]) -> None:
        self.name_map.update(mapping)
        self._used_names.update(mapping.values())

    def pre_register_name(self, original: str) -> str:
        return self.get_name(original)


class DefinitionCollector(ast.NodeVisitor):
    """
    AST visitor that collects all definitions.
    """

    RESERVED = ReservedNames.CORE_RESERVED | ReservedNames.BUILTINS
    BUILTINS = set(dir(__builtins__) if isinstance(__builtins__, dict) else dir(__builtins__))

    def __init__(self, name_generator: NameGenerator, exclude_names: Optional[Set[str]] = None):
        self.name_gen = name_generator
        self.exclude = self.RESERVED | self.BUILTINS | (exclude_names or set())
        self._in_class = False

    def _should_collect(self, name: str) -> bool:
        """Determines if an identifier should be collected for renaming."""
        is_magic = name.startswith('__') and name.endswith('__')
        return not is_magic and name not in self.exclude

    def _register(self, name: str) -> None:
        if self._should_collect(name):
            self.name_gen.pre_register_name(name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._register(node.name)
        if self._in_class:
            self.name_gen.register_method(node.name)
        for arg in node.args.args:
            if arg.arg not in ('self', 'cls'):
                self._register(arg.arg)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._register(node.name)
        if self._in_class:
            self.name_gen.register_method(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._register(node.name)
        prev_in_class = self._in_class
        self._in_class = True
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        self._register(target.id)
                        self.name_gen.register_class_attribute(target.id)
        self.generic_visit(node)
        self._in_class = prev_in_class

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._register(target.id)
            elif isinstance(target, ast.Attribute):
                if (isinstance(target.value, ast.Name) and
                    target.value.id in ('self', 'cls')):
                    self._register(target.attr)
                    self.name_gen.register_class_attribute(target.attr)
        self.generic_visit(node)


@TransformerRegistry.register("name_obfuscator")
class NameTransformer(BaseTransformer):
    """
    Transformer for renaming identifiers.
    """

    def __init__(
        self,
        name_generator: Optional[NameGenerator] = None,
        exclude_names: Optional[Set[str]] = None,
        rename_methods: bool = True,
        rename_attributes: bool = True,
        **kwargs
    ):
        self.name_gen = name_generator or NameGenerator()
        self.exclude_names = exclude_names
        self.rename_methods = rename_methods
        self.rename_attributes = rename_attributes

    def transform(self, source: str, context: Optional['TransformationContext'] = None) -> str:
        tree = self._parse_source(source)
        transformer = NameObfuscatorInternal(
            self.name_gen,
            exclude_names=self.exclude_names,
            rename_methods=self.rename_methods,
            rename_attributes=self.rename_attributes
        )
        tree = transformer.visit(tree)
        return self._unparse_tree(tree)


class NameObfuscatorInternal(ast.NodeTransformer):
    """
    Internal AST transformer for name renaming.
    """

    BUILTINS = set(dir(__builtins__) if isinstance(__builtins__, dict) else dir(__builtins__))
    RESERVED = ReservedNames.get_all_reserved()

    def __init__(
        self,
        name_generator: NameGenerator,
        exclude_names: Optional[Set[str]] = None,
        rename_methods: bool = True,
        rename_attributes: bool = True
    ):
        self.name_gen = name_generator
        self.exclude = self.RESERVED | self.BUILTINS | (exclude_names or set())
        self.import_names: Set[str] = set()
        self.rename_methods = rename_methods
        self.rename_attributes = rename_attributes
        self._in_class: bool = False
        self._instance_attributes: Set[str] = set()

    def _should_rename(self, name: str) -> bool:
        """Determines if an identifier should be renamed."""
        is_magic = name.startswith('__') and name.endswith('__')
        return not is_magic and name not in self.exclude and name not in self.import_names

    def _rename(self, name: str) -> str:
        if self._should_rename(name):
            return self.name_gen.get_name(name)
        return name

    def visit_Import(self, node: ast.Import) -> ast.Import:
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split('.')[0]
            self.import_names.add(name)
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        for alias in node.names:
            original_name = alias.name
            if original_name == '*':
                continue
            if original_name in self.name_gen.name_map:
                alias.name = self.name_gen.name_map[original_name]
                if alias.asname:
                    alias.asname = self._rename(alias.asname)
            else:
                name = alias.asname if alias.asname else alias.name
                self.import_names.add(name)
        return node

    def _rename_arguments(self, args: ast.arguments) -> None:
        for arg in args.args:
            if arg.arg not in ('self', 'cls'):
                arg.arg = self._rename(arg.arg)
        for arg in args.posonlyargs:
            if arg.arg not in ('self', 'cls'):
                arg.arg = self._rename(arg.arg)
        for arg in args.kwonlyargs:
            arg.arg = self._rename(arg.arg)
        if args.vararg:
            args.vararg.arg = self._rename(args.vararg.arg)
        if args.kwarg:
            args.kwarg.arg = self._rename(args.kwarg.arg)

    def _handle_func(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Union[ast.FunctionDef, ast.AsyncFunctionDef]:
        """Shared logic for function name and argument renaming."""
        if self._in_class and self.rename_methods:
            self.name_gen.register_method(node.name)
            node.name = self._rename(node.name)
        elif not self._in_class:
            node.name = self._rename(node.name)
        self._rename_arguments(node.args)
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        return self._handle_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        return self._handle_func(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        node.name = self._rename(node.name)
        prev_in_class = self._in_class
        self._in_class = True
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        self.name_gen.register_class_attribute(target.id)
                        self._instance_attributes.add(target.id)
        self.generic_visit(node)
        self._in_class = prev_in_class
        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        node.id = self._rename(node.id)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute:
        self.generic_visit(node)
        if not self.rename_attributes:
            return node
        attr_name = node.attr
        if attr_name.startswith('__') and attr_name.endswith('__') or attr_name in self.exclude:
            return node
        
        is_self_cls = (isinstance(node.value, ast.Name) and node.value.id in ('self', 'cls'))
        
        if is_self_cls:
            if isinstance(node.ctx, ast.Store):
                self._instance_attributes.add(attr_name)
                self.name_gen.register_class_attribute(attr_name)
            if attr_name in self._instance_attributes or self.name_gen.is_known_member(attr_name):
                node.attr = self._rename(attr_name)
        elif self.name_gen.is_known_member(attr_name):
            node.attr = self._rename(attr_name)
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if (isinstance(target.value, ast.Name) and
                    target.value.id in ('self', 'cls')):
                    self._instance_attributes.add(target.attr)
                    self.name_gen.register_class_attribute(target.attr)
        self.generic_visit(node)
        return node
