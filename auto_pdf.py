from selenium import webdriver
from PIL import Image
import tempfile
from io import BytesIO
from fpdf import FPDF
import argparse
import requests
from os import walk
import zipfile
import json

par = argparse.ArgumentParser()
par.add_argument("url",type=str,action="store",help="Please give me a double quoted url to work on.")
par.add_argument("--out","-o",type=str,action="store")
par.add_argument("--notheadless","-nh",action="store_true")
args = par.parse_args()

#Similar to iPad, adapted to A4 format
width = 768
height = 1086

cur_pos=0

pdf = FPDF()
pdf.set_auto_page_break(0)

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument("--test-type")
if not args.notheadless:
    options.add_argument("--headless")
options.binary_location = "/usr/bin/chromium"

r = requests.get("https://github.com/gorhill/uBlock/releases/latest")
uBlock_latest = r.url.split("/")[-1]
_, dirs, filenames = next(walk("."))
sub="uBlock"
f_name = next((s for s in filenames if sub in s), None)
d_name = next((s for s in dirs if sub in s), None)
if d_name is not None:
    j_obj = json.loads(d_name+"manifest.json")
    if j_obj["version"] != uBlock_latest:
        print("Get latest uBlock Origin from https://github.com/gorhill/uBlock/releases/latest .")
    options.add_argument(f"--load-extension={d_name}")
else:
    if f_name is not None:
        if uBlock_latest not in f_name:
            print("Get latest uBlock Origin from https://github.com/gorhill/uBlock/releases/latest .")
        with zipfile.ZipFile(f_name, 'r') as zip_ref:
            zip_ref.extractall(".")
        _, dirs, _ = next(walk("."))
        d_name = next((s for s in dirs if sub in s), None)
        options.add_argument("--load-extension="+d_name)
    else:
        print("uBlock Origin not found, not using.")

#Getting the url
driver = webdriver.Chrome(options=options)
driver.set_window_size(width, height)
driver.get(args.url)
if args.notheadless:
    inp = input("You are running this in \"not headless mode\".\nThis probably means you had some problems with cookie stuff.\n \
    \rThe browser will open the page and wait for you to complete necessary procedures.\n \
    \rWhen everything is ready came back and type something here: ")
    if inp is None:
        quit()
doc_height = driver.execute_script("return document.body.scrollHeight")
if args.out is None:
    args.out = driver.title 

#Screenshotting and saving into pdf
while doc_height>=cur_pos:
    png = driver.get_screenshot_as_png()
    
    #Buffers seems to not work with fpdf, found this workaround
    fo = tempfile.NamedTemporaryFile(suffix=".png")
    im = Image.open(BytesIO(png))
    im.save(fo.name)

    pdf.add_page()
    pdf.image(fo.name,0,0,210,297)

    fo.close()  

    cur_pos+=height
    driver.execute_script(f"window.scrollTo(0, {cur_pos})") 

driver.close()

pdf.output(args.out, "F")