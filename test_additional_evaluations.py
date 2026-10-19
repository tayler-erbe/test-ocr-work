from decimal import Decimal
import unittest
from additional_evaluations import safe_program

class SafeArithmetic(unittest.TestCase):
    def test_multistep_money_and_ratio(self):
        steps=[{"op":"subtract","a":"5829","b":"5735"},{"op":"divide","a":"#0","b":"5735"}]
        self.assertEqual(safe_program(steps,'Revenue 5829 vs 5735'),Decimal(94)/Decimal(5735))

    def test_invented_operand_rejected(self):
        with self.assertRaises(ValueError):safe_program([{"op":"add","a":"9000","b":"1"}], 'Fee 5000')

    def test_executable_expression_rejected(self):
        with self.assertRaises(Exception):safe_program([{"op":"add","a":"__import__('os')","b":"1"}], '1')

    def test_nonfinite_and_zero_division_rejected(self):
        for steps in [[{"op":"divide","a":"1","b":"0"}],[{"op":"add","a":"NaN","b":"1"}]]:
            with self.assertRaises(ValueError):safe_program(steps,'1 0')

    def test_forward_reference_and_unknown_operation_rejected(self):
        for step in [{"op":"add","a":"#0","b":"1"},{"op":"exec","a":"1","b":"1"}]:
            with self.assertRaises(ValueError):safe_program([step],'1')

if __name__=='__main__':unittest.main()
