import smtplib, imaplib
import email.MIMEMultipart as emailMp
import email.MIMEText as emailText
import email.MIMEBase as emailBase
from email import encoders
import datetime, csv, email,time, os, glob, sys



FROM_ADDR = "taelium.participationform@gmail.com"

CURR_DIR = os.getcwd()
WORKING = 'emailSender_working//'
ARCHIVE = 'archive//'
FOLLOW_UP = 'followUp//'
EMAIL_SUCCESS = 'taeliumSuccess'
EMAIL_FAILURE = 'taeliumFailure'
EMAIL_SUCCESS_HEADER = ['TAELIUM TX ID', 'TAELS AMOUNT', 'ETH HASH', 'ETH AMOUNT', 'PARTICIPANT EMAIL','TIMESTAMP', 'CARRY OVER TO ICO']
EMAIL_FAILURE_HEADER = ['TAELIUM TX ID', 'TAELS AMOUNT', 'ETH HASH', 'ETH AMOUNT', 'PARTICIPANT EMAIL','TIMESTAMP', 'CARRY OVER TO ICO']
TAELIUM_SUCCESS = 'taeliumSuccess'

POLLING_INTERVAL = 600

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
    
    msg['From'] = FROM_ADDR
    msg['To'] = participantEmail
    msg['Subject'] = "Thank you for your participation. Your Tx ID is " + taelTxHash +'.'
    
    body = 'Congratulations. You have received '+taelAmount+' Taels.' + ' ' + ethTxHash + ' '+ ethAmount
    
    msg.attach(emailText.MIMEText(body, 'plain'))
    
    filename = "tempicon.png"
    attachment = open(filename, "rb")
    
    part = emailBase.MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    
    msg.attach(part)
    
    
    text = msg.as_string()
    server.sendmail(FROM_ADDR, participantEmail, text)

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
            decode = email.header.decode_header(msg['Subject'])[0]
            subject = unicode(decode[0])

            for entryNum in range(0, len(taelTxHashList)):
                # taelTxHash, taelAmount, ethTxHash, ethAmount, participantEmail, processed_timestamp, rolloverBool

                taelTxHash = taelTxHashList[entryNum][0]
                taelAmount = taelTxHashList[entryNum][1]
                ethTxHash = taelTxHashList[entryNum][2]
                ethAmount = taelTxHashList[entryNum][3]
                participantEmail = taelTxHashList[entryNum][4]
                processed_timestamp = taelTxHashList[entryNum][5]
                rolloverBool = taelTxHashList[entryNum][6]

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

                fileTimestamp = tempString.split('_')[1].split('.')[0]
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
            
            
                time.sleep(5)
                checkSent(taelTxHashList, WORKING + EMAIL_SUCCESS_FILENAME, WORKING + EMAIL_FAILURE_FILENAME)

                print 'taelSender process with timestamp', current_timestamp, 'complete.'
            
                # move files after done
            
                os.rename(WORKING + TAELIUM_SUCCESS + '//' + eachFile,
                          ARCHIVE + TAELIUM_SUCCESS + '//' + eachFile)
                os.rename(WORKING + EMAIL_FAILURE_FILENAME,
                          FOLLOW_UP + EMAIL_FAILURE + '//' + EMAIL_FAILURE_FILENAME)
                os.rename(WORKING + EMAIL_SUCCESS_FILENAME,
                          'done//' + EMAIL_SUCCESS_FILENAME)
            
            
        countdown(POLLING_INTERVAL)



if __name__ == '__main__':
    overallEmailSender()