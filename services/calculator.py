from langchain.tools import tool

class Calculator:
    """
    Simple calculator for basic arithmetic operations.
    """
    @staticmethod
    @tool
    def add(first_number: int, second_number: int) -> int:
        """
        Add two integers.

        Args:
            a (int): The first integer.
            b (int): The second integer.

        Returns:
            int: The sum of a and b.
        """
        return first_number + second_number

    @staticmethod
    @tool
    def multiply(factor1: int, factor2: int) -> int:
        """
        Multiply two integers.

        Args:
            a (int): The first integer.
            b (int): The second integer.

        Returns:
            int: The product of a and b.
        """
        return factor1 * factor2

    @staticmethod
    @tool
    def divide(numerator: int, denominator: int) -> float:
        """
        Divide two integers.

        Args:
            a (int): The numerator.
            b (int): The denominator (must not be 0).

        Returns:
            float: The result of division.
        """
        if denominator == 0:
            raise ValueError("Denominator cannot be zero.")
        return numerator / denominator

    @staticmethod
    @tool
    def subtract(initial_value: int, value_to_subtract: int) -> int:
        """
        Subtract two integers.

        Args:
            a (int): The first integer.
            b (int): The second integer.

        Returns:
            int: The subtraction of a and b.
        """
        return initial_value - value_to_subtract
