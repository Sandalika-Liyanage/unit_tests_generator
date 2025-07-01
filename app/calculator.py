"""
Calculator module providing basic arithmetic operations
"""

class Calculator:
    """Class implementing basic calculator operations"""
    
    @staticmethod
    def add(a: float, b: float) -> float:
        """Add two numbers
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            float: Sum of a and b
        """
        return a + b

    @staticmethod
    def subtract(a: float, b: float) -> float:
        """Subtract second number from first
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            float: Difference of a and b
        """
        return a - b

    @staticmethod
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            float: Product of a and b
        """
        return a * b

    @staticmethod
    def divide(a: float, b: float) -> float:
        """Divide first number by second
        
        Args:
            a: Numerator
            b: Denominator
            
        Returns:
            float: Quotient of a divided by b
            
        Raises:
            ZeroDivisionError: If b is zero
        """
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b

    @staticmethod
    def power(base: float, exponent: float) -> float:
        """Raise base to the power of exponent
        
        Args:
            base: Base number
            exponent: Exponent
            
        Returns:
            float: Result of base raised to exponent
        """
        return base ** exponent

    @staticmethod
    def sqrt(number: float) -> float:
        """Calculate square root of a number
        
        Args:
            number: Number to find square root of
            
        Returns:
            float: Square root of the number
            
        Raises:
            ValueError: If number is negative
        """
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return number ** 0.5
