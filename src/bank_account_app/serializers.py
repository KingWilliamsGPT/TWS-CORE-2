from rest_framework import serializers
from .models import Banks, BankAccount


class GetBankSerializer(serializers.Serializer):
    bank_code = serializers.ChoiceField(choices=Banks.choices)
    account_number = serializers.CharField(max_length=20)
    account_name = serializers.CharField(max_length=255, read_only=True)
    bank_name = serializers.CharField(max_length=100, read_only=True)
    bank_label = serializers.CharField(max_length=100, read_only=True)


class AddBankAccountSerializer(serializers.Serializer):
    bank_code = serializers.ChoiceField(choices=Banks.choices)
    account_number = serializers.CharField(max_length=20)
    account_name = serializers.CharField(max_length=255, read_only=True)
    is_primary = serializers.BooleanField(read_only=True)
    # bvn = serializers.CharField(max_length=11, write_only=True)


class BankAccountSerializer(serializers.ModelSerializer):
    bank_name = serializers.SerializerMethodField()

    class Meta:
        model = BankAccount
        fields = [
            "id",
            "bank_code",
            "bank_name",
            "account_number",
            "account_name",
            "is_primary",
            "is_verified",
            "created_at",
            "updated_at",
        ]

    def get_bank_name(self, obj):
        return obj.get_bank_display()
