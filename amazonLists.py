
#!/usr/bin/python3
import requests
from bs4 import BeautifulSoup as bs
import datetime
import re
import json
import time

def getWishlist(wishlist_to_pull = 'https://www.amazon.com/gp/registry/wishlist/?ie=UTF8&cid=A1MX8CB2GP86N6'):
  #Check to see if the URL is a public wishlist.
  #Private gift lists, baby registries, and wedding registries don't work yet.
  if wishlist_to_pull.find('wishlist') < 10:
    return("Skipping %s because it's not a public wishlist.  It may be a personal giftlist (tied to your account), which I can't retrieve." % (wishlist_to_pull))
    
  #Pull the wishlist and soupify it using the fast lxml parser
  soup = bs(requests.get(wishlist_to_pull).text, "lxml")
  
  #Create the empty lists that we'll use to create JSON from later
  wishlist = {}  #use a dictionary here
  items = []   #and a list here
  
  #Add wishlist specific info to the list, which does not include any item info
  #Wishlists always have an ID, so no error checking here for now
  wishlist['id'] = soup.find('a', id='wl-print-link')['href'].split('/')[4].split('?')[0]
  
  if soup.find('span', class_="a-size-medium clip-text g-list-header-wrapper a-text-bold"):
    wishlist['owner'] = soup.find('span', class_="a-size-medium clip-text g-list-header-wrapper a-text-bold").text
  else:
    wishlist['owner'] = ''
  
  #Get the timestamp for right now in ISO format.  ex: 2017-06-13T19:47:23.734216
  wishlist['date_retrieved'] = str(datetime.datetime.now().isoformat())
  wishlist['description'] = soup.find('h3', id='profile-list-name').text
  wishlist['url'] = wishlist_to_pull
  
  #Iterate through all the items and pull info for each.  
  #If an item is not avaialble, then fields like price and offered_by are blank, 
  #hence all the error checking.
  for item in soup('div', id=re.compile('itemInfo*')):
    
    #If an item is no longer available, it'll still show up in the list, 
    #but won't have any of the attributes we're looing for, so let's skip it
    if item.find(id=re.compile('itemName*')).text.find('no longer available') > 0:
      debug_log = "this item is no longer available,so we'll just skip it, as if it was removed from the wishlist"
    #Otherwise, for those items that do exist, parse away!
    else:
      #There are LOTS of permutations that you can find in a wishlist,
      #so I do lots of error checking to catch these & refine the script
      
      #See if the item's name exists, if so, store it and move on, 
      #Otherwise catch the error and set the item_name to 'ERROR'
      try:
        item_name = item.find(id=re.compile('itemName*')).text
      except Exception as e:
        print("The item_name error is:", str(e))
        item_name = 'ERROR'
      
      try:   
        item_id = str(item.find(id=re.compile('itemName*'))).split('itemName_')[1].split('"')[0]  
      except Exception as e:
        print("The item_id error is:", str(e))
        item_id = 'ERROR'
      
      try:
        if 'href' in item.find(id=re.compile('itemName*')).attrs.keys():
          item_url = "https://www.amazon.com" + item.find(id=re.compile('itemName*'))['href']  
        else:
          item_url = ''
      except Exception as e:
        print("The item_url error is:", str(e))
        item_url = 'ERROR'   
        
      try:
        if item.find(id=re.compile('itemPrice*')):
          item_price = item.find(id=re.compile('itemPrice*')).text[1:].replace(',','')  
        else:
          item_price = ''
      except Exception as e:
        print("The item_price error is:", str(e))
        item_price = 'ERROR' 
      
      try:  
        if item.find(id=re.compile('availability*')):
          item_availability = item.find(id=re.compile('availability*')).text  
        else:
          item_availability = ''
      except Exception as e:
        print("The item_availability error is:", str(e))
        item_availability = 'ERROR'          
      
      try:    
        if item.find(id=re.compile('review_stars*')):
          item_review_stars = item.find(id=re.compile('review_stars*')).text[:3]  
        else:
          item_review_stars = ''
      except Exception as e:
        print("The item_review_stars error is:", str(e))
        item_review_stars = 'ERROR' 
      
      try:  
        if item.find(id=re.compile('review_count*')):
          item_review_count = item.find(id=re.compile('review_count*')).text[1:-1].replace(',','')  
        else:
          item_review_count = ''
      except Exception as e:
        print("The item_review_count error is:", str(e))
        item_review_count = 'ERROR' 
      
      try:
        if item.find(id=re.compile('offered-by*')):
          item_offered_by = item.find(id=re.compile('offered-by*')).text  
        else:
          item_offered_by = ''
      except Exception as e:
        print("The item_offered_by error is:", str(e))
        item_offered_by = 'ERROR' 
        
      try:
        if item.find(id=re.compile('used-and-new*')):
          item_used_and_new = item.find(id=re.compile('used-and-new*')).text.split(' ')[0].replace(',','')  
        else:
          item_used_and_new = ''
      except Exception as e:
        print("The item_used_and_new error is:", str(e))
        item_used_and_new = 'ERROR' 
        
      items.append({'name' : item_name, 
          'id' :  item_id,
          'url' : item_url, 
          'price' : item_price,
          'availability' : item_availability,
          'review_stars' : item_review_stars,
          'review_count' : item_review_count,
          'offered_by' : item_offered_by,
          'used_and_new' : item_used_and_new
      })
  #Add the items to the wishlist list
  wishlist['items'] = items

  #Print the JSON to screen (this will push to Elasticsearch later)
  return(wishlist)
  #print(json.dumps(wishlist, indent=4))
  
  
  
# Let's give some example code for anyone who may try to run this as
# a stand-alone program.  Examples include expected inputs and outputs.
if __name__ == "__main__":
  print("""#### This library takes one arugment (an Amazon wishlist URLs passed as a string)  #### 
#### and returns a Python dictionary object (in the format below) with the JSON    #### 
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
#### wishlist contents to Elastic every hour (skeleton loop below)     #### 

while(True):
  wishlist_data = getWishlist(wishlist)
  json_data = json.dumps(wishlist_data, indent=2)
  put_status = requests.post('http://localhost:9200/amazon/wishlist/', data=json_data)
  print(wishlist_data['owner'], ' - ', wishlist_data['description'], put_status, put_status.text)
  print('Sleeping for 60 minutes')
  time.sleep(60*60)

  """)