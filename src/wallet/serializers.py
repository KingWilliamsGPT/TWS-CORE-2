from rest_framework import serializers

from .models import Wallet

class WalletSerializer(serializers.ModelSerializer):

    class Meta:
        model = Wallet
        fields = (
            'wallet_name',
            'balance',
            'status',
            'wallet_type',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields # all fields
