# -*- coding: utf-8 -*-
"""
Instruction-Level Virtualization for PyObfuscator.

Compiles Python AST into custom VM bytecode and injects a VM interpreter.
"""

import ast
import random
import struct
from typing import List, Dict, Any, Optional

from .base import BaseTransformer
from ..registry import TransformerRegistry

class VMCompiler:
    """
    Compiles simple Python expressions and statements into custom VM bytecode.
    """
    
    # Opcode definitions (must match runtime_protection.py)
    OP_PUSH  = 0x01
    OP_POP   = 0x02
    OP_DUP   = 0x03
    OP_SWAP  = 0x04
    OP_ADD   = 0x10
    OP_SUB   = 0x11
    OP_MUL   = 0x12
    OP_DIV   = 0x13
    OP_XOR   = 0x20
    OP_AND   = 0x21
    OP_OR    = 0x22
    OP_LOAD  = 0x30
    OP_STORE = 0x31
    OP_HALT  = 0xF0

    def __init__(self):
        self.bytecode = bytearray()
        self.symbol_table: Dict[str, int] = {}
        self.next_mem_addr = 0

    def _get_addr(self, name: str) -> int:
        if name not in self.symbol_table:
            self.symbol_table[name] = self.next_mem_addr
            self.next_mem_addr += 1
        return self.symbol_table[name]

    def compile_node(self, node: ast.AST):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, bool)):
            val = int(node.value)
            self.bytecode.append(self.OP_PUSH)
            self.bytecode.extend(struct.pack('<I', val & 0xFFFFFFFF))
        
        elif isinstance(node, ast.Name):
            addr = self._get_addr(node.id)
            self.bytecode.append(self.OP_PUSH)
            self.bytecode.extend(struct.pack('<I', addr))
            self.bytecode.append(self.OP_LOAD)
            
        elif isinstance(node, ast.BinOp):
            self.compile_node(node.left)
            self.compile_node(node.right)
            if isinstance(node.op, ast.Add): self.bytecode.append(self.OP_ADD)
            elif isinstance(node.op, ast.Sub): self.bytecode.append(self.OP_SUB)
            elif isinstance(node.op, ast.Mult): self.bytecode.append(self.OP_MUL)
            elif isinstance(node.op, ast.BitXor): self.bytecode.append(self.OP_XOR)
            
        elif isinstance(node, ast.Assign):
            # Target must be a Name for this simple VM
            if isinstance(node.targets[0], ast.Name):
                addr = self._get_addr(node.targets[0].id)
                self.bytecode.append(self.OP_PUSH)
                self.bytecode.extend(struct.pack('<I', addr))
                self.compile_node(node.value)
                self.bytecode.append(self.OP_STORE)

        elif isinstance(node, ast.Return):
            if node.value:
                addr = self._get_addr("__return__")
                self.bytecode.append(self.OP_PUSH)
                self.bytecode.extend(struct.pack('<I', addr))
                self.compile_node(node.value)
                self.bytecode.append(self.OP_STORE)
            self.bytecode.append(self.OP_HALT)

    def compile_function(self, body: List[ast.stmt]) -> bytes:
        for stmt in body:
            self.compile_node(stmt)
        if not self.bytecode or self.bytecode[-1] != self.OP_HALT:
            self.bytecode.append(self.OP_HALT)
        return bytes(self.bytecode)

@TransformerRegistry.register("vm_transformer")
class VirtualMachineTransformer(BaseTransformer):
    """
    Targeted virtualization transformer.
    Replaces function bodies with a VM execution call.
    """
    
    def __init__(self, intensity: int = 1, **kwargs):
        self.intensity = intensity

    def transform(self, source: str, context: Optional[Any] = None) -> str:
        tree = self._parse_source(source)
        tree = self.visit(tree)
        return self._unparse_tree(tree)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        # Only virtualize functions that are simple enough for our current VM
        # and meet the intensity threshold
        if len(node.body) < 2 or any(isinstance(s, (ast.If, ast.While, ast.For)) for s in node.body):
            return node
            
        if random.random() > 0.3 * self.intensity:
            return node

        # Check for function arguments and add them to compiler symbol table
        compiler = VMCompiler()
        for i, arg in enumerate(node.args.args):
            addr = compiler._get_addr(arg.arg)
            # We'll need to initialize these in the new_body

        try:
            bytecode = compiler.compile_function(node.body)
        except Exception:
            return node

        bytecode_hex = bytecode.hex()
        
        new_body = [
            ast.Import(names=[ast.alias(name='pyobfuscator.runtime_protection', asname='_vm_mod')]),
            ast.Assign(
                targets=[ast.Name(id='_vm', ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id='_vm_mod', ctx=ast.Load()), attr='VM', ctx=ast.Load()),
                    args=[], keywords=[]
                )
            )
        ]

        # Initialize function arguments in VM memory
        for i, arg in enumerate(node.args.args):
            addr = compiler.symbol_table[arg.arg]
            new_body.append(
                ast.Assign(
                    targets=[ast.Subscript(
                        value=ast.Attribute(value=ast.Name(id='_vm', ctx=ast.Load()), attr='_mem', ctx=ast.Load()),
                        slice=ast.Constant(value=addr),
                        ctx=ast.Store()
                    )],
                    value=ast.Name(id=arg.arg, ctx=ast.Load())
                )
            )
        
        # Execute VM
        new_body.append(
            ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id='_vm', ctx=ast.Load()), attr='execute', ctx=ast.Load()),
                    args=[ast.Constant(value=bytes.fromhex(bytecode_hex)), ast.Constant(value=b'')],
                    keywords=[]
                )
            )
        )
        
        # Map back local variables if needed, and handle return
        has_return = "__return__" in compiler.symbol_table
        
        for name, addr in compiler.symbol_table.items():
            if name == "__return__":
                continue
            new_body.append(
                ast.Assign(
                    targets=[ast.Name(id=name, ctx=ast.Store())],
                    value=ast.Subscript(
                        value=ast.Attribute(value=ast.Name(id='_vm', ctx=ast.Load()), attr='_mem', ctx=ast.Load()),
                        slice=ast.Constant(value=addr),
                        ctx=ast.Load()
                    )
                )
            )

        if has_return:
            addr = compiler.symbol_table["__return__"]
            new_body.append(
                ast.Return(
                    value=ast.Subscript(
                        value=ast.Attribute(value=ast.Name(id='_vm', ctx=ast.Load()), attr='_mem', ctx=ast.Load()),
                        slice=ast.Constant(value=addr),
                        ctx=ast.Load()
                    )
                )
            )

        node.body = new_body
        return node
