import csv
import time
from datetime import datetime

import pandas as pd
from selenium import webdriver
from os import listdir
from functools import partial
#import pandas as pd
import os
import re
from pathlib import Path
import logging
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

BASE_DIR = Path(__name__).absolute().parent


class TaskLogger:
    def __init__(self, logger, extra):
        self.info = partial(logger.info, extra=extra)
        self.debug = partial(logger.debug, extra=extra)
        self.error = partial(logger.error, extra=extra)


class TripAdvisor():
    def __init__(self):
        logs_dir = BASE_DIR / "logs"
        logs_dir.mkdir(exist_ok=True)
        logger = logging.getLogger(__name__)
        sh = logging.StreamHandler()
        log_format = "%(levelname)s : %(asctime)s : %(message)s"
        formatter = logging.Formatter(log_format)
        sh.setFormatter(formatter)
        fh = logging.FileHandler(
            logs_dir / f"{datetime.now().strftime('%Y-%m-%d %I.%M %p')}.log", mode="w"
        )
        fh.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(sh)
        logger.addHandler(fh)
        self.logger = logger
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-setuid-sandbox')
        self.options.add_argument("--proxy-server='direct://")
        self.options.add_argument('--proxy-bypass-list=*')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-accelerated-2d-canvas')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument("start-maximized")

        # self.options.add_argument('--headless')
        # self.options.add_argument("-incognito")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.base_url = "https://www.tripadvisor.com"

    def create_driver(self):
        try:
            chrome_options = Options()
            #chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(options=chrome_options)
        except:
            driver = None

        return driver

    def close_driver(self, driver):
        """
        :param driver:
        :return:
        """
        try:
            driver.close()
            driver.quit()
            print('Driver closed successfully.')
        except Exception as e:
            print(e)
            pass

    @staticmethod
    def make_request(driver, url):
        """
        :param driver: selenium driver
        :param url: url to hit
        :return: driver containing source of given url
        """
        if driver and url:
            url = url if not isinstance(url, bytes) else url.decode('utf-8')
            time.sleep(2)
            driver.get(url)
            return driver
        return None

    def parse(self):
        driver = self.create_driver()
        self.logger.info("making request")
        driver = self.make_request(driver,'https://www.tripadvisor.com/Search?q=Windsor%2C%20berkshire&searchSessionId=CD22B4FE12370530E95E4129D5F25F1B1627757011310ssid&sid=F6654899447B4D90895BAADCCAA7E3C11627759548772&blockRedirect=true&ssrc=h&geo=1&rf=4')
        CSV_Files = [file for file in listdir('./input_csv')
                     if
                     file.endswith('.csv')]

        df = pd.read_csv("./input_csv/{}".format(CSV_Files[0]), encoding="ISO-8859-1", engine='python')
        for q1,q2 in zip(df['q1'], df['q2']):
            time.sleep(5)
            driver.find_element_by_id("mainSearch").send_keys(Keys.CONTROL + "a")
            driver.find_element_by_id("mainSearch").send_keys(Keys.DELETE)
            driver.find_element_by_id("mainSearch").send_keys(q1)
            driver.find_element_by_id("GEO_SCOPED_SEARCH_INPUT").send_keys(Keys.CONTROL + "a")
            driver.find_element_by_id("GEO_SCOPED_SEARCH_INPUT").send_keys(Keys.DELETE)
            driver.find_element_by_id("GEO_SCOPED_SEARCH_INPUT").send_keys(q2)
            driver.find_element_by_id("SEARCH_BUTTON").click()
            time.sleep(5)
            driver.find_element_by_css_selector('[data-filter-id="ATTRACTIONS"]').click()
            time.sleep(5)
            if driver.find_elements_by_css_selector(".result-title"):
                for i in range(len(driver.find_elements_by_css_selector(".result-title"))):
                    try:
                        url = re.findall("/Attraction.*html",
                                         driver.find_elements_by_css_selector(".result-title[onclick]")[
                                             i].get_attribute(
                                             "onclick"))[0]
                    except:
                        print("link not valid")
                        continue
                    url = "{}{}".format(self.base_url, url)
                    print(url)
                    driver = self.make_request(driver, url)
                    time.sleep(10)
                    item = dict()
                    try:
                        try:
                            item["title"] = driver.find_element_by_css_selector('h1[data-automation="mainH1"]').text
                        except:
                            item["title"] = driver.find_element_by_id('HEADING').text
                    except:
                        item["title"] = ''
                        print("something wrong with title")
                    try:
                        try:
                            item["reviewsCount"] = driver.find_element_by_css_selector(
                                'a[href="#REVIEWS"] span span').text
                        except:
                            item["reviewsCount"] = driver.find_element_by_css_selector(
                                '[class^="reviewCount"]').text
                    except:
                        item["reviewsCount"] = ''
                        print("something wrong with reviewsCount")
                    try:
                        item["averageReview"] = \
                            driver.find_element_by_css_selector('a[href="#REVIEWS"] div[aria-label]').get_attribute(
                                'aria-label').split(" ")[0]
                    except:
                        item["averageReview"] = str(driver.find_element_by_css_selector(
                            '.ui_poi_review_rating  span[class^="ui_bubble_rating"]').get_attribute(
                            'class').split("_")[-1])
                        if "50" in \
                                str(item["averageReview"]):
                            item["averageReview"] = 5
                        if "45" in \
                                str(item["averageReview"]):
                            item["averageReview"] = 4.5
                        if "40" in \
                                str(item["averageReview"]):
                            item["averageReview"] = 4
                        if "35" in \
                                str(item["averageReview"]):
                            item["averageReview"] = 3.5
                        if "30" in \
                                str(item["averageReview"]):
                            item["averageReview"] = 3
                        if "25" in \
                                str(item["averageReview"]):
                            item["averageReview"] = 2.5
                        if "20" in \
                                str(item["averageReview"]):
                            item["averageReview"] = 2
                        if "15" in \
                                str(item["averageReview"]):
                            item["averageReview"] = 1.5
                        if "10" in \
                                str(item["averageReview"]):
                            item["averageReview"] = 1

                    try:
                        item["openStatus"] = driver.find_element_by_css_selector(
                            '[aria-label="Open Hours"] span').text
                    except:
                        item["openStatus"] = ''
                        print("something wrong with openStatus")
                    try:
                        item["openHour"] = driver.find_element_by_css_selector(
                            '[aria-label="Open Hours"]+span').text
                    except:
                        item["openHour"] = ''
                        print("something wrong with openHour")
                    try:
                        item["phone"] = driver.find_element_by_css_selector('[href^="tel:"]').get_attribute(
                            "href").replace(
                            "tel:", "")

                    except:
                        item["phone"] = ''
                        print("something wrong with phone")
                    try:
                        item["email"] = driver.find_element_by_css_selector('[href^="mailto:"]').get_attribute(
                            "href").replace("mailto:", "").replace("('", "").replace("',)", ""),

                    except:
                        item["email"] = ''
                        print("something wrong with email")
                    try:
                        item["aboutDescription"] = driver.find_element_by_css_selector(
                            '[style^="line-break"] div').text

                    except:
                        item["aboutDescription"] = ""
                        print("something wrong with aboutDescription")
                    try:
                        item["thingsTodo"] = driver.find_element_by_css_selector(
                            '[data-automation="AppPresentation_PoiOverviewWeb"] a span div').text
                    except:
                        item["thingsTodo"] = ""
                    try:
                        if "website" in driver.find_element_by_css_selector('[rel="nofollow"] span').text:
                            item["website"] = driver.find_element_by_css_selector('[rel="nofollow"]').get_attribute(
                                "href")
                    except:
                        item["website"] = ""
                        print("something wrong with website")
                    try:
                        item["Address"] = driver.find_element_by_css_selector('.map-pin+span').text
                    except:
                        item["Address"] = "{}{}".format(q1, q2)
                    try:
                        item["link"] = driver.current_url
                    except:
                        item["link"] = ''
                        print("something wrong with link")
                    filename = 'trip_thing.csv'
                    file_exists = os.path.isfile(filename)

                    with open(filename, 'a', encoding="utf-8") as csvfile:
                        headers = item.keys()
                        writer = csv.DictWriter(csvfile, delimiter=',',
                                                lineterminator='\n',
                                                fieldnames=headers)

                        if not file_exists:
                            writer.writeheader()  # file doesn't exist yet, write a header
                        writer.writerow(item)
                    print(item)
                    driver.back()
                    time.sleep(5)
            driver.find_element_by_id("mainSearch").send_keys(Keys.CONTROL + "a")
            driver.find_element_by_id("mainSearch").send_keys(Keys.DELETE)
            driver.find_element_by_id("mainSearch").send_keys(q1)
            driver.find_element_by_id("GEO_SCOPED_SEARCH_INPUT").send_keys(Keys.CONTROL + "a")
            driver.find_element_by_id("GEO_SCOPED_SEARCH_INPUT").send_keys(Keys.DELETE)
            driver.find_element_by_id("GEO_SCOPED_SEARCH_INPUT").send_keys(q2)
            driver.find_element_by_id("SEARCH_BUTTON").click()
            time.sleep(10)
            try:
                driver.find_element_by_css_selector('[data-tab-name="Restaurants"]').click()
                time.sleep(5)
            except:
                print("issue in hotels link")
            if driver.find_elements_by_css_selector(".result-title"):
                for i in range(len(driver.find_elements_by_css_selector(".result-title"))):
                    try:
                        url = re.findall("/Restaurant_Review.*html",
                                         driver.find_elements_by_css_selector(".result-title[onclick]")[
                                             i].get_attribute(
                                             "onclick"))[0]
                    except:
                        print("Url not found")
                        continue
                    url = "{}{}".format(self.base_url, url)
                    print(url)
                    driver = self.make_request(driver, url)
                    time.sleep(5)
                    item = dict()
                    try:
                        item["title"] = driver.find_element_by_css_selector('[data-test-target="top-info-header"]').text
                    except:
                        item["title"] = ''
                        print("something wrong with title")
                    try:
                        item["reviewsCount"] = driver.find_element_by_css_selector(
                            'a[href="#REVIEWS"] span').text
                    except:
                        item["reviewsCount"] = ''
                        print("something wrong with reviewsCount")
                    try:
                        item["averageReview"] = driver.find_element_by_css_selector(
                            'a[href="#REVIEWS"] svg').get_attribute("title").split(" ")[0]
                    except:
                        item["averageReview"] = ""
                        print("something wrong with averageReview")
                    try:
                        item["Address"] = driver.find_element_by_css_selector('.map-pin-fill+span').text
                    except:
                        item["Address"] = ''
                        print("something wrong with Address")
                    try:
                        item["rank"] = driver.find_element_by_css_selector(
                            '[data-test-target="restaurant-detail-info"] div span+span a span').text
                        if not item['rank']:
                            item['rank'] = driver.find_element_by_css_selector('a[href="#REVIEWS"]+div').text
                    except:
                        item["rank"] = ''
                        print("something wrong with rank")
                    try:
                        item["link"] = driver.current_url
                    except:
                        item["link"] = ''
                        print("something wrong with link")
                    try:
                        item["website"] = driver.find_element_by_css_selector(
                            '[referrerpolicy="origin"]').get_attribute("href")
                    except:
                        item["website"] = ''
                        print("something wrong with website")
                    try:
                        item["phone"] = driver.find_element_by_css_selector('[href^="tel:"]').get_attribute(
                            "href").replace(
                            "tel:", "")
                    except:
                        item["phone"] = ''
                        print("something wrong with phone")
                    try:
                        item["email"] = driver.find_element_by_css_selector('[href^="mailto:"]').get_attribute(
                            "href").replace("mailto:", ""),
                    except:
                        item["email"] = ''
                        print("something wrong with email")
                    try:
                        item["status"] = driver.find_element_by_css_selector('span div span span span').text,
                    except:
                        item["status"] = ''
                        print("something wrong with status")
                    filename = 'trip_Resturants.csv'
                    file_exists = os.path.isfile(filename)

                    with open(filename, 'a', encoding="utf-8") as csvfile:
                        headers = item.keys()
                        writer = csv.DictWriter(csvfile, delimiter=',',
                                                lineterminator='\n',
                                                fieldnames=headers)

                        if not file_exists:
                            writer.writeheader()  # file doesn't exist yet, write a header
                        writer.writerow(item)
                    print(item)
                    driver.back()
                    time.sleep(5)





trip = TripAdvisor()
trip.parse()
