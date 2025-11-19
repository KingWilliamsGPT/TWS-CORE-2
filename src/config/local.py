from src.config.common import *  # noqa
from src.config.currencies import *
from src.config.ebay import *
from src.config.logging import *


INSTALLED_APPS += CURRENCY_APPS     # handles money
# Testing
# INSTALLED_APPS += ('django_nose',)  # noqa
# TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
# NOSE_ARGS = ['-s', '--nologcapture', '--with-progressive', '--with-fixture-bundling']

# INSTALLED_APPS += ['']
