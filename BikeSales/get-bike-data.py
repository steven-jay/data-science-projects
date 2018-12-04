import requests
import json
import re
from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

class BikeSalesCrawler():
    def __init__(self):
        self.url_to_crawl = "https://www.bikesales.com.au/"
        self.all_items =  []
        self.brands = {}
        self.models = []
        self.user_agent = UserAgent(verify_ssl=False)

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
        brand_list = []
        xpath_makes = '//*[@class="select-menu main-search-form__dropdown make-list"]'
        brand_list = brand_list + self.get_fields(xpath_makes)
        try:
            brand_list = set(sorted(brand_list.remove('$$disabled$$')))
        except:
            brand_list= set(sorted(brand_list))
        self.brands = dict.fromkeys(brand_list, None)

    def get_models(self):
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
                    sleep(3)
                    self.brands[brand] = dict.fromkeys(self.get_fields(xpath_models), None)
                    sleep(1)
                    print('Brand %s is valid' % brand)
                    self.write_to_file()
                except Exception:
                    self.write_to_file()
                    print("Brand %s is not valid" % brand)
                    pass


    def write_to_file(self):
        with open('brand_makes.json', 'w+') as f:
            f.write(json.dumps(self.brands))
            f.close()

    def search_url(self, brand, model):
        model = model.replace(' ', '-').lower()
        model = re.sub(r'[\(\)]', '', model)
        search_url = 'http://www.bikesales.com.au/bikes/%s/%s' % (brand, model)
        return search_url

    def return_hyperlinks(self, brand, model):
        r = requests.get(self.search_url(brand, model), headers={'User-agent':self.user_agent.chrome})
        soup = BeautifulSoup(r.text, 'html.parser')
        print(soup)


    def get_ad_hyperlinks(self):
        for brand, models in self.brands.items():
            if brand == 'Ducati':
                for model in models:
                    self.return_hyperlinks(brand, model)

    # need to test this function
    def get_ads(self):
        for brand, models in self.brands.items():
            if brand == 'Ducati':
                for model in models:
                    if model == '899 Panigale':
                        self.driver.execute_script('document.getElementsByName("make")[0].value="%s"' % (brand))
                        self.driver.find_element_by_xpath('//div[@id="csnDropdown-make"]//div[@class="select-box"]').click()
                        sleep(0.5)
                        self.driver.find_element_by_xpath('//div[@id="csnDropdown-make"]//div[@class="select-menu main-search-form__dropdown make-list"]//li[@data-value="%s"]' % (brand)).click()
                        sleep(2)
                        self.driver.find_element_by_xpath('//div[@id="csnDropdown-model"]//div[@class="select-box"]').click()
                        sleep(0.5)
                        self.driver.find_element_by_xpath('//div[@id="csnDropdown-model"]//div[@class="select-menu main-search-form__dropdown model-list"]//li[@data-value="1000 SS"]').click()
                        sleep(0.5)
                        self.search()

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
#BikeSales.get_ads()
BikeSales.get_ad_hyperlinks()
BikeSales.close_driver()
