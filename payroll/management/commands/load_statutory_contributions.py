from decimal import Decimal
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from payroll.models import (
    SSSContributionBracket,
    StatutoryContributionRule,
    WithholdingTaxBracket,
)


class Command(BaseCommand):
    help = "Load Philippine statutory contribution and withholding tax schedules."

    @transaction.atomic
    def handle(self, *args, **options):
        self.load_sss_brackets()
        self.load_statutory_rules()
        self.load_withholding_tax_brackets()

        self.stdout.write(
            self.style.SUCCESS(
                "All available statutory contribution and tax schedules loaded successfully."
            )
        )

    def load_sss_brackets(self):
        effective_date = date(2025, 1, 1)
        created_count = 0
        updated_count = 0

        for index in range(61):
            monthly_salary_credit = Decimal("5000") + (
                Decimal("500") * index
            )

            if index == 0:
                minimum_compensation = Decimal("0")
                maximum_compensation = Decimal("5249.99")
            else:
                minimum_compensation = Decimal("5250") + (
                    Decimal("500") * (index - 1)
                )

                if index == 60:
                    maximum_compensation = None
                else:
                    maximum_compensation = (
                        minimum_compensation + Decimal("499.99")
                    )

            regular_salary_credit = min(
                monthly_salary_credit,
                Decimal("20000"),
            )

            mpf_salary_credit = max(
                monthly_salary_credit - Decimal("20000"),
                Decimal("0"),
            )

            employee_contribution = (
                regular_salary_credit * Decimal("0.05")
            )

            employer_contribution = (
                regular_salary_credit * Decimal("0.10")
            )

            employee_mpf_contribution = (
                mpf_salary_credit * Decimal("0.05")
            )

            employer_mpf_contribution = (
                mpf_salary_credit * Decimal("0.10")
            )

            employer_ec_contribution = (
                Decimal("10.00")
                if monthly_salary_credit <= Decimal("14500")
                else Decimal("30.00")
            )

            _, created = SSSContributionBracket.objects.update_or_create(
                minimum_compensation=minimum_compensation,
                effective_date=effective_date,
                defaults={
                    "maximum_compensation": maximum_compensation,
                    "monthly_salary_credit": monthly_salary_credit,
                    "employee_contribution": employee_contribution,
                    "employee_mpf_contribution": employee_mpf_contribution,
                    "employer_contribution": employer_contribution,
                    "employer_mpf_contribution": employer_mpf_contribution,
                    "employer_ec_contribution": employer_ec_contribution,
                    "is_active": True,
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"SSS schedule loaded. Created: {created_count}, "
                f"Updated: {updated_count}"
            )
        )

    def load_statutory_rules(self):
        rules = [
            {
                "name": "PhilHealth",
                "employee_rate": Decimal("2.5"),
                "employer_rate": Decimal("2.5"),
                "minimum_monthly_salary": Decimal("10000"),
                "maximum_monthly_salary": Decimal("100000"),
                "maximum_contribution_salary": Decimal("100000"),
                "effective_date": date(2025, 1, 1),
            },
            {
                "name": "Pag-IBIG",
                "employee_rate": Decimal("1"),
                "employer_rate": Decimal("2"),
                "minimum_monthly_salary": Decimal("0"),
                "maximum_monthly_salary": Decimal("1500"),
                "maximum_contribution_salary": Decimal("10000"),
                "effective_date": date(2024, 2, 1),
            },
            {
                "name": "Pag-IBIG",
                "employee_rate": Decimal("2"),
                "employer_rate": Decimal("2"),
                "minimum_monthly_salary": Decimal("1500.01"),
                "maximum_monthly_salary": None,
                "maximum_contribution_salary": Decimal("10000"),
                "effective_date": date(2024, 2, 1),
            },
        ]

        created_count = 0
        updated_count = 0

        for rule in rules:
            _, created = StatutoryContributionRule.objects.update_or_create(
                name=rule["name"],
                minimum_monthly_salary=rule["minimum_monthly_salary"],
                effective_date=rule["effective_date"],
                defaults={
                    "employee_rate": rule["employee_rate"],
                    "employer_rate": rule["employer_rate"],
                    "maximum_monthly_salary": rule["maximum_monthly_salary"],
                    "maximum_contribution_salary": rule[
                        "maximum_contribution_salary"
                    ],
                    "is_active": True,
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"PhilHealth and Pag-IBIG rules loaded. "
                f"Created: {created_count}, Updated: {updated_count}"
            )
        )

    def load_withholding_tax_brackets(self):
        effective_date = date(2023, 1, 1)

        tax_tables = {
            "Daily": [
                (Decimal("0"), Decimal("685"), Decimal("0"), Decimal("0")),
                (Decimal("685.01"), Decimal("1095"), Decimal("0"), Decimal("0.15")),
                (Decimal("1096"), Decimal("2191"), Decimal("61.65"), Decimal("0.20")),
                (Decimal("2192"), Decimal("5478"), Decimal("280.85"), Decimal("0.25")),
                (Decimal("5479"), Decimal("21917"), Decimal("1102.60"), Decimal("0.30")),
                (Decimal("21918"), None, Decimal("6034.30"), Decimal("0.35")),
            ],
            "Weekly": [
                (Decimal("0"), Decimal("4808"), Decimal("0"), Decimal("0")),
                (Decimal("4808.01"), Decimal("7691"), Decimal("0"), Decimal("0.15")),
                (Decimal("7692"), Decimal("15384"), Decimal("432.60"), Decimal("0.20")),
                (Decimal("15385"), Decimal("38461"), Decimal("1971.20"), Decimal("0.25")),
                (Decimal("38462"), Decimal("153845"), Decimal("7740.45"), Decimal("0.30")),
                (Decimal("153846"), None, Decimal("42355.65"), Decimal("0.35")),
            ],
            "Semi-monthly": [
                (Decimal("0"), Decimal("10417"), Decimal("0"), Decimal("0")),
                (Decimal("10417.01"), Decimal("16666"), Decimal("0"), Decimal("0.15")),
                (Decimal("16667"), Decimal("33332"), Decimal("937.50"), Decimal("0.20")),
                (Decimal("33333"), Decimal("83332"), Decimal("4270.70"), Decimal("0.25")),
                (Decimal("83333"), Decimal("333332"), Decimal("16770.70"), Decimal("0.30")),
                (Decimal("333333"), None, Decimal("91770.70"), Decimal("0.35")),
            ],
            "Monthly": [
                (Decimal("0"), Decimal("20833"), Decimal("0"), Decimal("0")),
                (Decimal("20833.01"), Decimal("33332"), Decimal("0"), Decimal("0.15")),
                (Decimal("33333"), Decimal("66666"), Decimal("1875.00"), Decimal("0.20")),
                (Decimal("66667"), Decimal("166666"), Decimal("8541.80"), Decimal("0.25")),
                (Decimal("166667"), Decimal("666666"), Decimal("33541.80"), Decimal("0.30")),
                (Decimal("666667"), None, Decimal("183541.80"), Decimal("0.35")),
            ],
        }

        created_count = 0
        updated_count = 0

        for frequency, brackets in tax_tables.items():
            for minimum, maximum, base_tax, rate in brackets:
                _, created = WithholdingTaxBracket.objects.update_or_create(
                    pay_frequency=frequency,
                    minimum_taxable_income=minimum,
                    effective_date=effective_date,
                    defaults={
                        "maximum_taxable_income": maximum,
                        "base_tax": base_tax,
                        "tax_rate": rate,
                        "is_active": True,
                    },
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"BIR withholding tax brackets loaded. "
                f"Created: {created_count}, Updated: {updated_count}"
            )
        )
