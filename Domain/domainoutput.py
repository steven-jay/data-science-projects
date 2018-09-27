import requests
import time
import csv
import collections
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
        max_pages = int(-(-int(total_results) / ads_per_page))

    #search each page and extract the URLs to each ad, then go to the next page
    for page_no in range(1, max_pages):
        #print('Scanning ' + str(page_no))
        domain_search_page = domain_search_url + next_page + str(page_no)

        response = requests.get(domain_search_page)
        soup = BeautifulSoup(response.text, 'html.parser')

        url_list.extend(get_advertisements(soup))
        time.sleep(0.1)

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

    #javascript parser
    parser = Parser()
    tree = parser.parse(script.text)
    fields = {getattr(node.left, 'value', ''): getattr(node.right, 'value', '')
              for node in nodevisitor.visit(tree)
              if isinstance(node, ast.Assign)}
    return fields

def parse_advertisement(domain_url, headers, target_writer):

    fields = get_property_attributes(domain_url)

    csv_row = []
    for header in headers:
        key = str(header)
        try:
            csv_row.append(fields['"' + key + '"'][1:-1])
        except KeyError:
            csv_row.append('')

    target_writer.writerow(csv_row)

domain_urls = []

columns = collections.defaultdict(list)

with open('sydney_postcodes.csv', 'r') as pc:
    reader = csv.DictReader(pc)
    for row in reader:
        for (k, v) in row.items():
            columns[k].append(v)

i = 0

for postcode in columns['Postcode']:
#for postcode in range (2071, 2072):
    for bedrooms in range(1, 3, 2):
        bedroom_range = str(bedrooms) + '-' + str(bedrooms+1)
        for bathrooms in range(1, 3, 2):
            bathroom_range = str(bathrooms) + '-' + str(bathrooms+1)
            for price in range(500000,900000,50000):
                price_range = str(price) + '-' + str(price + 50000)
                carspaces = '1-any'
                search_results = []
                search_results.extend(get_advertisement_urls(str(postcode), bedroom_range, bathroom_range, price_range, carspaces))
                domain_urls.extend(search_results)

    i += 1
    print(str(i/len(columns['Postcode'])) + '% complete')

domain_urls = list(set(domain_urls))

with open('url_list.csv', 'w') as url_list:
    writer = csv.writer(url_list, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
    for url in domain_urls:
        writer.writerow([url])

print(len(domain_urls))

if len(domain_urls) == 0:
    print('No ads match your criteria.')

domain_headers = ['propertyId', 'primaryPropertyType', 'secondaryPropertyType', 'primaryCategory', 'address', 'state', 'locarea', 'suburb', 'postcode', 'suburbId', 'price', 'buildingsize', 'landsize', 'bedrooms', 'bathrooms', 'parking', 'medianPrice', 'propertyFeatures']

domain_csv = open('domain_data.csv', 'w')
domain_writer = csv.writer(domain_csv, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
domain_writer.writerow(domain_headers)

counter = 0

for url in domain_urls:
    counter = counter + 1
    parse_advertisement(url, domain_headers, domain_writer)
    if counter % 10 == 0:
        print('Checked ' + str(counter) + ' out of ' + str(len(domain_urls)))
