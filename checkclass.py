#! /usr/bin/env python
import sys
import time
import re
import json
from multiprocessing import Process, Queue
import datetime
# from pprint import pprint

import requests
from bs4 import BeautifulSoup

from course import Course, Section
from Emailcore import Emailcore


def getJson(kwargs=None):
    payload = {'campus': 'NB', 'level': 'U', 'semester': '92015'}
    if kwargs is not None:
        payload.update(kwargs)
    else:
        payload['subject'] = 198

    deptUrl = 'https://sis.rutgers.edu/soc/courses.json'

    try:
        response = requests.get(deptUrl, params=payload)
        j = response.json()
    except KeyboardInterrupt:
        sys.exit()
    except:
        print("error connecting/ loading json")
        j = None

    return j


def login():
    s = requests.Session()
    s.headers.update({
        'Host': 'cas.rutgers.edu',
        'Origin': 'https://cas.rutgers.edu',
        'Referer': 'https://cas.rutgers.edu/login',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.8,es;q=0.6'
        })

    body = {
        'authenticationType': 'Kerberos',
        '_currentStateId': None,
        '_eventId': 'submit'
    }

    with open('/home/itslikeroar/dev/ru/info.json') as f:
        info = json.load(f)

    body['username'] = info['netid']
    body['password'] = info['netidpw']

    loginUrl = 'https://cas.rutgers.edu/login'
    loginPage = s.get(loginUrl)
    if not loginPage.ok:
        print("could not load CAS")
        raise IOError

    loginHtml = BeautifulSoup(loginPage.content)
    body['lt'] = loginHtml.select("form#fm1")[0].select("input")[3].get("value")

    r = s.post(loginUrl, data=body)

    if not loginPage.ok:
        print("could not login")
        raise IOError

    loginSuccess = BeautifulSoup(r.content)

    if loginSuccess.find(text=re.compile("successfully")) is None:
        print("login unsuccessful")
        raise IOError
        return None
    else:
        return s


def register(section):
    try:
        session = login()
        if session is not None:
            webregUrl = 'https://sims.rutgers.edu/webreg/editSchedule.htm'
            body = {'semesterSelection': '92015', 'submit': 'Continue &#8594;'}
            webreg = session.post(webregUrl, data=body)
            if not webreg.ok:
                print('problem loading webreg')
                raise IOError

            registerUrl = 'https://sims.rutgers.edu/webreg/addCourses.htm'
            registerData = {
                'coursesToAdd[0].courseIndex': section.index,
                'coursesToAdd[1].courseIndex': None,
                'coursesToAdd[2].courseIndex': None,
                'coursesToAdd[3].courseIndex': None,
                'coursesToAdd[4].courseIndex': None,
                'coursesToAdd[5].courseIndex': None,
                'coursesToAdd[6].courseIndex': None,
                'coursesToAdd[7].courseIndex': None,
                'coursesToAdd[8].courseIndex': None,
                'coursesToAdd[9].courseIndex': None
            }

            registerResponse = session.post(registerUrl, data=registerData)
            if registerResponse.ok:
                print('register request sent for', section)
                return True
            else:
                print('register request failed')
                return False
    except:
        print('unable to register to', section)
        return False

def getOpenCloseTimes(currentTime: datetime.datetime):
    if currentTime.weekday() <= 4:  # weekdays
        open, close = datetime.time(6, 25), datetime.time.max
    else:  # weekends
        open, close = datetime.time(6, 25), datetime.time(18, 30)
    return open, close

def webregIsOpen(currentTime: datetime.datetime):
    """ Compares currentTime to hours of operation

    I'm too lazy to make this smart and check for stuff on
    the website itself... so just gonna hardcode some datetimes
    """

    open, close = getOpenCloseTimes(currentTime)
    if currentTime.time() > close or currentTime.time() < open:
        return False
    else:
        return True

def getNextOpenTime(currentTime: datetime.datetime):
    open, close = getOpenCloseTimes(currentTime)
    if currentTime.time() > close or currentTime.time() < open:
        nextday = currentTime + datetime.timedelta(1)
        return datetime.datetime.combine(nextday, open)
    else:
        return currentTime


def busySleep(startTime: datetime.datetime, wakeTime: datetime.datetime):
    """ A busy loop to prevent hanging when standby occurs """
    currentTime = datetime.datetime.now()
    while currentTime > startTime and currentTime < wakeTime:
        print("last checked time at " + str(datetime.datetime.now()))
        time.sleep(60)

def worker(q):
    classes = {}
    memo = {}
    # print(courses, courses[0].subject, courses[0].course)

    while True:
        t = datetime.datetime.now()

        if not webregIsOpen(t):
            print("gonna sleep for a bit")
            busySleep(t, getNextOpenTime(t))

        while not q.empty():
            try:
                item = q.get()
            except:
                continue

            classes[item.course] = item
            subject = item.subject

        checkClasses(classes.values(), memo, subject)

        time.sleep(15)


def checkClasses(classList, memo, subject):
    if len(classList) == 0:
        print("No courses. Exiting")
        sys.exit()

    jclasses = None
    while jclasses is None:
        jclasses = getJson({'subject': subject})
        if jclasses is not None and len(jclasses) == 0:
            print(datetime.datetime.now(), "issue with the json rutgers is providing, gonna wait a minute")
            time.sleep(60)

    # update time
    t = datetime.datetime.now()

    # print([(x.subject, x.course) for x in classList])

    sections = {}

    # pprint(jclasses[8])
    for item in classList:
        if isinstance(item, Section):
            sections[item.index] = item
            continue

        item.getInfo(jclasses)

        # import pprint
        # pprint.pprint(info['sections'])

        for section in item.sections.values():
            sections[section.index] = section

    for section in sections.values():
        section.getInfo(jclasses)
        # isDifferent = False
        if (section.index in memo and memo[section.index] is not None and
                section.isOpen != memo[section.index]):
            # isDifferent = True

            if section.isOpen:
                status = section.courseStr() + " OPEN"
                print("############## CLASS IS OPEN ##############")
            else:
                status = section.courseStr() + " CLOSED"
                print("############## CLASS IS CLOSED ##############")

            Process(target=register, args=(section, )).start()
            # register(section)

            email = Emailcore()
            email.ESBody += status + ' since ' + t
            email.ESSubject += status
            email.setEmailContent()
            email.ConnectToServer()
            email.SendEmail()

        memo[section.index] = section.isOpen

        print("{0} | {1.title} {1.index} {1.prof} {1.isOpen}".format(
            t, section))

    print("###########################")


def main():
    subjects = {}

    if len(sys.argv) > 1:
        # classes = []
        for arg in sys.argv[1:]:
            info = arg.split(":")

            if subjects.get(info[0]) is None:
                subjects[info[0]] = []

            sub = subjects[info[0]]

            if len(info) == 3:
                sub.append(Section(info[0], info[1], info[2]))
            elif len(info) == 2:
                sub.append(Course(info[0], info[1]))
            else:
                print("Could not parse {:}".format(arg))
    else:
        subjects[198] = [
            #Course(198, 206),
            #Course(198, 314),
            #Section(198, 314, '12850')
            Section(198, 352, "03693"),
        ]

    # memo = {}
    # print(courses, courses[0].subject, courses[0].course)

    # set the signal handler
    # signal.signal(signal.SIGALRM, sigalrm_handler)

    for subject, classList in subjects.items():
        q = Queue()
        for item in classList:
            q.put(item)

        subjects[subject] = q
        Process(target=worker, args=(q,)).start()


if __name__ == '__main__':
    main()
