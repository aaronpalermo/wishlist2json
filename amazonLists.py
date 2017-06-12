
#!/usr/bin/python3
import requests
from bs4 import BeautifulSoup as bs
import datetime
import re
import json
import time

def getWishlist(wishlist_to_watch = 'https://www.amazon.com/gp/registry/wishlist/?ie=UTF8&cid=A1MX8CB2GP86N6'):
    #Check to see if the URL is a public wishlist.
    #Private gift lists, baby registries, and wedding registries don't work yet.
    if wishlist_to_watch.find('wishlist') < 10:
        return('Skipping %s because it\'s not a public wishlist.  It may be a personal giftlist (tied to your account), which I can\'t retrieve.' % (wishlist_to_watch[0]))
        
    #Pull the wishlist and soupify it
    soup = bs(requests.get(wishlist_to_watch).text, "lxml")
    
    #Create the empty lists that we'll use to create JSON from later
    wishlist = {}  #use a dictionary here
    items = []     #and a list here
    
    #Add wishlist specific info to the list, which does not include any item info
    wishlist['id'] = soup.find('a', id='wl-print-link')['href'].split('/')[4].split('?')[0]
    wishlist['owner'] = soup.find('span', class_="a-size-medium clip-text g-list-header-wrapper a-text-bold").text if soup.find('span', class_="a-size-medium clip-text g-list-header-wrapper a-text-bold") else ''
    wishlist['date_retrieved'] = str(datetime.datetime.now().isoformat())
    wishlist['description'] = soup.find('h3', id='profile-list-name').text
    wishlist['url'] = wishlist_to_watch
    
    #Iterate through all the items and pull info for each.  
    #If an item is not avaialble, then fields like price and offered_by are blank, 
    #hence all the error checking.
    for item in soup('div', id=re.compile('itemInfo*')):
        
        if item.find(id=re.compile('itemName*')).text.find('no longer available') > 0:
            debug_log = "this item is no longer available,so we'll just skip it, as if it was removed from the wishlist"
        else:
            try:
                items.append({'name' : item.find(id=re.compile('itemName*')).text, 
                          #'id' : re.search('id="itemName_(.*)" title', str(item.find(id=re.compile('itemName*')))).group(1) if item.find(id=re.compile('itemName*')).text.find('no longer available') < 0 else '', 
                          'id' : str(item.find(id=re.compile('itemName*'))).split('itemName_')[1].split('"')[0] if item.find(id=re.compile('itemName*')).text.find('no longer available') < 0 else '', 
                          #'url' : "https://www.amazon.com" + item.find(id=re.compile('itemName*'))['href'] if item.find(id=re.compile('itemName*'))['href'] else '',
                          'url' : "https://www.amazon.com" + item.find(id=re.compile('itemName*'))['href'] if 'href' in item.find(id=re.compile('itemName*')).attrs.keys() else '', 
                          'price' : item.find(id=re.compile('itemPrice*')).text[1:].replace(',','') if item.find(id=re.compile('itemPrice*')) else '',
                          'availability' : item.find(id=re.compile('availability*')).text if item.find(id=re.compile('availability*')) else '',
                          'review_stars' : item.find(id=re.compile('review_stars*')).text[:3] if item.find(id=re.compile('review_stars*')) else '',
                          'review_count' : item.find(id=re.compile('review_count*')).text[1:-1].replace(',','') if item.find(id=re.compile('review_count*')) else '',
                          'offered_by' : item.find(id=re.compile('offered-by*')).text if item.find(id=re.compile('offered-by*')) else '',
                          'used_and_new' : item.find(id=re.compile('used-and-new*')).text.split(' ')[0].replace(',','') if item.find(id=re.compile('used-and-new*')) else ''
                })
            except Exception as e:
                print("The error is:")
                print(str(e))
                print("The error was:")
    
    #Add the items to the wishlist list
    wishlist['items'] = items

    #Print the JSON to screen (this will push to Elasticsearch later)
    return(wishlist)
    #print(json.dumps(wishlist, indent=4))
    
if __name__ == "__main__":
    print("""#### This library takes one arugment (an Amazon wishlist URLs passed as a string)  #### 
#### and returns a Python dictionary object (in the format below) with the JSON      #### 
#### formatted wishlist contents.  Easy to pipe into Elasticsearch, or use elsewhere #### 

#### Structure of returned object ####
{
  "id": "1XDCOSMFIIJR9",
  "description": "Wishlist",
  "owner": "Aaron D Palermo",
  "date_retrieved": "2017-06-12T14:17:16.183225",
  "url": "https://www.amazon.com/gp/registry/wishlist/?ie=UTF8&cid=A1MX8CB2GP86N6",
  "items": [
    {
      "availability": "In Stock",
      "price": "39.40",
      "name": "LEGO Architecture London 21034 Building Kit",
      "id": "I1SFFQB9N633XR",
      "review_stars": "4.8",
      "url": "https://www.amazon.com/dp/B01KJENN0U/_encoding=UTF8?coliid=I1SFFQB9N633XR&colid=1XDCOSMFIIJR9",
      "offered_by": "Offered by Amazon.com.",
      "used_and_new": "21",
      "review_count": "40"
    }
  ]
}

#### Example code ####

from amazonLists import getWishlist
import json
import requests

wishlist = 'https://www.amazon.com/gp/registry/wishlist/23ES3G47ODB5B/ref=cm_wl_rlist_go_v?'

wishlist_data = getWishlist(wishlist) 
print(json.dumps(wishlist_data, indent=2))

#### Optionally, you can push this directly to Elasticsearch: #### 

put_status = requests.post('http://localhost:9200/amazon/wishlist/', data=json_data) 

#### And if you really want to, you can wrap everything in a loop and push #### 
#### wishlist contents to Elastic every hour (skeleton loop below)         #### 

while(True):
    wishlist_data = getWishlist(wishlist)
    json_data = json.dumps(wishlist_data, indent=2)
    put_status = requests.post('http://localhost:9200/amazon/wishlist/', data=json_data)
    print(wishlist_data['owner'], ' - ', wishlist_data['description'], put_status, put_status.text)
    print('Sleeping for 60 minutes')
    time.sleep(60*60)

    """)