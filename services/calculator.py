from langchain.tools import tool
import math

class Calculator:
    """
    Extended calculator for basic and advanced arithmetic operations.
    """

    @staticmethod
    @tool
    def add(first_number: int, second_number: int) -> int:
        """Add two integers."""
        return first_number + second_number

    @staticmethod
    @tool
    def subtract(minuend: int, subtrahend: int) -> int:
        """Subtract two integers."""
        return minuend - subtrahend

    @staticmethod
    @tool
    def multiply(factor1: int, factor2: int) -> int:
        """Multiply two integers."""
        return factor1 * factor2

    @staticmethod
    @tool
    def divide(numerator: int, denominator: int) -> float:
        """Divide two integers."""
        if denominator == 0:
            raise ValueError("Denominator cannot be zero.")
        return numerator / denominator

    @staticmethod
    @tool
    def floor_divide(numerator: int, denominator: int) -> int:
        """Perform floor division."""
        if denominator == 0:
            raise ValueError("Denominator cannot be zero.")
        return numerator // denominator

    @staticmethod
    @tool
    def modulus(dividend: int, divisor: int) -> int:
        """Find the remainder of division."""
        if divisor == 0:
            raise ValueError("Divisor cannot be zero.")
        return dividend % divisor

    @staticmethod
    @tool
    def power(base: float, exponent: float) -> float:
        """Raise base to the power of exponent."""
        return base ** exponent

    @staticmethod
    @tool
    def sqrt(value: float) -> float:
        """Calculate the square root."""
        if value < 0:
            raise ValueError("Cannot take square root of a negative number.")
        return math.sqrt(value)

    @staticmethod
    @tool
    def absolute(value: float) -> float:
        """Return the absolute value."""
        return abs(value)

    @staticmethod
    @tool
    def log(value: float, base: float = math.e) -> float:
        """Calculate logarithm with optional base (default is natural log)."""
        if value <= 0:
            raise ValueError("Logarithm undefined for non-positive values.")
        return math.log(value, base)
