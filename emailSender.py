import smtplib, imaplib
import email.MIMEMultipart as emailMp
import email.MIMEText as emailText
import email.MIMEBase as emailBase
from email import encoders
import datetime, csv, email,time, os, glob, sys



TEMPLATE_HEAD = '''
<body style="width:100% !important; margin:0 !important; padding:0 !important; -webkit-text-size-adjust:none; -ms-text-size-adjust:none; background-color:#FFFFFF;">
<table cellpadding="0" cellspacing="0" border="0" id="backgroundTable" style="height:auto !important; margin:0; padding:0; width:100% !important; background-color:#FFFFFF; color:#222222;">
	<tr>
		<td>
         <div id="tablewrap" style="width:100% !important; max-width:600px !important; text-align:center !important; margin-top:0 !important; margin-right: auto !important; margin-bottom:0 !important; margin-left: auto !important;">
		      <table id="contenttable" width="600" align="center" cellpadding="0" cellspacing="0" border="0" style="background-color:#FFFFFF; text-align:center !important; margin-top:0 !important; margin-right: auto !important; margin-bottom:0 !important; margin-left: auto !important; border:none; width: 100% !important; max-width:600px !important;">
            <tr>
                <td width="100%">
                    <table bgcolor="#FFFFFF" border="0" cellspacing="0" cellpadding="0" width="100%">
                        <tr>
                            <td width="100%" bgcolor="#ffffff" style="text-align:center;"><a href="#"><img src="https://www.dropbox.com/s/gma19c7bdym39uq/Taelium%20Header.jpg?raw=1" width="600" alt="Taelium" style="display: block; border: 0px; outline: none; 
width: 100%; height: auto; max-width: 600px;" /></a>
                            </td>
                        </tr>
                   </table>
                   <table bgcolor="#FFFFFF" border="0" cellspacing="0" cellpadding="25" width="100%">
                        <tr>
                            <td width="100%" bgcolor="#ffffff" style="text-align:left;">
                            	<p style="color:#222222; font-size:15px; line-height:19px; margin-top:0; margin-bottom:20px; padding:0; font-weight:normal;">
                            	<br/><br/>
'''

TEMPLATE_TAIL = '''
<br/><br/>
Cheers,
<br/>
The Taelium Team
                                            </p>
                                        </td>
                                       </tr>
                                    </table>
    
                            </td>
                        </tr>
                   </table>
                   <table bgcolor="#FFFFFF" border="0" cellspacing="0" cellpadding="0" width="100%">
                        <tr>
                         
                        </tr>
                   </table>
                   <table bgcolor="#FFFFFF" border="0" cellspacing="0" cellpadding="25" width="100%">
                        <tr>
                            <td width="100%" bgcolor="#ffffff" style="text-align:left;">
                            	<p style="color:#222222; font-size:11px; line-height:14px; margin-top:0; margin-bottom:15px; padding:0; font-weight:normal;">
                                    Email not displaying correctly? <a style="color:#2489B3; font-weight:bold; text-decoration:underline;" href="#">View it in your browser.</a>
                                </p>
                            	
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        </div>
		</td>
	</tr>
</table> 
</body>
'''


FROM_ADDR = "taelium.participationform@gmail.com"

CURR_DIR = os.getcwd()
WORKING = 'emailSender_working//'
ARCHIVE = 'archive//'
FOLLOW_UP = 'followUp//'
EMAIL_SUCCESS = 'emailSuccess'
EMAIL_FAILURE = 'emailFailure'
EMAIL_SUCCESS_HEADER = ['TAELIUM TX ID', 'TAELS AMOUNT', 'ETH HASH', 'ETH AMOUNT', 'PARTICIPANT EMAIL','TIMESTAMP', 'CARRY OVER TO ICO']
EMAIL_FAILURE_HEADER = ['TAELIUM TX ID', 'TAELS AMOUNT', 'ETH HASH', 'ETH AMOUNT', 'PARTICIPANT EMAIL','TIMESTAMP', 'CARRY OVER TO ICO']
TAELIUM_SUCCESS = 'taeliumSuccess'

POLLING_INTERVAL = 60
WAIT_TIME_TO_CHECK_SENT = 10

def countdown(interval):
    for i in range(interval,-1,-1):
        sys.stdout.write("\r" +str(i) + ' seconds left to chill.')
        sys.stdout.flush()
        time.sleep(1)

def findFiles(dir):
    csvList = []

    csvDict = {}
    os.chdir(dir)
    for file in glob.glob("*.csv"):
        # csvList.append(dir+'//'+file)
        timeModified = os.path.getmtime(file)
        csvDict[timeModified] = dir+'//'+file

    sortedTimeList = csvDict.keys()
    sortedTimeList.sort()

    for eachTime in sortedTimeList:
        csvList.append(csvDict[eachTime])

    os.chdir(CURR_DIR)

    return csvList

def create_csv(filename, header):

    with open(filename, 'wb') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow(header)

def append_to_csv(fileName, data):
    with open(WORKING+fileName + '.csv', 'ab') as f:
        writer = csv.writer(f)
        writer.writerow(data)


def sendMail(server, ethTxHash, ethAmount, taelTxHash, taelAmount, participantEmail, rolloverBool):

    
    msg = emailMp.MIMEMultipart()
    
    processed_timestamp = datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S.%f")[:-3]
    
    msg['From'] = "Taelium Team"
    msg['To'] = participantEmail
    msg['Subject'] = "Thank you for your participation. Your Tx ID is " + taelTxHash +'.'
    
    # insert = 'Congratulations! You have received '+taelAmount+' Taels.'

    insert1 = '''
    Congratulations!<br /><br /> Your contribution has been processed and accepted. 
    '''

    insert2 = ''' Taels have been added to your Taelium account.<br /><br /> Thank you for supporting Taelium. <br />
<br /><br />This is a system generated email. Please do not reply to it.
    '''

    body = TEMPLATE_HEAD + insert1 + taelAmount + insert2 + TEMPLATE_TAIL
    
    msg.attach(emailText.MIMEText(body, 'html'))

   ##If want to send attachements.
    # filename = "tempicon.png"
    # attachment = open(filename, "rb")
    #
    # part = emailBase.MIMEBase('application', 'octet-stream')
    # part.set_payload((attachment).read())
    # encoders.encode_base64(part)
    # part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    #
    # msg.attach(part)
    #
    
    text = msg.as_string()
    server.sendmail(FROM_ADDR, participantEmail, text)

    print FROM_ADDR, 'sent to', participantEmail

    return [taelTxHash, taelAmount,ethTxHash,ethAmount,participantEmail,processed_timestamp, rolloverBool]


def checkSent(taelTxHashList, successFile, failureFile):
    M = imaplib.IMAP4_SSL('imap.gmail.com')

    try:
        rv, data = M.login(FROM_ADDR, "lotsoftael")
    except imaplib.IMAP4.error:
        print "LOGIN FAILED!!! "

    print rv, data

    rv, mailboxes = M.list()
    # if rv == 'OK':
    #     print "Mailboxes:"
    #     print mailboxes

    rv, data = M.select("[Gmail]/Sent Mail")
    if rv == 'OK':
        print "Processing mailbox...\n"

        rv, data = M.search(None, "ALL")
        if rv != 'OK':
            print "No messages found!"
            return

        items = data[0].split()

        print items

        for i in range(len(items)-1,-1,-1):

            print i
            num = items[i]



            rv, dataThis = M.fetch(num, '(RFC822)')
            if rv != 'OK':
                print "ERROR getting message", num
                return

            msg = email.message_from_string(dataThis[0][1])
            # print msg['Subject']
            # decode = email.header.decode_header(msg['Subject'])[0]
            # subject = unicode(decode[0])
            subject = msg['Subject']

            print taelTxHashList
            print 'this'

            for entryNum in range(0, len(taelTxHashList)):
                # taelTxHash, taelAmount, ethTxHash, ethAmount, participantEmail, processed_timestamp, rolloverBool

                taelTxHash = taelTxHashList[entryNum][0]
                taelAmount = taelTxHashList[entryNum][1]
                ethTxHash = taelTxHashList[entryNum][2]
                ethAmount = taelTxHashList[entryNum][3]
                participantEmail = taelTxHashList[entryNum][4]
                processed_timestamp = taelTxHashList[entryNum][5]
                rolloverBool = taelTxHashList[entryNum][6]

                print taelTxHashList[entryNum][0]
                print subject

                if taelTxHashList[entryNum][0] in subject:
                    #append to csv
                    # EMAIL_SUCCESS_HEADER = ['TAELIUM TX ID', 'TAELS AMOUNT', 'ETH HASH', 'ETH AMOUNT',
                                            # 'PARTICIPANT EMAIL', 'TIMESTAMP', 'CARRY OVER TO ICO']
                    append_to_csv(successFile,[taelTxHash, taelAmount,ethTxHash,ethAmount,participantEmail,processed_timestamp,rolloverBool])
                    taelTxHashList.pop(entryNum)
                    print taelTxHashList
                    break

            if len(taelTxHashList)==0:
                break
        M.close()

    else:
        print "ERROR: Unable to open mailbox ", rv

    M.logout()

    if len(taelTxHashList) != 0:
        for entryNum in range(0, len(taelTxHashList)):
            taelTxHash = taelTxHashList[entryNum][0]
            taelAmount = taelTxHashList[entryNum][1]
            ethTxHash = taelTxHashList[entryNum][2]
            ethAmount = taelTxHashList[entryNum][3]
            participantEmail = taelTxHashList[entryNum][4]
            processed_timestamp = taelTxHashList[entryNum][5]
            rolloverBool = taelTxHashList[entryNum][6]
            # append to failed csv
            # EMAIL_FAILURE_HEADER = ['TAELIUM TX ID', 'TAELS AMOUNT', 'ETH HASH', 'ETH AMOUNT', 'PARTICIPANT EMAIL',
                                    # 'TIMESTAMP', 'CARRY OVER TO ICO']
            append_to_csv(failureFile, [taelTxHash, taelAmount, ethTxHash, ethAmount, participantEmail, processed_timestamp,rolloverBool])
            taelTxHashList.pop(entryNum)


def overallEmailSender():
    while (True):
        workingFiles = findFiles(WORKING + TAELIUM_SUCCESS)

        if len(workingFiles) != 0:
            for eachFile in workingFiles:
                tempString = eachFile

                fileTimestamp = tempString.split('_')[2].split('.')[0]
                EMAIL_SUCCESS_FILENAME = EMAIL_SUCCESS + '_' + fileTimestamp + '.csv'
                EMAIL_FAILURE_FILENAME = EMAIL_FAILURE + '_' + fileTimestamp + '.csv'

                create_csv(WORKING + EMAIL_SUCCESS_FILENAME, EMAIL_SUCCESS_HEADER)
                create_csv(WORKING + EMAIL_FAILURE_FILENAME, EMAIL_FAILURE_HEADER)

                current_timestamp = datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S")
                print 'Starting taelSender process. Timestamp:', current_timestamp, 'Working File:', eachFile

                taelTxHashList =[]
            
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(FROM_ADDR, "lotsoftael")

                with open(eachFile, 'rb') as f:
                    reader = csv.reader(f)
                    for row in reader:

                        print row

                        if row[0] == 'TAELIUM TX ID': continue
                        # 'TAELIUM TX ID', 'TAELIUM ADDRESS', 'TAELS AMOUNT', 'TAELIUM BLOCK ID', 'TAELIUM BLOCK HEIGHT', 'ETH AMOUNT',
                        # 'ETH TX HASH', 'PARTICIPANT EMAIL', 'TAELIUM TIMESTAMP', 'CARRY OVER TO ICO'
                        ethTxHash = row[6];
                        ethAmount = row[5];
                        taelTxHash = row[0];
                        taelAmount = row[2];
                        participantEmail = row[7];
                        rolloverBool = row[9];

                        taelTxHashListEntry = sendMail(server=server, ethTxHash=ethTxHash,ethAmount=ethAmount,taelTxHash=taelTxHash,taelAmount=taelAmount,participantEmail=participantEmail, rolloverBool = rolloverBool)
                        taelTxHashList.append(taelTxHashListEntry)
                server.quit()

                print taelTxHashList
            
            
                time.sleep(WAIT_TIME_TO_CHECK_SENT)
                checkSent(taelTxHashList, EMAIL_SUCCESS_FILENAME, EMAIL_FAILURE_FILENAME)

                print 'taelSender process with timestamp', current_timestamp, 'complete.'
            
                # move files after done

                pathless_filename = eachFile.split('//')[-1]

                os.rename(WORKING + TAELIUM_SUCCESS + '//' + pathless_filename,
                          ARCHIVE + TAELIUM_SUCCESS + '//' + pathless_filename)
                os.rename(WORKING + EMAIL_FAILURE_FILENAME,
                          FOLLOW_UP + EMAIL_FAILURE + '//' + EMAIL_FAILURE_FILENAME)
                os.rename(WORKING + EMAIL_SUCCESS_FILENAME,
                          'done//' + EMAIL_SUCCESS_FILENAME)
            
            
        countdown(POLLING_INTERVAL)



if __name__ == '__main__':
    overallEmailSender()