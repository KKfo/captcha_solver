import requests
from PIL import Image, ImageEnhance, ImageChops, ImageFilter
from io import BytesIO, StringIO
import time
import sys, os
import codecs

url = 'http://d1222391-23d7-46de-abef-73cbb63c1862.levels.pathwar.net'
imgurl = url + '/captcha.php'

headers = { 'Host' : 'd1222391-23d7-46de-abef-73cbb63c1862.levels.pathwar.net',
            'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64; rv:37.0) Gecko/20100101 Firefox/37.0',
            'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language' : 'en-US,en;q=0.5',
            'Accept-Encoding' : 'gzip, deflate',
            'DNT' : '1',
            'Referer' : 'http://http://d1222391-23d7-46de-abef-73cbb63c1862.levels.pathwar.net/',
            'Cookie' : 'PHPSESSID=', #erased cookie
            'Authorization' : 'Basic ', #used to have a token here
            # 'Connection' : 'keep-alive',
            'Content-Type' : 'application/x-www-form-urlencoded' }

def recognize(img, bounds):

    # read dataset of images for each letter
    imgs = {}
    datfile = open("ads.dat", "rt")
    line = datfile.readline()
    while line!="":
        key = line[0]
        if key not in imgs:
            imgs[key] = []
        s = codecs.encode(StringIO(line[2:-1]).getvalue())
        s = codecs.decode(s, 'hex')
        imgs[key].append(Image.open(BytesIO(s)))
        line = datfile.readline()
    datfile.close()

    # calculate difference with dataset for each boundbox
    word = ""
    for bound in bounds:
        guess = []
        total = (img.crop(bound).size)[0]*(img.crop(bound).size)[1]*1.0
        for key in imgs:
            for pattern in imgs[key]:
                diff = ImageChops.difference(img.crop(bound), pattern.resize(img.crop(bound).size, Image.NEAREST))
                pixels = list(diff.getdata())
                samePixCnt = sum(i==0 for i in pixels)
                guess.append([samePixCnt, key])
        guess.sort(reverse=True)
        word = word+guess[0][1]
        #print(total, guess[0:3], guess[0][0]/total, guess[1][0]/total, guess[2][0]/total)
    # print(word)

    return word.replace("_", "")


def prepare(im):
    im = im.convert("P")
    im2 = Image.new("P",im.size,255)

    for x in range(im.size[1]):
        for y in range(im.size[0]):
            pix = im.getpixel((y,x))
            if pix == 1: # these are the numbers to get
                im2.putpixel((y,x),0)

    return im2

def _train(img, bounds):
    datfile = open("ads.dat", "rt")
    lines = datfile.readlines()
    datfile.close()

    datfile = open("ads.dat", "at")
    for bound in bounds:
        img.crop(bound).show()
        letter = input("Type in the letters you see in the image above (ENTER to skip): ")        
        bmpfile = BytesIO()
        img.crop(bound).save(bmpfile, format='BMP')
        s = codecs.encode(bmpfile.getvalue(), 'hex')
        s = codecs.decode(s)
        line = letter+"|"+s+"\n"
        if (letter!="") and (line not in lines):  # if (not skipped) and (not duplicated)
            datfile.write(line)

        bmpfile.close()
    datfile.close()

def horizontal_cut(limits, im2):
    left = limits[0]
    right = limits[1]
    inletter = False
    foundletter = False
    start= 0
    end = 0
    size_x = im2.size[1]
    
    for x in range(size_x): # slice down
        for y in range(left,right): # slice across
            pix = im2.getpixel((y,x))
            if pix != 255:
                inletter = True

        if foundletter == False and inletter == True:
            foundletter = True
            start = x

        if foundletter == True and inletter == False:
            foundletter = False
            end = x
            return (start,end)
        
        inletter=False
        

def vertical_cut(im2):

    inletterv = False
    foundletterv = False
    startv = 0
    endv = 0
    vertical = []
    horizontal = []
    size_y = im2.size[0]
    size_x = im2.size[1]
    
    for y in range(size_y): # slice across
        for x in range(size_x): # slice down
            pixv = im2.getpixel((y,x))
            if pixv != 255:
                inletterv = True
                        
        if foundletterv == False and inletterv == True:
            foundletterv = True
            startv = y

        if foundletterv == True and inletterv == False:
            foundletterv = False
            endv = y
            vertical.append((startv,endv))
            horizontal.append(horizontal_cut((startv,endv), im2)) ## Horizontal

        inletterv=False
        inletterh=False

    bounds = []
    letters = zip(vertical, horizontal)
    for letter in letters:
        bounds.append([ letter[0][0] , letter[1][0], letter[0][1], letter[1][1] ])

    return bounds

if __name__=="__main__":
    i = 0
    if  len(sys.argv) < 2:
         train = 0
    else:
        train = 1
    while i < 6 :
        response = requests.get(imgurl, headers = headers)
        the_page = response.content
        file = BytesIO(the_page)
        img = Image.open(file)
        # img = img.resize((img.size[0]*4, img.size[1]*4), Image.BILINEAR)
        img = prepare(img)
        bounds = vertical_cut(img)
        if train:
            img.show()
            _train(img, bounds)
        else:
            passw = recognize(img, bounds)
            values = {'password' : passw }
            req = requests.post(url, data=values, headers = headers)
            if i > 999:
                test = req.text.find("passphrase")
                if test != -1:
                    print(req.text)
                    sys.exit(0)
            print("try number: %i with pass: %s" % (i, passw))
        i = i + 1
