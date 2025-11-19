import re
import random
import string

from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.conf import settings

from src.common.serializers import EmptySerializer
from .models import Wallet
from .serializers import WalletSerializer
from .services.wallet_services import WalletService


class WalletViewSet(viewsets.GenericViewSet):
    """
    Creates, Updates and Retrieves - User Accounts
    """

    serializers = {
        "default": WalletSerializer,
    }
    permissions = {
        "default": (IsAuthenticated,),
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers["default"])

    def get_permissions(self):
        self.permission_classes = self.permissions.get(
            self.action, self.permissions["default"]
        )
        return super().get_permissions()
    
    @action(detail=False, methods=['get'], pagination_class=None)
    def get_user_wallets(self, request):
        wallets = WalletService.get_user_wallets(
            request.user,
        )
        serializer = WalletSerializer(wallets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=False, methods=["post"], url_path="fund", url_name="fund")
    def fund_main_wallet(self, request):
        return Response(
            {"message": "Wallet successfully funded"}, status=status.HTTP_200_OK
        )

    # @action(detail=False, methods=['get'], url_path='me', url_name='me')
    # def get_user_data(self, instance):
    #     try:
    #         return Response(UserSerializer(self.request.user, context={'request': self.request}).data, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         return Response({'error': 'Wrong auth token' + e}, status=status.HTTP_400_BAD_REQUEST)
