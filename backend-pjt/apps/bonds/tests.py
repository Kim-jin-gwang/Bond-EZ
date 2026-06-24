from types import SimpleNamespace

from django.test import SimpleTestCase

from .utils import generate_rule_based_summary


class RuleBasedSummaryTests(SimpleTestCase):
    def make_bond(self, **overrides):
        values = {
            "company_name": "테스트회사",
            "bond_type": "회사채",
            "coupon_rate": 4.25,
            "seniority": "선순위",
            "guarantee_status": "무보증",
            "credit_rating": "BBB+",
            "maturity_date": "2027-06-24",
            "call_put_option": "NONE",
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_bbb_is_described_as_investment_grade(self):
        summary = generate_rule_based_summary(self.make_bond())

        self.assertIn("투자적격 등급", summary[1])
        self.assertNotIn("투자주의 등급", summary[1])

    def test_missing_rating_is_not_described_as_speculative(self):
        summary = generate_rule_based_summary(self.make_bond(credit_rating=None))

        self.assertIn("신용등급 정보가 없어", summary[1])
        self.assertNotIn("투기등급", summary[1])

    def test_call_and_put_are_both_described(self):
        summary = generate_rule_based_summary(self.make_bond(call_put_option="CALL+PUT"))

        self.assertIn("콜옵션", summary[2])
        self.assertIn("풋옵션", summary[2])

    def test_no_option_does_not_make_suitability_claim(self):
        summary = generate_rule_based_summary(self.make_bond(maturity_date="2099-06-24"))

        self.assertIn("등록된 중도 조기상환 옵션은 없습니다", summary[2])
        self.assertNotIn("보유하기 적합", summary[2])

    def test_matured_bond_requires_status_confirmation(self):
        summary = generate_rule_based_summary(self.make_bond(maturity_date="2020-06-24"))

        self.assertIn("이미 지났습니다", summary[2])
        self.assertIn("상환 완료 여부", summary[2])
