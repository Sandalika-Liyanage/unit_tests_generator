
import pytest
from app.calculator import Calculator

class TestCalculator:

    @pytest.mark.parametrize("a,b,expected", [
        (1, 2, 3),
        (-1, 2, 1),
        (0, 0, 0),
        (1.5, 2.5, 4.0),
        (-1.5, -2.5, -4.0)
    ])
    def test_add(self, a, b, expected):
        assert Calculator.add(a, b) == expected

    @pytest.mark.parametrize("a,b,expected", [
        (5, 3, 2),
        (0, 5, -5),
        (-4, -2, -2),
        (2.5, 1.2, 1.3),
        (-1.2, 1.2, -2.4)
    ])
    def test_subtract(self, a, b, expected):
        assert Calculator.subtract(a, b) == expected

    @pytest.mark.parametrize("a,b,expected", [
        (2, 3, 6),
        (-2, 3, -6),
        (0, 4, 0),
        (1.5, 2, 3.0),
        (-1.5, -2, 3.0)
    ])
    def test_multiply(self, a, b, expected):
        assert Calculator.multiply(a, b) == expected

    @pytest.mark.parametrize("a,b,expected", [
        (6, 3, 2),
        (5, 2, 2.5),
        (-6, 2, -3),
        (3.0, 1.5, 2.0),
        (-4, -2, 2.0)
    ])
    def test_divide(self, a, b, expected):
        assert Calculator.divide(a, b) == expected

    def test_divide_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            Calculator.divide(5, 0)

    @pytest.mark.parametrize("base,exponent,expected", [
        (2, 3, 8),
        (5, 0, 1),
        (2, -1, 0.5),
        (9, 0.5, 3),
        (0, 5, 0),
        (-2, 2, 4),
    ])
    def test_power(self, base, exponent, expected):
        result = Calculator.power(base, exponent)
        assert result == pytest.approx(expected)

    @pytest.mark.parametrize("number,expected", [
        (9, 3),
        (16, 4),
        (0, 0),
        (1.21, 1.1),
        (10000, 100),
    ])
    def test_sqrt(self, number, expected):
        result = Calculator.sqrt(number)
        assert result == pytest.approx(expected)

    def test_sqrt_negative(self):
        with pytest.raises(ValueError):
            Calculator.sqrt(-1)
