"""Operand parsing utilities for assembly instructions."""

import re
from typing import Tuple
from CompilerComponents.Exceptions import OperandError


class OperandType:
    """Enumeration of operand types."""
    IMMEDIATE = 'immediate'
    DIRECT_ADDRESS = 'direct_address'
    REGISTER = 'register'
    SYMBOL = 'symbol'


class OperandParser:
    """
    Parser for assembly instruction operands.
    
    Handles parsing of different operand formats:
    - Immediate values: #42, #0xFF
    - Direct addresses: [0x1000], [#100]
    - Register indirect: [REA]
    - Registers: REA, REB, etc.
    - Symbols: label_name, function_start
    """
    
    def __init__(self, pRegisters):
        """
        Initialize the operand parser.
        
        Args:
            registers: Register class with register definitions
        """
        self.registers = pRegisters
    
    def IsRegister(self, pToken: str) -> bool:
        """
        Check if a token is a valid register name.
        
        Args:
            token: Token to check
            
        Returns:
            True if token is a register name
        """
        return hasattr(self.registers, pToken.upper())
    
    def ParseRegister(self, pToken: str) -> int:
        """
        Parse a register name to its numeric value.
        
        Args:
            token: Register name
            
        Returns:
            Register numeric value
            
        Raises:
            OperandError: If register name is invalid
        """
        try:
            return getattr(self.registers, pToken.upper())
        except AttributeError:
            raise OperandError(f"Invalid register: {pToken}")
    
    def ParseOperand(self, pOperand: str) -> Tuple[str, int | str]:
        """
        Parse an operand string and determine its type and value.
        
        Args:
            operand: Operand string to parse
            
        Returns:
            Tuple of (operand_type, value)
            - For immediate/address/register: (type, int_value)
            - For symbols: (type, symbol_name)
            
        Raises:
            OperandError: If operand format is invalid
        """
        operand = pOperand.strip()
        
        # Immediate value: #42, #0xFF
        if operand.startswith('#'):
            return self._parse_immediate(operand)
        
        # Direct address or register indirect: [addr] or [REG]
        elif operand.startswith('[') and operand.endswith(']'):
            return self._parse_bracketed(operand)
        
        # Register: REA, REB, etc.
        elif self.IsRegister(operand):
            return OperandType.REGISTER, self.ParseRegister(operand)
        
        # Symbol: label_name, function_start
        elif re.match(r'^[A-Za-z_][A-Za-z0-9_.]*$', operand):
            return OperandType.SYMBOL, operand
        
        else:
            raise OperandError(f"Unrecognized operand format: {operand}")
    
    def _ParseImmediate(self, pOperand: str) -> Tuple[str, int]:
        """Parse immediate value format."""
        try:
            value = int(pOperand[1:], 0)
            return OperandType.IMMEDIATE, value
        except ValueError:
            raise OperandError(f"Invalid immediate value: {pOperand}")
    
    def _ParseBracketed(self, pOperand: str) -> Tuple[str, int]:
        """Parse bracketed format (direct address or register indirect)."""
        inner = pOperand[1:-1].strip()
        
        # Register indirect: [REA]
        if self.IsRegister(inner):
            return OperandType.REGISTER, self.ParseRegister(inner)
        
        # Direct address: [0x1000] or [#100]
        if inner.startswith('#'):
            inner = inner[1:]
        
        try:
            address = int(inner, 0)
            return OperandType.DIRECT_ADDRESS, address
        except ValueError:
            raise OperandError(f"Invalid direct address: {pOperand}")
