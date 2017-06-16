import json
from amazonLists import getWishlist
import requests
import time
import datetime
import random

wishlists = ['https://www.amazon.com/gp/registry/wishlist/ref=cm_wl_search_1?ie=UTF8&cid=A1MX8CB2GP86N6']

for wishlist in wishlists:
  wishlist_data = getWishlist(wishlist)
  for i in range(1,1000):
    wishlist_data['date_retrieved'] = str((datetime.datetime.now()-datetime.timedelta(minutes=(i*60))).isoformat())
    for item in wishlist_data['items']:
      try:
        item['price'] = str(round(float(item['price'])*((random.random()-.5)*.25+1),2))
      except:
        # If the item is out of stock or unavailable, the price won't be
        # a number, so we can't calculate price fluctuations
        item['price'] = item['price']
    json_data = json.dumps(wishlist_data, indent=2)
    put_status = requests.post('http://localhost:9200/amazon/wishlist/', data=json_data)
    print(wishlist_data['owner'], ' - ', wishlist_data['description'], ' - ', wishlist_data['date_retrieved'],  put_status, put_status.text)

