import smtplib
import sys
import json
from getpass import getpass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Emailcore(object):
   
    # defaultSubject = "CLASS "
    # defaultBody = "The class you were checking for is "
    def __init__(self):
        # print('im in email')
        u = {}
        try:
            with open('/home/itslikeroar/dev/ru/info.json') as f:
                u = json.load(f)
        except IOError:
            u['email'] = input('Email: ')
            u['pw'] = getpass()

        self.ESAddress = 'smtp.gmail.com'
        self.ESPort = 587
        self.ESUser = u['email'].split('@')[0]
        self.ESPassword = u['pw']
        self.ESFromAddress = u['email']
        self.ESSubject = ""
        self.ESBody = "The class you were checking for is "
        self.ESToAddress = u['email']
        self.setEmailContent()
        self.status = 'Idle'
        
        
    
    def setEmailContent(self):
        
        self.msg = MIMEMultipart()
        self.msg['From'] = self.ESFromAddress
        self.msg['To'] = self.ESToAddress
        self.msg['Subject'] = self.ESSubject
        self.body = self.ESBody
        self.msg.attach(MIMEText(self.body, 'plain'))
        self.text = self.msg.as_string()
        
        
    def ConnectToServer(self):

    #send the immediate confirmation email
        # print("Connecting to email server...")
        try:
            self.mailserver = smtplib.SMTP(self.ESAddress, self.ESPort)
            self.mailserver.ehlo() 
            self.mailserver.starttls() 
            self.mailserver.ehlo() 
            self.mailserver.login(self.ESUser, self.ESPassword)
            # print("Connected to email server")
        except:
            print("Connect to email server Failed", sys.exc_info()[1])
        
        
    def SendEmail(self):
        # print('getting to send email function')
        try:
            self.mailserver.sendmail(self.ESFromAddress, self.ESToAddress, self.text)
            # print('im sending it')
            self.status = 'Email Sent Successfully'
            # return (0,'SendEmail')
        except:
            print('cant send', sys.exc_info()[1])
            self.status = 'Error Sending Mail'
            return (1, 'SendEmail', str(sys.exc_info()[1]))
            
            
        
    #    send_first_email('itslikeroar2412@gmail.com','g00228389@smail.raritanval.edu')
# email = Emailcore()
# email.setEmailContent()
# email.ConnectToServer()
# email.SendEmail()
        
