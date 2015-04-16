#! /usr/bin/env python
import requests, time, sys, signal
from multiprocessing import Process, Queue
from datetime import datetime
from pprint import pprint
from course import Course, Section
from Emailcore import Emailcore

def sigalrm_handler(signal, frame):
    print('alarm received!')

def getJson(kwargs = None):
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

def worker(q):
    classes = {}
    memo = {}
    # print(courses, courses[0].subject, courses[0].course)

    # set the signal handler
    signal.signal(signal.SIGALRM, sigalrm_handler)

    while True:
        t = datetime.now()
        # figures out how much time it needs to wait until it should start
        # checking for classes being open again, since webreg opens and closes
        sec = (6 * 3600) + (26 * 60)
        if t.hour <= 6 and t.minute < 25:
            print('ohai')
            sec -= (t.hour * 3600) + (t.minute * 60) + t.second
        elif (t.weekday() == 5 or t.weekday() == 6) and (t.hour >= 18 and t.minute > 30):
            print('here')
            sec += ((23 - t.hour) * 3600) + ((59 - t.minute) * 60) + (59 - t.second)
        if sec != (6 * 3600) + (26 * 60):
            signal.alarm(sec)
            print('set alarm for {0} hours {1} min and {2} sec from now ({3}:{4}) at {5}:{6}'.format(
                sec//3600, (sec//60) % 60, sec % 60, (sec//3600 + t.hour) % 24,((sec//60) + t.minute) % 60,
                t.hour, t.minute))
            signal.pause()

        while not q.empty():
            try:
                item = q.get()
            except:
                continue

            classes[item.course] = item
            subject = item.subject
        
        checkClasses(classes.values(), memo, subject)

        time.sleep(30)

def checkClasses(classList, memo, subject):
    if len(classList) == 0:
        print("No courses. Exiting")
        sys.exit()

    jclasses = None
    while jclasses is None:
        jclasses = getJson({'subject': subject})

    # update time
    t = datetime.now()

    #print([(x.subject, x.course) for x in classList])

    sections = {}

    #pprint(jclasses[8])
    for item in classList:
        if isinstance(item, Section):
            sections[item.index] = item
            continue

        info = item.getInfo(jclasses)

        # import pprint
        # pprint.pprint(info['sections'])

        for section in item.sections.values():
            sections[section.index] = section

    for section in sections.values():
        section.getInfo(jclasses)
        # isDifferent = False
        if section.index in memo and memo[section.index] is not None and section.isOpen != memo[section.index]:
            # isDifferent = True
            if section.isOpen:
                status = section.courseStr() + " OPEN"
            else:
                status = section.courseStr() + " CLOSED"
            email = Emailcore()
            email.ESBody += status + ' since ' + t
            email.ESSubject += status
            email.setEmailContent()
            email.ConnectToServer()
            email.SendEmail()

        memo[section.index] = section.isOpen

        print("{0} | {1.title} {1.index} {1.prof} {1.isOpen}".format(t, section))

    print("###########################")

def main():
    subjects = {}

    if len(sys.argv) > 1:
        classes = []
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
        subjects[198] = [Course(198, 206), Course(198, 314), Section(198, 314, '12850')]

    memo = {}
    # print(courses, courses[0].subject, courses[0].course)

    # set the signal handler
    #signal.signal(signal.SIGALRM, sigalrm_handler)

    for subject, classList in subjects.items():
        q = Queue()
        for item in classList:
            q.put(item)

        subjects[subject] = q
        Process(target=worker, args=(q,)).start()
    

if __name__ == '__main__':
    main()
