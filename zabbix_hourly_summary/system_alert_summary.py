__author__ = 'kshk'
#!/usr/bin/env python

import zabbix_api
import sys
from optparse import OptionParser
import os
import MySQLdb
import MySQLdb.cursors
import datetime
from datetime import date, timedelta
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import smtplib
import HTML
from time import time

def SystemAlert():
    now_time = datetime.datetime.now()
    now_time4 = datetime.datetime.now() - timedelta(hours=1)
    yday_time = datetime.date.today() - datetime.timedelta(days=1)
    today = datetime.date.today()
    unix_today = today.strftime("%s")
    unix_now = now_time.strftime("%s")
    unix_4before = now_time4.strftime("%s")
    print now_time
    print yday_time
    unix_yday = yday_time.strftime("%s")
    print unix_yday
    try:
        username='apiuser'
        password='yourpassword'
        zabbix_url='http://10.42.0.180/zabbix/'
        z=zabbix_api.ZabbixAPI(server=zabbix_url)
        z.login(user=username, password=password)

    except:
        print "cannot connect.."
        sys.exit()

    host_group = z.hostgroup.get({'filter':{'name':'Anorak Servers'},
                                      'output':'extend',
                                     })
    fw=12
    table_data = []
    event_data = []
    tableS = HTML.Table(header_row=['HOST','IP','DESCRIPTION','LASTCHANGE','HOURS'])
    eventS = HTML.Table(header_row=['HOST','IP','EVENT','LASTCHANGE'])
    for i in host_group:
        #print i['groupid']
        trigger_items = z.trigger.get({'groupids':i['groupid'],
                                       'output':'extend',
                                       'only_true': 'False',
                                       'expandDescription': 'True',
                                       'expandData': 'True',
                                       'sortfield': 'lastchange',
                                       'sortorder': 'DESC',
                                      })
        event_items = z.event.get({'groupids':i['groupid'],
                                   'output':'extend',
                                   'value':0,
                                   'time_from': unix_4before,
                                   'time_till': unix_now,
                                  })

        for e in event_items:
            count = 0
            sub_trigger_items = z.trigger.get({'triggerids':e['objectid'],
                                               'output': 'extend',
                                               'expandDescription': 'True',
                                               'expandData': 'True',
                                              })

            for s in sub_trigger_items:
                shost_ip = z.hostinterface.get({ 'output': 'extend', 'filter':{'hostid':[s['hostid']]}})
                for sp in shost_ip:
                    sp_ip = sp['ip']
                count = count + 1
                print (s['host'] +"    " +s['description'] + "")
                lastT = datetime.datetime.fromtimestamp(int(s['lastchange'])).strftime('%Y-%m-%d %H:%M:%S')
                eventS.rows.append([s['host'],sp_ip,s['description'],lastT])
            #print count

        for t in trigger_items:
            #print t['hostid']
            #print t['host']
            #print t['description']
            host_ip = z.hostinterface.get({ 'output': 'extend',
                                    'filter':{'hostid':[t['hostid']]}})
            for h in host_ip:
                ip_addr = h['ip']
                #print ip_addr

            lastC = datetime.datetime.fromtimestamp(int(t['lastchange'])).strftime('%Y-%m-%d %H:%M:%S')
            #print t['lastchange']
            c_date = now_time
            l_date = datetime.datetime.strptime(lastC, "%Y-%m-%d %H:%M:%S")
            absdiff = abs(c_date - l_date)
            hours = (absdiff.days * 24 * 60 * 60 + absdiff.seconds) / 3600.0
            h = "%.2f" % hours
            #if int(hours) > 1:
            if "1" in t['value']:
                tableS.rows.append([t['host'],ip_addr,t['description'],lastC,str(h)])
            else:
                pass
    recipients = ['systems@yourcompany.com']
    sender = 'noreply@yourcompany.com'
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Systems Hourly Summary Report"
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)
    text = "hello how are you?"
    heading = "<p><strong>Events Recovered in the Last Hour</strong><br />&nbsp;</p>"
    htmlcode = str(tableS) + "\n" + heading + str(eventS)
    part1 = MIMEText(htmlcode, 'html')
    msg.attach(part1)
    s = smtplib.SMTP('127.0.0.1')
    s.sendmail(sender,recipients,msg.as_string())
    s.quit()

def main():
    SystemAlert()

if __name__ == "__main__":
    main()
