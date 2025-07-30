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
            first_number (int): The first integer.
            second_number (int): The second integer.

        Returns:
            int: The sum of first_number and second_number.
        """
        return first_number + second_number

    @staticmethod
    @tool
    def multiply(factor1: int, factor2: int) -> int:
        """
        Multiply two integers.

        Args:
            factor1 (int): The first integer.
            factor2 (int): The second integer.

        Returns:
            int: The product of factor1 and factor2.
        """
        return factor1 * factor2

    @staticmethod
    @tool
    def divide(numerator: int, denominator: int) -> float:
        """
        Divide two integers.

        Args:
            numerator (int): The numerator.
            denominator (int): The denominator (must not be 0).

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
            initial_value (int): The first integer.
            value_to_subtract (int): The second integer.

        Returns:
            int: The subtraction of initial_value and value_to_subtract.
        """
        return initial_value - value_to_subtract
