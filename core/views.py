from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Customer, Loan
from .serializers import CustomerSerializer, LoanSerializer, CheckEligibilitySerializer, LoanDetailSerializer, LoanListItemSerializer
from .utils import calculate_emi
from datetime import datetime


class RegisterCustomer(APIView):
    def post(self, request):
        data = request.data
        salary = data["monthly_income"]
        approved_limit = round((36 * salary) / 100000) * 100000
        customer = Customer.objects.create(
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone_number=data["phone_number"],
            age=data["age"],
            monthly_salary=salary,
            approved_limit=approved_limit,
        )
        return Response(CustomerSerializer(customer).data)


class CheckEligibility(APIView):
    def post(self, request):
        serializer = CheckEligibilitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        data = serializer.validated_data
        customer_id = data["customer_id"]
        loan_amount = data["loan_amount"]
        interest_rate = data["interest_rate"]
        tenure = data["tenure"]

        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # 1. If sum of current loans > approved limit, credit score = 0
        current_loans_sum = sum(
            Loan.objects.filter(customer=customer).values_list("loan_amount", flat=True)
        )
        if current_loans_sum > customer.approved_limit:
            credit_score = 0
        else:
            # Calculate credit score (out of 100)
            loans = Loan.objects.filter(customer=customer)
            total_loans = loans.count()
            paid_on_time = 0
            current_year = datetime.now().year
            activity_this_year = 0
            approved_volume = 0
            for loan in loans:
                if loan.emis_paid_on_time >= loan.tenure:
                    paid_on_time += 1
                if loan.start_date.year == current_year:
                    activity_this_year += 1
                approved_volume += loan.loan_amount
            # Assign points (simple distribution, can be adjusted)
            score = 0
            if total_loans > 0:
                score += min(
                    40, 40 * paid_on_time / total_loans
                )  # Past loans paid on time
                score += min(
                    15, 15 * total_loans / 5
                )  # No of loans taken in past (max 5 loans)
                score += 15 if activity_this_year > 0 else 0  # Activity in current year
                score += min(
                    15, 15 * approved_volume / customer.approved_limit
                )  # Approved volume
                score += (
                    15 if customer.current_debt < 0.5 * customer.approved_limit else 0
                )  # Debt vs limit
            credit_score = round(score, 2)

        # 2. If sum of all current EMIs > 50% of monthly salary, do not approve
        current_emis = sum(
            Loan.objects.filter(customer=customer).values_list(
                "monthly_installment", flat=True
            )
        )
        if current_emis > 0.5 * customer.monthly_salary:
            approval = False
            corrected_interest_rate = max(16.0, interest_rate)
        elif credit_score > 50:
            approval = True
            corrected_interest_rate = interest_rate
        elif 50 >= credit_score > 30:
            if interest_rate > 12:
                approval = True
                corrected_interest_rate = interest_rate
            else:
                approval = False
                corrected_interest_rate = 12.01
        elif 30 >= credit_score > 10:
            if interest_rate > 16:
                approval = True
                corrected_interest_rate = interest_rate
            else:
                approval = False
                corrected_interest_rate = 16.01
        else:
            approval = False
            corrected_interest_rate = max(16.0, interest_rate)

        # If interest rate does not match slab, correct it in the response
        if credit_score > 50:
            min_rate = 0
        elif 50 >= credit_score > 30:
            min_rate = 12
        elif 30 >= credit_score > 10:
            min_rate = 16
        else:
            min_rate = 16
        if interest_rate < min_rate:
            corrected_interest_rate = min_rate

        # Calculate monthly installment
        monthly_installment = calculate_emi(
            loan_amount, corrected_interest_rate, tenure
        )

        response = {
            "customer_id": customer_id,
            "approval": approval,
            "interest_rate": interest_rate,
            "corrected_interest_rate": corrected_interest_rate,
            "tenure": tenure,
            "monthly_installment": monthly_installment,
        }
        return Response(response)


class CreateLoan(APIView):
    def post(self, request):
        serializer = CheckEligibilitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        data = serializer.validated_data
        customer_id = data["customer_id"]
        loan_amount = data["loan_amount"]
        interest_rate = data["interest_rate"]
        tenure = data["tenure"]

        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response({"message": "Customer not found.", "loan_approved": False, "loan_id": None, "customer_id": customer_id, "monthly_installment": None}, status=404)

        # Eligibility logic (reuse from CheckEligibility)
        current_loans_sum = sum(
            Loan.objects.filter(customer=customer).values_list("loan_amount", flat=True)
        )
        if current_loans_sum > customer.approved_limit:
            credit_score = 0
        else:
            loans = Loan.objects.filter(customer=customer)
            total_loans = loans.count()
            paid_on_time = 0
            current_year = datetime.now().year
            activity_this_year = 0
            approved_volume = 0
            for loan in loans:
                if loan.emis_paid_on_time >= loan.tenure:
                    paid_on_time += 1
                if loan.start_date.year == current_year:
                    activity_this_year += 1
                approved_volume += loan.loan_amount
            score = 0
            if total_loans > 0:
                score += min(40, 40 * paid_on_time / total_loans)
                score += min(15, 15 * total_loans / 5)
                score += 15 if activity_this_year > 0 else 0
                score += min(15, 15 * approved_volume / customer.approved_limit)
                score += 15 if customer.current_debt < 0.5 * customer.approved_limit else 0
            credit_score = round(score, 2)

        current_emis = sum(
            Loan.objects.filter(customer=customer).values_list("monthly_installment", flat=True)
        )
        approval = False
        message = ""
        corrected_interest_rate = interest_rate
        if current_emis > 0.5 * customer.monthly_salary:
            approval = False
            message = "Current EMIs exceed 50% of monthly salary. Loan not approved."
            corrected_interest_rate = max(16.0, interest_rate)
        elif credit_score > 50:
            approval = True
            message = "Loan approved."
            corrected_interest_rate = interest_rate
        elif 50 >= credit_score > 30:
            if interest_rate > 12:
                approval = True
                message = "Loan approved."
                corrected_interest_rate = interest_rate
            else:
                approval = False
                message = "Interest rate too low for this credit score. Loan not approved."
                corrected_interest_rate = 12.01
        elif 30 >= credit_score > 10:
            if interest_rate > 16:
                approval = True
                message = "Loan approved."
                corrected_interest_rate = interest_rate
            else:
                approval = False
                message = "Interest rate too low for this credit score. Loan not approved."
                corrected_interest_rate = 16.01
        else:
            approval = False
            message = "Credit score too low. Loan not approved."
            corrected_interest_rate = max(16.0, interest_rate)

        if credit_score > 50:
            min_rate = 0
        elif 50 >= credit_score > 30:
            min_rate = 12
        elif 30 >= credit_score > 10:
            min_rate = 16
        else:
            min_rate = 16
        if interest_rate < min_rate:
            corrected_interest_rate = min_rate

        monthly_installment = calculate_emi(loan_amount, corrected_interest_rate, tenure)

        if approval:
            loan = Loan.objects.create(
                customer=customer,
                loan_amount=loan_amount,
                tenure=tenure,
                interest_rate=corrected_interest_rate,
                monthly_installment=monthly_installment,
                emis_paid_on_time=0,
                start_date=datetime.now().date(),
                end_date=datetime.now().date().replace(year=datetime.now().year + tenure // 12),
            )
            loan_id = loan.loan_id
        else:
            loan_id = None

        response = {
            "loan_id": loan_id,
            "customer_id": customer_id,
            "loan_approved": approval,
            "message": message,
            "monthly_installment": monthly_installment if approval else None,
        }
        return Response(response)


class ViewLoan(APIView):
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.get(loan_id=loan_id)
        except Loan.DoesNotExist:
            return Response({"error": "Loan not found."}, status=404)
        serializer = LoanDetailSerializer(loan)
        return Response(serializer.data)


class ViewLoans(APIView):
    def get(self, request, customer_id):
        loans = Loan.objects.filter(customer__customer_id=customer_id)
        if not loans.exists():
            return Response({"error": "No loans found for this customer."}, status=404)
        serializer = LoanListItemSerializer(loans, many=True)
        return Response(serializer.data)
