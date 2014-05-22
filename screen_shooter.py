#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Gilmullin T.M.

# This program opens URL, finds all links in <a> tag, and then goes to those links and makes screenshot of pages.


from selenium import webdriver

import lxml.html
import os
import sys
import urllib
import urllib.request
import argparse
from datetime import datetime


# Start URL for screen shooter.
startURL = 'http://forworktests.blogspot.com/'

# Depth of link's tree, [0, +oo)
depth = 1

# Method = 'CSS', 'xPath'
method = 'CSS'

# List links
linksTree = {}

# Working Directory.
workDir = os.path.abspath(os.curdir)

# Full Path to screen's directory
resultPath = workDir + '/screens'

# One WebDriver browser.
browser = None

# WebDriver browser string (*firefox, *ie, *chrome). *firefox by default.
browserString = '*firefox'


def ParseArgs():
    """
    Function get and parse command line keys.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--URL", type=str,
                        help="Start URL for screen-shooter. For example: http://forworktests.blogspot.com/")
    parser.add_argument("-d", "--depth", type=int,
                        help="Depth for link's tree from interval [0..+оо]. Start URL has the highest depth.")
    parser.add_argument("-m", "--method", type=str,
                        help="Method = CSS: use lxml CSS finder, Method = xPath: use WebDriver xPath finder.")
    parser.add_argument("-b", "--browser", type=str,
                        help="Browser for testing (*firefox, *ie, *chrome). *firefox by default.")
    args = parser.parse_args()
    global startURL
    global depth
    global method
    global browserString
    if args.URL != None:
        startURL = args.URL
    if (args.depth != None) and (args.depth >= 0):
        depth = args.depth
    else:
        depth = 1
    if (args.method != None) and ((args.method == 'CSS') or (args.method == 'xPath')):
        method = args.method
    else:
        method = 'CSS'
    if (args.browser == '*chrome') or (args.browser == '*ie'):
        browserString = args.browser
    else:
        browserString = '*firefox'


def LinksCrawlerByXPath(startURL='http://forworktests.blogspot.com/', depth=1, tree={}):
    '''
    Function LinksCrawlerByXPath(startURL, depth, tree) looks for all links by xPath, starting with an initial URL
    and then passing on these links looks for other links.
    initial_url         URL for crawler start. For example: 'http://forworktests.blogspot.com/'
    initial_depth       Scan depth
    '''
    global browser
    if (depth <= 0) or (browser == None):
        tree[startURL] = None
        return 0
    try:
        browser.get(startURL)
        tree[startURL] = {}
    except:
        tree[startURL] = 'Connect error'
        return 1
    try:
        # get links by xPath
        allLinks = browser.find_elements_by_xpath("//a")
        hrefs = []
        hrefs = [x.get_attribute('href') for x in allLinks if x.get_attribute('href') not in hrefs]
        for href in hrefs:
            if not href.startswith('http'):
                href = startURL + href
            LinksCrawlerByXPath(href, depth - 1, tree[startURL])
        return 0
    except:
        tree[startURL] = 'Parse error'
        return 1


def LinksCrawlerByCSS(startURL='http://forworktests.blogspot.com/', depth=1, tree={}):
    '''
    Function LinksCrawlerByCSS(startURL, depth, tree) looks for all links by CSS, starting with an initial URL
    and then passing on these links looks for other links.
    initial_url         URL for crawler start. For example: 'http://forworktests.blogspot.com/'
    initial_depth       Scan depth
    '''
    if (depth <= 0):
        tree[startURL] = None
        return 0
    try:
        raw_page = urllib.request.urlopen(startURL).read()
        tree[startURL] = {}
    except:
        tree[startURL] = 'Connect error'
        return 1
    try:
        page = lxml.html.document_fromstring(raw_page)
        # get links from css
        hrefs = []
        hrefs = [elem.get('href') for elem in page.cssselect('a') if
        (((elem.get('href') != None) or (elem.get('href') == '')) and
         (elem.get('href') not in hrefs))]
        for href in hrefs:
            if not href.startswith('http'):
                href = startURL + href
            LinksCrawlerByCSS(href, depth - 1, tree[startURL])
        return 0
    except:
        tree[startURL] = 'Parse error'
        return 1


def GetScreen(nameOfScreen='screen.png'):
    """
    Function gets screenshot from browser and create file by format: depth_<num>_index_<num>.png
    Screens put into dir: <project_root>/screens/<date_time>/
    """
    global resultPath
    global browser
    try:
        browser.get_screenshot_as_file(nameOfScreen)
        print('Screenshot created: %s' % nameOfScreen)
        return 0
    except:
        print('Can not create screenshot-file!')
        return 1


def MakeAllScreens(screenDir='screens/1', depth=1, tree={}):
    """
    Function gets screenshot from all pages from link's tree.
    """
    global resultPath
    global browser
    if (depth < 0) or tree == {}:
        return 0
    try:
        index = 0
        for href in tree:
            browser.get(href)
            screenFile = screenDir + '/' + 'depth_' + str(depth) + '_index_' + str(index)
            if screenFile[-4:] != '.png':
                screenFile = screenFile + '.png'
            GetScreen(screenFile)
            MakeAllScreens(screenDir, depth - 1, tree[href])
            index += 1
    except:
        print('Error while capturing process!')
        return 1


def OpenBrowser(opTimeout=10, browserString='*firefox', ffProfile=None):
    """
    Commands for opening WebDriver browser.
    """
    global browser
    try:
        # Get new browser instance and put it into browser array. One browser for one thread.
        if browserString == '*chrome':
            chromeOptions = webdriver.ChromeOptions()
            chromeOptions.add_argument('--start-maximized')
            chromeOptions.add_argument('--log-path=' + workDir + '/browser_drivers/chromedriver.log')
            browser = webdriver.Chrome(executable_path=workDir + '/browser_drivers/chromedriver.exe',
                                       chrome_options=chromeOptions)
        elif browserString == '*ie':
            browser = webdriver.Ie(executable_path=workDir + '/browser_drivers/IEDriverServer.exe',
                                   log_file=workDir + '/browser_drivers/iedriver.log')
            browser.maximize_window()
        else:
            ffp = webdriver.FirefoxProfile(ffProfile)
            browser = webdriver.Firefox(firefox_profile=ffp, timeout=opTimeout)
            browser.maximize_window()
        print('command: OpenBrowser, status: oK')
        return 0
    except Exception as e:
        print('command: OpenBrowser, status: error')
        return 1


def CloseBrowser():
    """
    Try to close WebDriver browser.
    """
    global browser
    if browser != None:
        try:
            browser.close()
            browser = None
            print('command: CloseBrowser, status: oK')
            return 0
        except Exception as e:
            print('command: CloseBrowser, status: error')
            return 1


def Main():
    """
    Goto URL, find all links in <a> tag, and then goes to those links and makes screenshot of pages.
    """
    global startURL
    global depth
    global method
    global linksTree
    global browser
    global browserString

    status = 0
    startTime = datetime.now()
    print('Start time: ' + str(startTime))
    try:
        # Open browser (only for Selenium WebDriver) and find all links in every page.
        status += OpenBrowser(10, browserString, None)
        if method == 'CSS':
            status += LinksCrawlerByCSS(startURL, depth, linksTree)
        elif method == 'xPath':
            status += LinksCrawlerByXPath(startURL, depth, linksTree)
        else:
            pass

        # Going by every link and capture screenshot to screenDir
        screenDir = resultPath
        if not (os.path.exists(screenDir)):
            os.mkdir(screenDir)
        screenDir = screenDir + '/' + datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
        if not (os.path.exists(screenDir)):
            os.mkdir(screenDir)
        if status == 0:
            MakeAllScreens(screenDir, depth, linksTree)

    except:
        print('It were errors during the program execution.')
        sys.exit(1)

    finally:
        CloseBrowser()
        finishTime = datetime.now()
        print('Finish time: ' + str(finishTime))
        print('Duration: ' + str(finishTime - startTime))
        sys.exit(status)


# Run this script if you want to running screen-shooter.
if __name__ == "__main__":
    ParseArgs()
    Main()