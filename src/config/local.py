from src.config.common import *  # noqa

# Testing
INSTALLED_APPS += (
    'django_nose',
    'django_seed',
)  # noqa
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ['-s', '--nologcapture', '--with-fixture-bundling']
# REUSE_DB = True
# MIGRATE = True
# MIGRATION_MODULES = {"models": "src.models.migrations"}
