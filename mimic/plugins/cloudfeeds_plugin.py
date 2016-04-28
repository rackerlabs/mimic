"""
Plugin for Rackspace cloud feeds mock.
"""
from mimic.rest.cloudfeeds import CloudFeedsApi, CloudFeedsControlApi

cloudfeeds = CloudFeedsApi()
cloudfeeds_control = CloudFeedsControlApi(cf_api=cloudfeeds)
