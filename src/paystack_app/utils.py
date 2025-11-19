import json
import paystack
import logging

from django.conf import *
from rest_framework.exceptions import ValidationError, NotFound


paystack.api_key = settings.PAYSTACK_SECRET
logger = logging.getLogger("app")


def try_load_json(object):
    try:
        return json.loads(object)
    except ValueError:
        return object


def call_paystack_api(func, *args, **kwargs):
    # just to raise appropriate for frontend for paystack errors
    # logger.debug(
    #     f"call_paystack_api(<function:{func.__name__}>, args={args},  kwargs={kwargs})"
    # )
    catch_exception = kwargs.pop("catch_exception", True)
    try:
        result = func(*args, **kwargs)
        # logger.debug(
        #     f"call_paystack_api result: {try_load_json(result.body) if hasattr(result, 'body') else result}"
        # )
        return result
    except paystack.exceptions.ApiException as ex:
        # logger.error(
        #     "call_paystack_api error"
        #     + (
        #         ": suppressing native error"
        #         if catch_exception
        #         else " raising native error"
        #     ),
        #     exc_info=True,
        # )
        if not catch_exception:
            raise ex
        if hasattr(ex, "body"):
            error = "paystack error: " + try_load_json(ex.body).get(
                "message", "An internal Error occured"
            )
        else:
            error = str(ex)
        raise ValidationError({"error": error})
    except Exception as ex:
        if not catch_exception:
            raise ex
        raise ValidationError({"error": str(ex)})
