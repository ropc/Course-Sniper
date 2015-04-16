class Course(object):
    def __init__(self, subject, course):
        self.subject = subject
        self.course = course
        self.path = None
        self.sections = {}

    def __str__(self):
        return self.subject + ':' + self.course
        
    def getPath(self, j):
        for i, course in enumerate(j):
            if course['courseNumber'] == str(self.course):
                self.path = i
                self.title = course['title']
                return

    def getInfo(self, j):
        if not isinstance(j, list):
            return None

        if self.path is None:
            self.getPath(j)

        info = None

        try:
            course = j[self.path]
            if course['courseNumber'] != str(self.course):
                raise IndexError
            info = course
            for section in info['sections']:
                self.sections[section['index']] = Section(self.subject, self.course, section['index'])
                self.sections[section['index']].getPath(j)
                self.sections[section['index']].isOpen = section['openStatus']
                self.sections[section['index']].prof = section['instructors']
        except:
            temp = self.path
            self.getPath(j)
            # if new path is different, try again recursively
            if temp != self.path:
                info = self.getInfo(j)

        return info


class Section(Course):
    """
    Section object holds info to quickly 
    """
    def __init__(self, subject, course, index):
        super().__init__(subject, course)
        self.index = index

    def __str__(self):
        return self.subject + ':' + self.course + ':' + self.index

    def courseStr(self):
        return super().__str__()

    def getPath(self, jclasses):
        for i, course in enumerate(jclasses):
            if course['courseNumber'] == str(self.course):
                for j, section in enumerate(course['sections']):
                    if section['index'] == self.index:
                        self.path = (i, j)
                        self.title = course['title']
                        return

    def getInfo(self, j):
        if not isinstance(j, list):
            return None

        if self.path is None:
            self.getPath(j)

        info = None

        try:
            section = j[self.path[0]]['sections'][self.path[1]]
            if section['index'] != self.index:
                raise IndexError
            self.isOpen = section['openStatus']
            self.prof = [x['name'] for x in section['instructors']]
            info = section['index']
        except:
            temp = self.path
            self.getPath(j)
            # if new path is different, try again recursively
            if temp != self.path:
                info = self.getInfo(j)

        return info