'''Setting for ebay accross application.'''

import os
import urllib.parse



USE_EBAY_IN_PRODUCTION = os.getenv('USE_EBAY_IN_PRODUCTION2', 'True') == 'True'

EBAY_LOGIN_URL_TEST = "https://auth.sandbox.ebay.com/oauth2/authorize?client_id=AyomideA-AutoVeri-SBX-6734da688-31a53aa5&response_type=code&redirect_uri=ByteChain-AyomideA-AutoVe-tvbkcnb&scope=https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/buy.order.readonly https://api.ebay.com/oauth/api_scope/buy.guest.order https://api.ebay.com/oauth/api_scope/sell.marketing.readonly https://api.ebay.com/oauth/api_scope/sell.marketing https://api.ebay.com/oauth/api_scope/sell.inventory.readonly https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account.readonly https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly https://api.ebay.com/oauth/api_scope/sell.fulfillment https://api.ebay.com/oauth/api_scope/sell.analytics.readonly https://api.ebay.com/oauth/api_scope/sell.marketplace.insights.readonly https://api.ebay.com/oauth/api_scope/commerce.catalog.readonly https://api.ebay.com/oauth/api_scope/buy.shopping.cart https://api.ebay.com/oauth/api_scope/buy.offer.auction https://api.ebay.com/oauth/api_scope/commerce.identity.readonly https://api.ebay.com/oauth/api_scope/commerce.identity.email.readonly https://api.ebay.com/oauth/api_scope/commerce.identity.phone.readonly https://api.ebay.com/oauth/api_scope/commerce.identity.address.readonly https://api.ebay.com/oauth/api_scope/commerce.identity.name.readonly https://api.ebay.com/oauth/api_scope/commerce.identity.status.readonly https://api.ebay.com/oauth/api_scope/sell.finances https://api.ebay.com/oauth/api_scope/sell.payment.dispute https://api.ebay.com/oauth/api_scope/sell.item.draft https://api.ebay.com/oauth/api_scope/sell.item https://api.ebay.com/oauth/api_scope/sell.reputation https://api.ebay.com/oauth/api_scope/sell.reputation.readonly https://api.ebay.com/oauth/api_scope/commerce.notification.subscription https://api.ebay.com/oauth/api_scope/commerce.notification.subscription.readonly https://api.ebay.com/oauth/api_scope/sell.stores https://api.ebay.com/oauth/api_scope/sell.stores.readonly"
EBAY_LOGIN_URL_PRD = "https://auth.ebay.com/oauth2/authorize?client_id=AyomideA-AutoVeri-PRD-d83d9745b-57096505&response_type=code&redirect_uri=ByteChain-AyomideA-AutoVe-xfjmrzn&scope=https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.marketing.readonly https://api.ebay.com/oauth/api_scope/sell.marketing https://api.ebay.com/oauth/api_scope/sell.inventory.readonly https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account.readonly https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly https://api.ebay.com/oauth/api_scope/sell.fulfillment https://api.ebay.com/oauth/api_scope/sell.analytics.readonly https://api.ebay.com/oauth/api_scope/sell.finances https://api.ebay.com/oauth/api_scope/sell.payment.dispute https://api.ebay.com/oauth/api_scope/commerce.identity.readonly https://api.ebay.com/oauth/api_scope/sell.reputation https://api.ebay.com/oauth/api_scope/sell.reputation.readonly https://api.ebay.com/oauth/api_scope/commerce.notification.subscription https://api.ebay.com/oauth/api_scope/commerce.notification.subscription.readonly https://api.ebay.com/oauth/api_scope/sell.stores https://api.ebay.com/oauth/api_scope/sell.stores.readonly"
# EBAY_LOGIN_URL_TEST = "https://TEST"
# EBAY_LOGIN_URL_PRD = "https://PROD"


def extract_scopes(url):
    # Parse the URL
    parsed_url = urllib.parse.urlparse(url)
    
    # Parse the query parameters
    query_params = urllib.parse.parse_qs(parsed_url.query)
    
    # Extract the 'scope' parameter and split it into individual scopes
    scopes = query_params.get('scope', [])
    if scopes:
        scopes = scopes[0].split()
    
    return scopes



EBAY_TEST_SCOPES = extract_scopes(EBAY_LOGIN_URL_TEST)
EBAY_PROD_SCOPES = extract_scopes(EBAY_LOGIN_URL_PRD)

# EBAY_SCOPES = [
#  'https://api.ebay.com/oauth/api_scope',                                       
#  'https://api.ebay.com/oauth/api_scope/buy.order.readonly',                    
#  'https://api.ebay.com/oauth/api_scope/buy.guest.order',                       
#  'https://api.ebay.com/oauth/api_scope/sell.marketing.readonly',               
#  'https://api.ebay.com/oauth/api_scope/sell.marketing',                        
#  'https://api.ebay.com/oauth/api_scope/sell.inventory.readonly',               
#  'https://api.ebay.com/oauth/api_scope/sell.inventory',                        
#  'https://api.ebay.com/oauth/api_scope/sell.account.readonly',                 
#  'https://api.ebay.com/oauth/api_scope/sell.account',                          
#  'https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly',             
#  'https://api.ebay.com/oauth/api_scope/sell.fulfillment',                      
#  'https://api.ebay.com/oauth/api_scope/sell.analytics.readonly',               
#  'https://api.ebay.com/oauth/api_scope/sell.marketplace.insights.readonly',    
#  'https://api.ebay.com/oauth/api_scope/commerce.catalog.readonly',             
#  'https://api.ebay.com/oauth/api_scope/buy.shopping.cart',                     
#  'https://api.ebay.com/oauth/api_scope/buy.offer.auction',
# ]
# EBAY_TRADING_SCOPES = [
#  # For Trading.GetUser, ...
#  'https://api.ebay.com/oauth/api_scope/commerce.identity.readonly',            
#  'https://api.ebay.com/oauth/api_scope/commerce.identity.email.readonly',      
#  'https://api.ebay.com/oauth/api_scope/commerce.identity.phone.readonly',      
#  'https://api.ebay.com/oauth/api_scope/commerce.identity.address.readonly',    
#  'https://api.ebay.com/oauth/api_scope/commerce.identity.name.readonly',       
#  'https://api.ebay.com/oauth/api_scope/commerce.identity.status.readonly',     
# ]
# EBAY_OTHER_SCOPES=[
#  'https://api.ebay.com/oauth/api_scope/sell.finances',                         
#  'https://api.ebay.com/oauth/api_scope/sell.payment.dispute',                  
#  'https://api.ebay.com/oauth/api_scope/sell.item.draft',                       
#  'https://api.ebay.com/oauth/api_scope/sell.item',                             
#  'https://api.ebay.com/oauth/api_scope/sell.reputation',                       
#  'https://api.ebay.com/oauth/api_scope/sell.reputation.readonly',              
#  'https://api.ebay.com/oauth/api_scope/commerce.notification.subscription',    
#  'https://api.ebay.com/oauth/api_scope/commerce.notification.subscription.readonly',                                                                          
#  'https://api.ebay.com/oauth/api_scope/sell.stores',                           
#  'https://api.ebay.com/oauth/api_scope/sell.stores.readonly'
#  ]

CONFIG_FILE = 'ebay.yaml'