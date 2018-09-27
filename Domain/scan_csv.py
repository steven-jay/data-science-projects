import requests
import time
import csv
import collections
import pandas
import re
from bs4 import BeautifulSoup
from slimit import ast
from slimit.parser import Parser
from slimit.visitors import nodevisitor

def get_advertisement_urls(postcode, bedrooms, bathrooms, price, carspaces):
    domain_search_url = 'https://www.domain.com.au/sold-listings/?postcode=%s&bedrooms=%s&bathrooms=%s&price=%s&carspaces=%s' \
    % (postcode, bedrooms, bathrooms, price, carspaces)
    #print(domain_search_url)
    next_page = '&page='
    url_list = []

    ads_per_page = 20

    # get total amount of results and divide by ads per page to determine how many search pages need to be scanned
    fields = get_property_attributes(domain_search_url)
    total_results = fields['"searchResultCount"'][1:-1]
    if int(total_results) == 0:
        return []
    else:
        max_pages = -(-int(total_results) / ads_per_page)

    #search each page and extract the URLs to each ad, then go to the next page
    for page_no in range(1, max_pages):
        #print('Scanning ' + str(page_no))
        domain_search_page = domain_search_url + next_page + str(page_no)

        response = requests.get(domain_search_page)
        soup = BeautifulSoup(response.text, 'html.parser')

        url_list.extend(get_advertisements(soup))
        time.sleep(0.2)

    return(url_list)

def get_advertisements(search_page):
    #find the link extract to each ad and then append it the domain URL, then return the list
    domain = 'https://www.domain.com.au'
    list = []

    for advertisement in search_page.findAll('li'):
        if advertisement.get('class') == ['strap', 'new-listing']:
            for link in advertisement.findAll('a', limit=1):
                complete_link = link.get('href')
                list.append(complete_link)

    return(list)

def get_property_attributes(url):
    response = requests.get(url)

    #html parser
    soup = BeautifulSoup(response.text, 'html.parser')
    script = soup.findAll('script', {'type':'text/javascript'})[3]

    # if ad link returns valid search result, scan for attributes, else skip
    if soup.title.string.find('Real Estate Properties') == -1:
        # if ad is archived, put in dummy date, else get real date
        if soup.find("span", "status-label label-archive") != None:
            date = '31 Dec 9999'
        else:
            #get date from title of advertisement
            date = re.findall(r'\d{2}\s\w{3}\s\d{4}', soup.title.string)[0]

        #javascript parser
        parser = Parser()
        tree = parser.parse(script.text)
        fields = {getattr(node.left, 'value', ''): getattr(node.right, 'value', '')
                  for node in nodevisitor.visit(tree)
                  if isinstance(node, ast.Assign)}
        fields.update({'"date sold"':'"' + date + '"'})
        return fields
    else:
        return None

def parse_advertisement(domain_url, headers, csv_file, target_writer):

    fields = get_property_attributes(domain_url)
    if fields != None:
        csv_row = []
        for header in headers:
            key = str(header)
            try:
                csv_row.append(fields['"' + key + '"'][1:-1])
            except KeyError:
                csv_row.append('')

        target_writer.writerow(csv_row)
        csv_file.flush()

data = pandas.read_csv('url_list.csv', names=['url'])
domain_urls = data.url.tolist()[1:]

if len(domain_urls) == 0:
    print('No ads match your criteria.')

domain_headers = ['propertyId', 'date sold', 'primaryPropertyType', 'secondaryPropertyType', 'primaryCategory', 'address', 'state', 'locarea', 'suburb', 'postcode', 'suburbId', 'price', 'buildingsize', 'landsize', 'bedrooms', 'bathrooms', 'parking', 'medianPrice', 'propertyFeatures']

domain_csv = open('domain_data.csv', 'w', newline='')
domain_writer = csv.writer(domain_csv, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
domain_writer.writerow(domain_headers)

counter = 0

for url in domain_urls:
    counter = counter + 1
    if counter > 33291:
        parse_advertisement(url, domain_headers, domain_csv, domain_writer)
        time.sleep(0.1)
        if counter % 10 == 0:
            print('Checked ' + str(counter) + ' out of ' + str(len(domain_urls)))
