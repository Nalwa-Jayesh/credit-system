from rest_framework import serializers
from .models import Customer, Loan


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"


class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = "__all__"


class CheckEligibilitySerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()

class LoanDetailCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["customer_id", "first_name", "last_name", "phone_number", "age"]

class LoanDetailSerializer(serializers.ModelSerializer):
    customer = LoanDetailCustomerSerializer(read_only=True)
    class Meta:
        model = Loan
        fields = [
            "loan_id",
            "customer",
            "loan_amount",
            "interest_rate",
            "monthly_installment",
            "tenure",
        ]

class LoanListItemSerializer(serializers.ModelSerializer):
    repayments_left = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            "loan_id",
            "loan_amount",
            "interest_rate",
            "monthly_installment",
            "repayments_left",
        ]

    def get_repayments_left(self, obj):
        return max(0, obj.tenure - obj.emis_paid_on_time)
