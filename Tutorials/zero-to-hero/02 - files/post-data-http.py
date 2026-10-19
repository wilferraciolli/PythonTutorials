import requests
import simplejson as json


# my_data = {'name': 'Wil', 'email': 'wil@hotmail.com'}
# r = requests.post('http://www.w3schools.com/php/welcome.php', data=my_data)
#
# f = open('myfile.html', 'w+')

url = 'https://www.googleapis.com/urlshortener/v1/url'
response = requests.get(url)
payload = {'longUrl', 'http://example.com'}
headers = {'content-type': 'application/json'}

r = requests.post(url, data=payload, headers=headers)

print(r.text)
print(r.headers)
print(r.text['error']['code'])
