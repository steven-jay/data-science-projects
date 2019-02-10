import requests
import json
import re
import pprint as pp
from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from itertools import islice

class BikeSalesCrawler():
    def __init__(self):
        self.url_to_crawl = "https://www.bikesales.com.au"
        self.all_items =  []
        self.brands = {}
        self.models = []
        self.user_agent = UserAgent(verify_ssl=False)
        self.headers = {
            'user-agent': self.user_agent.chrome,
            'referer': 'https://www.google.com.au',
            }

    # Open chromedriver
    def start_driver(self):
        print('starting driver...')
        self.driver = webdriver.Chrome()
        sleep(1)

    def close_driver(self):
        print('closing driver...')
        self.driver.quit()
        print('closed!')

    def get_page(self, url):
        print('getting page...')
        self.driver.get(url)
        sleep(3)

    def get_fields(self, xpath):
        data = []
        try:
            form = self.driver.find_element_by_xpath(xpath)
            all_items = form.find_elements_by_tag_name("li")
            for item in all_items:
                data_value = item.get_attribute("data-value")
                if data_value is not None:
                    data.append(item.get_attribute("data-value"))
        except Exception:
            pass
        return data

    def get_makes(self):
        print('Getting makes...')
        brand_list = []
        xpath_makes = '//*[@class="select-menu main-search-form__dropdown make-list"]'
        brand_list = brand_list + self.get_fields(xpath_makes)
        try:
            brand_list = set(sorted(brand_list.remove('$$disabled$$')))
        except:
            brand_list= set(sorted(brand_list))
        self.brands = dict.fromkeys(brand_list, None)

    def get_models(self):
        print('Getting models...')
        brand_to_test = ['Ducati']

        for brand in self.brands:
            if brand in brand_to_test:
                try:
                    self.driver.execute_script('document.getElementsByName("make")[0].value="%s"' % (brand))
                    self.driver.find_element_by_xpath('//div[@id="csnDropdown-make"]//div[@class="select-box"]').click()
                    sleep(0.5)
                    self.driver.find_element_by_xpath('//div[@id="csnDropdown-make"]//div[@class="select-menu main-search-form__dropdown make-list"]//li[@data-value="%s"]' % (brand)).click()
                    sleep(2)

                    xpath_models = '//*[@class="select-menu main-search-form__dropdown model-list"]'
                    sleep(5)
                    self.brands[brand] = dict.fromkeys(self.get_fields(xpath_models), None)
                    sleep(1)
                    print('Brand %s is valid' % brand)
                    self.write_to_file('brand_makes.json', self.brands)
                except Exception:
                    self.write_to_file('brand_makes.json', self.brands)
                    print("Brand %s is not valid" % brand)
                    pass

    def check_content_type(self, content):
        content = str(content)
        if content[0] == '<':
            return 'XML'
        elif content[0] == '{':
            return 'JSON'

    def write_to_file(self, filename, content):
        if self.check_content_type(content) == 'XML':
            self.write_xml(filename, content)
        elif self.check_content_type(content) == 'JSON':
            self.write_json(filename, content)

    def write_xml(self, filename, content):
        with open(filename, 'w+') as f:
            f.write(content)
            f.close()

    def write_json(self, filename, content):
        with open(filename, 'w+') as f:
            f.write(json.dumps(content))
            f.close()

    def search_url(self, brand, model):
        model = model.replace(' ', '-').lower()
        model = re.sub(r'[\(\)]', '', model)
        search_url = '%s/bikes/%s/%s' % (self.url_to_crawl, brand, model)
        return search_url

    def mod_url(self, url_suffix):
        print('Truncating URL...')
        param_indicator = '?'
        try:
            url_suffix = url_suffix[:url_suffix.index(param_indicator)]
        except AttributeError:
            pass
        url = str(self.url_to_crawl) + str(url_suffix)
        return url

    def return_hyperlinks(self, brand, model):
        print('Returning search result links...')
        r = requests.get(self.search_url(brand, model), headers=self.headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        body = soup.body
        results = body.find_all(class_='js-encode-search')
        # with open('href output.xml', 'w+') as f:
        #     f.write(str(results))
        #     f.close()
        #self.brands[brand][model] = set([str(self.url_to_crawl) + str(result.get('href')) for result in results])
        self.brands[brand][model] = set([self.mod_url(result.get('href')) for result in results])

        self.get_stats(brand, model)
        #pp.pprint(self.brands[brand][model])

    def get_stats(self, brand, model):
        print('Scraping ad...')
        for url in self.brands[brand][model]:
            print(url)
            r = requests.get(url, headers=self.headers)
            print(r.text)
            if r.status_code == 200:
                self.write_to_file('ad_output.xml', r.text)

    def get_ad_hyperlinks(self):
        for brand, models in self.brands.items():
            if brand == 'Ducati':
                for model in models:
                    if model == '899 Panigale':
                        print('Getting links for %s %s...' % (brand, model))
                        self.return_hyperlinks(brand, model)

    def search(self):
        self.driver.find_element_by_xpath('//button[@id="csnSearchButton"]').click()

    def parse(self):
        self.start_driver()
        self.get_page(self.url_to_crawl)
        self.close_driver()

BikeSales = BikeSalesCrawler()
BikeSales.get_makes()
BikeSales.start_driver()
BikeSales.get_page(BikeSales.url_to_crawl)
BikeSales.get_makes()
BikeSales.get_models()
BikeSales.get_ad_hyperlinks()
BikeSales.close_driver()
