# coding:utf-8 
from flask import Flask, url_for, render_template, request, session
from flask import request
import requests
import json
import re
import pandas as pd
import numpy as np
from pandas import DataFrame,Series
from bs4 import BeautifulSoup
import csv,os,json
from time import sleep
from lxml import html 
from lxml import etree 
import xlwt
# from pyquery import PyQuery
import urllib
from amazon.api import AmazonAPI
from flask_sqlalchemy import SQLAlchemy


#
# reload(sys)
# sys.setdefaultencoding('utf8')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/pre-registration'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

__tablename__ = "users"
title = db.Column(db.String(120), primary_key=False)
price = db.Column(db.String(120), unique=False)
search_word = ""

#function used for taobao search
def taobao_search(search_word):
    price_table = DataFrame(np.array(['title', 'price']).reshape(1, 2), columns=['raw_title', 'view_price'])
    url = "https://s.taobao.com/search?initiative_id=tbindexz_20160224&ie=utf8&spm=a21bo.7724922.8452-taobao-item.2&sourceId=tb.index&search" \
          "_type=item&ssid=s5-e&commend=all&imgfile=&q=" + search_word + "&suggest=history_1&_input_charset=utf-8&wq=s&suggest_query=s&source=suggest"
    url_base = "https://s.taobao.com/search?initiative_id=tbindexz_20160224&ie=utf8&spm=a21bo.7724922.8452-taobao-item." \
               "2&sourceId=tb.index&search_type=item&ssid=s5-e&commend=all&imgfile=&q=" + search_word + "&suggest=history_1&_input_charset=utf-8&wq=s&suggest_query=s&source=suggest&s="

    i = 1
    while i < 3:
        resp=requests.get(url) 
        html=resp.text 
        regex = r'g_page_config =(.+)' 
        items = re.findall(regex, html)  
        items = items.pop().strip()  
        items = items[0:-1]  
        items = json.loads(items)
        try: 
            data = DataFrame(items['mods']['itemlist']['data']['auctions'], columns=['raw_title', 'view_price'])
        except:
            data = DataFrame(items['mods']['grid']['data']['spus'], columns=['importantKey','price','title'])

        price_table = pd.concat([price_table, data])
        url = url_base + str(i * 48)
        i += 1

    file_name = 'taobao'+ search_word +'result.csv'
    price_table.to_csv(file_name, header=False,encoding='utf-8-sig')

#boqi search
class boqi_search(object):
    """docstring for boqi_search"""
    def __init__(self, search_word):
        self.search_word = search_word
        self.id_list = []
        self.url = ('http://shop.boqii.com/search?keyword=' + self.search_word + '&cid=0&bid=0&aid=0').requests.get.decode()
        self.csv_columns = ['NAME',
                    # 'SALE_PRICE',
                    'SIZE',
                    'ORIGINAL_PRICE',
                    #'AVAILABILITY',
                    'URL']
        self.extracted_data = []
    

    def get_product_id(self):
        self.page = requests.get(self.url,headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'})
        self.soup = BeautifulSoup(self.page.text, "html.parser")

        for tags in self.soup.find_all("div",{"class":"product_list_container"}):
            tag_name = tags.find_all("p",{"class":"product_active"})

            for name in tag_name:
            # print (b)
                print (name["tid"])
                self.id_list.append(name["tid"])
            # print soup.find('span', {"class": "thisClass"})['title']

    def BoqiParser(self, url):
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}
        page = requests.get(url,headers=headers)

        while True:
            sleep(3)
            try:

                doc = html.fromstring(page.content)

                XPATH_NAME = '//*[@id="content"]/div[2]/div[1]/div[2]/div[1]/text()'
            # XPATH_SALE_PRICE = '//*[@id="bqPrice"]/text()'
                XPATH_ORIGINAL_PRICE = '//*[@id="shPrice"]/text()'
                XPATH_SIZE = '//*[@id="001"]/div[2]/div[2]/div/div[1]/div[2]/p[2]/span[1]/text()'
            #XPATH_AVAILABILITY = '//div[@id="availability"]//text()'

                RAW_NAME = doc.xpath(XPATH_NAME)
            # RAW_SALE_PRICE = doc.xpath(XPATH_SALE_PRICE)
                RAW_SIZE = doc.xpath(XPATH_SIZE)
                RAW_ORIGINAL_PRICE = doc.xpath(XPATH_ORIGINAL_PRICE)
            #RAw_AVAILABILITY = doc.xpath(XPATH_AVAILABILITY)

                NAME = ' '.join(''.join(RAW_NAME).split()) if RAW_NAME else None
            # SALE_PRICE = ' '.join(''.join(RAW_SALE_PRICE).split()).strip() if RAW_SALE_PRICE else None
                SIZE = ' > '.join([i.strip() for i in RAW_SIZE]) if RAW_SIZE else None
                ORIGINAL_PRICE = ''.join(RAW_ORIGINAL_PRICE).strip() if RAW_ORIGINAL_PRICE else None


            # if not ORIGINAL_PRICE:
            #     ORIGINAL_PRICE = SALE_PRICE

                if page.status_code!=200:
                    raise ValueError('captha')
                data = {
                    'NAME':NAME,
                    # 'SALE_PRICE':SALE_PRICE,
                    'SIZE':SIZE,
                    'ORIGINAL_PRICE':ORIGINAL_PRICE,

                    }

                return data
            except Exception as e:
                print (e)

    def Readid(self):

        for i in self.id_list:
            self.url_search = "http://shop.boqii.com/product-" + i + ".html"
        #print "Processing: "+url
            self.extracted_data.append(self.BoqiParser(self.url_search))
            sleep(5)
    

        with open('boqi_csv', 'w', newline='',encoding='utf-8-sig') as csvfile:
            self.writer = csv.DictWriter(csvfile, fieldnames=self.csv_columns)
            self.writer.writeheader()
            for data in self.extracted_data:
                self.writer.writerow(data)
#amazon search
class amazon_search(object):
    """docstring for boqi_search"""
    def __init__(self, search_word):
        self.search_word = search_word
        self.AMAZON_ACCESS_KEY = "AKIAJBVSXYPBD6LUXTSQ"
        self.AMAZON_SECRET_KEY = "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"
        self.AMAZON_ASSOC_TAG = "wawwawwaw1204-20"
        self.amazon = AmazonAPI(self.AMAZON_ACCESS_KEY, self.AMAZON_SECRET_KEY, self.AMAZON_ASSOC_TAG)
        self.AsinList = []
        self.extracted_data = []
    

    def get_searchword_from_user(self):

        self.products = self.amazon.search_n(20, Keywords=self.search_word, SearchIndex='All')
        for i, self.product in enumerate(self.products):
            print (self.product.asin)
            self.AsinList.append(self.product.asin)

    def AmazonParser(self,url):
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}
        page = requests.get(url,headers=headers)

        while True:
            sleep(3)
            try:
                doc = html.fromstring(page.content)

                XPATH_NAME = '//h1[@id="title"]//text()'
                # XPATH_SALE_PRICE = '//span[contains(@id,"ourprice") or contains(@id,"saleprice")]/text()'
                XPATH_ORIGINAL_PRICE = '//td[contains(text(),"List Price") or contains(text(),"M.R.P") or contains(text(),"Price")]/following-sibling::td/text()'
                XPATH_SIZE = '//*[@id="variation_size_name"]/div/span/text()'

                RAW_NAME = doc.xpath(XPATH_NAME)
            # RAW_SALE_PRICE = doc.xpath(XPATH_SALE_PRICE)
                RAW_SIZE = doc.xpath(XPATH_SIZE)
                RAW_ORIGINAL_PRICE = doc.xpath(XPATH_ORIGINAL_PRICE)
            #RAw_AVAILABILITY = doc.xpath(XPATH_AVAILABILITY)

                NAME = ' '.join(''.join(RAW_NAME).split()) if RAW_NAME else None
            # SALE_PRICE = ' '.join(''.join(RAW_SALE_PRICE).split()).strip() if RAW_SALE_PRICE else None
                SIZE = ' > '.join([i.strip() for i in RAW_SIZE]) if RAW_SIZE else None
                ORIGINAL_PRICE = ''.join(RAW_ORIGINAL_PRICE).strip() if RAW_ORIGINAL_PRICE else None

                if page.status_code!=200:
                    raise ValueError('captha')
                data = {
                    'NAME':NAME,
                    # 'SALE_PRICE':SALE_PRICE,
                    'SIZE':SIZE,
                    'ORIGINAL_PRICE':ORIGINAL_PRICE,

                    }

                return data
            except Exception as e:
                print (e)

    def ReadAsin(self):
        self.csv_columns = ['NAME',
                    # 'SALE_PRICE',
                    'SIZE',
                    'ORIGINAL_PRICE',
                    #'AVAILABILITY',
                    'URL']

        for asin in self.AsinList:
            self.url_search = "http://www.amazon.com/dp/"+asin
         

            self.extracted_data.append(self.AmazonParser(self.url_search))
            sleep(5)

        with open(self.search_word + '_csv', 'w') as csvfile:
            self.writer = csv.DictWriter(csvfile, fieldnames=self.csv_columns)
            self.writer.writeheader()
            for data in self.extracted_data:
                self.writer.writerow(data)

class JdPrice(object):
    """
    对获取京东商品价格进行简单封装
    """
    def __init__(self, search_word):
        self.search_word = search_word
        self.url = ('http://search.jd.com/Search?keyword=' + self.search_word + '&enc=utf-8&wq=' + self.search_word)
        self.product_list = []
        self.price_list = []
        self.p_dict = {}
        # self._response = requests.get(self.url)
        # self.html = self._response.text
 

    def get_product_price(self):

        page = requests.get(self.url,headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'})
        page.encoding='utf-8'
        soup = BeautifulSoup(page.text, "html.parser")
        for tag1 in soup.find_all("div",{"class":"gl-i-wrap"}):
            for tag_name in tag1.find_all("div",{"class":"p-name p-name-type-2"}):
                print ((tag_name.text).encode(encoding="utf-8").decode())
                self.product_list.append(tag_name.text)

            for tag_name in tag1.find_all("div",{"class":"p-price"}):
                # print (tag_name.text)
                self.price_list.append(tag_name.text)
        self.p_dict = dict(zip(self.product_list, self.price_list))
        for item in self.p_dict:
            print(type(item))

        # self.csv_columns = ['product','price']

        with open('JD' + self.search_word + '.csv', 'w', newline='',encoding='utf-8-sig') as csv_file:
            # self.writer = csv.DictWriter(csvfile, fieldnames=self.csv_columns)
            # self.writer.writeheader()
            self.writer = csv.writer(csv_file)
            for key, value in self.p_dict.items():
                self.writer.writerow([key, value])




@app.route('/')
def index():
    return 'Error Page'
#
# @app.route('/hello')
# def hello():
#     return 'Hello, World'
#
# @app.route('/user/<username>')
# def show_user_profile(username):
#     # show the user profile for that user
#     return 'User %s' % username

@app.route('/main')
def main(key=None):
    # show the post with the given id, the id is an integer
    return render_template('main.html', key=key)

@app.route('/search', methods=['POST', 'GET'])
def search(name=None):
    if request.method == 'POST':
        session['search key'] = request.form['search key']
        #search_word = string(request.args.get('search key', ''))
        assert isinstance(search_word, str)
        #return search_word

        return render_template('search.html', name=name)

    else:
        return 'Please enter a product name'

@app.route('/key', methods=['POST', 'GET'])
def key():
#     error = None
    if request.method == 'POST':
        web_key = request.form['web key']
        if web_key == 'taobao':
            taobao_search(session['search key'])
            return render_template('key.html', key=session['search key'])
        elif web_key == 'boqi':
            boqi_obj = boqi_search(session['search key'])
            boqi_obj.get_product_id()
            boqi_obj.Readid()
            return render_template('key.html', key=session['search key'])
        elif web_key == 'amazon':
            amazon_obj = amazon_search(session['search key'])
            amazon_obj.get_searchword_from_user()
            amazon_obj.ReadAsin()
            return render_template('key.html', key=session['search key'])
        elif web_key == 'jingdong':
            jd_obj = JdPrice(session['search key'])
            jd_obj.get_product_price()
            return render_template('key.html', key=session['search key'])
    else:
        return render_template('main.html')



# @app.route('/back', methods=['POST','GET'])
# def contact(name=None):
#     if request.method == 'POST':
#         if request.form['submit'] == 'Do Something':
#             return render_template('search.html', name=name)
#         elif request.form['submit'] == 'Do Something Else':
#             return render_template('main.html', name=name)
#         else:
#             pass # unknown
#     # elif request.method == 'GET':
#     #     return render_template('main.html', form=form)



app.secret_key = '1234567890'

if __name__ == '__main__':
    app.run(host='0.0.0.0')
