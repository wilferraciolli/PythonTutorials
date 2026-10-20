from bs4 import BeautifulSoup
import requests
from PIL import Image
from io import BytesIO
import os

search = input('Enter search term: ')
params = {'q': search}
dir_name = search.replace(' ', '_')

if not os.path.isdir(dir_name):
    os.mkdir(dir_name)

r = requests.get('http://bing.com/images/search', params=params)

soup = BeautifulSoup(r.text, 'html.parser')
links = soup.find_all('a', {'class': 'thumb'})

for item in links:
    try:
        img_obj = requests.get(item.attrs['href'])
        print('Getting image', item.attrs['href'])
        title = item.attrs['href'].split('/')[-1]

        try:
            img = Image.open(BytesIO(img_obj.content))
            img.save('./' + dir_name + title, img.format)
        except:
            print('Image not found')
    except:
        print('Could not get images')
