import os
import time
from sys import platform
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from urllib.parse import quote
import random

class Person():
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.id_ = kwargs.get('id_', '')
        self.link = kwargs.get('link', '')
        self.img = kwargs.get('img', '')
        self.job = kwargs.get('job', '')
        self.skills = kwargs.get('skill', '')
        self.parents = kwargs.get('parents', [])

    def __str__(self):
        return self.name + '  |  ' + self.job + ("   |  None img" if self.img is None else "")

    def show_person(self):
        print('------------------')
        print("Name: ", self.name)
        print("id: ", self.id_)
        print("img: ", self.img)
        print("link: ", self.link)
        print("job: ", self.job)
        print("parents: ", self.parents)
        print('------------------\n')
def random_base(base, var):
    return random.random()*var + base
def random_sleep(base, var):
    time.sleep(random_base(base, var))


def quote_https(url):
    return url[:8] + quote(url[8:])

def get_webdriver(headless):

    # if platform == "linux":
    #     # linux64
    #     path = "geckodriver_linux64"
    # elif platform == "linux2":
    #     # linux32
    #     path = "geckodriver_linux32"
    # elif platform == "darwin":
    #     # OS X
    #     path = "geckodriver_mac"
    # elif platform == "win32":
    #     # Windows..
    #     path = "geckodriver.exe"

    # path = os.path.join(os.getcwd(), 'webdrivers', path)
    # print(path)
    # if headless:
    #     options = Options()
    #     options.add_argument('-headless')
    #     return webdriver.Firefox(firefox_options=options, executable_path=path)
    # else:
    #     return webdriver.Firefox(executable_path=path)

    return webdriver.Firefox()


def get_profile_img2(bsObj):
    parent_img = bsObj.find(class_="presence-entity__image")

    if parent_img != None:
        parent_img = parent_img.attrs.get("style")
        if 'url' in parent_img:
            st = parent_img.index('"') + 1
            end = parent_img.index('"', st)
            parent_img = parent_img[st:end]
        else:
            parent_img = None

    return parent_img

def tr_link(link):
    start = len("https://www.linkedin.com/in/")
    try:
        end = link.index('/', start)
    except ValueError:
        end = len(link)
    return link[start:end]
