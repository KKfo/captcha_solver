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
            'Cookie' : 'PHPSESSID=',#erased
            'Authorization' : 'Basic ',#erased
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
        imgs[key].append(Image.open(StringIO.StringIO(line[2:-1].decode("hex"))))
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
        print(total, guess[0:3], guess[0][0]/total, guess[1][0]/total, guess[2][0]/total)
    print(word)

    return word.replace("_", "")

def separate(img):

    # count number of pixels for each column
    colPixCnts = []
    for col in range(img.size[0]):
        pixels = list(img.crop([col, 0, col+1, img.size[1]]).getdata())
        colPixCnts.append(sum(i==0 for i in pixels))
    print (colPixCnts)
    print("\n")
    # average out pixel counts for trough column
    for i in range(3, len(colPixCnts)-3, 2):
        if colPixCnts[i-3]>4 and colPixCnts[i+3]>4:
            colPixCnts[i-2:i+3] = [j+10 for j in colPixCnts[i-2:i+3]]
    print(colPixCnts)
    print("\n")
    
    # calculate all bounding boxes of all letters
    bounds = []
    left = 0
    right = 0
    for col in range(img.size[0]): # slice all letters per column
        if left==0 and colPixCnts[col]>20:  # if (begin not set) and (col has letter)
            left = col  # then letter begin
        if left!=0 and colPixCnts[col]<=20:  # if (begin is set) and (col no letter)
            right = col  # then letter end
            if right-left>8:  # if (the letter is wide enough)
                ##############################################
                print((right-left))
                top = -1
                bottom = -1
                prev = -1
                curr = -1
                for row in range(img.size[1]):  # slice single letter per row
                    pixels = list(img.crop([left, row, right, row+1]).getdata())
                    rowPixCnt = sum(i==255 for i in pixels)
                    if rowPixCnt==(right-left):  # if (row no letter)
                        curr = row
                        if (curr-prev)>(bottom-top):  # if (the letter is tall enough)
                            top = prev
                            bottom = curr
                        prev = curr
                if (img.size[1]-prev)>(bottom-top):  # if (the letter align to bottom)
                    top = prev
                    bottom = img.size[1]
                ##############################################
                bounds.append([left, top+1, right, bottom])  # top row should has letter
            left = 0
            right = 0
    print(bounds)
    
    return bounds

def prepare(im):
    im2 = Image.new("P",im.size,255)
    for x in range(im.size[1]):
        for y in range(im.size[0]):
            pix = im.getpixel((y,x))
            if pix == 1: # these are the numbers to get
                im2.putpixel((y,x),0)
    # im2 = im2.convert("RGB")
    im2 = im2.resize((im2.size[0]*8, im2.size[1]*8), Image.BILINEAR)
    # im2 = im2.resize((int(im2.size[0] / 2), int(im2.size[1] / 2)), Image.ANTIALIAS)
    # im2 = ImageEnhance.Contrast(im2).enhance(1.4)
    # im2 = ImageEnhance.Sharpness(im2).enhance(5)
    # im2 = ImageChops.invert(im2)
    # im2 = im2.filter(ImageFilter.MedianFilter(3))
    # im2 = im2.convert('P')
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
        # g = codecs.encode(bmpfile.getvalue(), 'hex_codec')
        s = codecs.encode(bmpfile.getvalue(), 'hex')
        s = codecs.decode(s)
        line = letter+"|"+s+"\n"
        if (letter!="") and (line not in lines):  # if (not skipped) and (not duplicated)
            datfile.write(line)
            print(line)
        bmpfile.close()
    datfile.close()

def vertical_cut(im):

    im = im.convert("P")
    im2 = Image.new("P",im.size,255)
    im = im.convert("P")
    temp = {}

    for x in range(im.size[1]):
        for y in range(im.size[0]):
            pix = im.getpixel((y,x))
            temp[pix] = pix
            if pix == 1: # these are the numbers to get
                im2.putpixel((y,x),0)

    # new code starts here

    inletter = False
    foundletter=False
    start = 0
    end = 0

    letters = []

    for y in range(im2.size[0]): # slice across
        for x in range(im2.size[1]): # slice down
            pix = im2.getpixel((y,x))
            if pix != 255:
                inletter = True
        if foundletter == False and inletter == True:
            foundletter = True
            start = y

        if foundletter == True and inletter == False:
            foundletter = False
            end = y
            letters.append((start,end))

        inletter=False

    bounds = []
    for letter in letters:
        bounds.append([ letter[0] , 0, letter[1], im2.size[1] ])

    print(bounds)
    return bounds

if __name__=="__main__":
    # if len(sys.argv) < 2:
    #     print(("usage: %s image" % (sys.argv[0])))
    #     sys.exit(2)
    # file_name = sys.argv[1]
    # img = Image.open(file_name).convert('P')
    i = 0
    while i < 3 :
        response = requests.get(imgurl, headers = headers)
        the_page = response.content
        file = BytesIO(the_page)
        img = Image.open(file)
        # img = prepare(img)
        img = img.resize((img.size[0]*4, img.size[1]*4), Image.BILINEAR)
        img.show()
        # bounds = separate(img)
        bounds = vertical_cut(img)
        _train(img, bounds)
        i = i + 1
