import os

__author__ = 'dmakhno'

# Global setting for zone
ZONE_NAME = os.getenv('QUBELL_ZONE')
zone_suffix = lambda: ' at '+ZONE_NAME if ZONE_NAME else ''

DEFAULT_ENV_NAME = lambda: 'default'+zone_suffix()
DEFAULT_WORKFLOW_SERVICE = lambda: 'Default workflow service'+zone_suffix()
DEFAULT_CREDENTIAL_SERVICE = lambda: 'Default credentials service'+zone_suffix()