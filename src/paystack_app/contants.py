from django.conf import settings

PAYSTACK_IP_WHITELIST = [    
    "52.31.139.75",
    "52.49.173.169",
    "52.214.14.220",
]

if settings.DEBUG:
    PAYSTACK_IP_WHITELIST.append("127.0.0.1")