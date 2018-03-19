#!/usr/bin/env python
#
# Very basic example of using Python and IMAP to iterate over emails in a
# gmail folder/label.  This code is released into the public domain.
#
# RKI July 2013
# http://www.voidynullness.net/blog/2013/07/25/gmail-email-with-python-via-imap/
#
import sys, os
import glob, os
import imaplib, email, email.header, datetime, csv,re, time
global oldCsvTxHashList

CURR_DIR = os.getcwd()
EMAIL_ACCOUNT = "taelium.participationform@gmail.com"
EMAIL_FOLDER = "Inbox"
SUBJECT_IDENTIFIER = "Participation Form Submitted"
PROCESSED_FOLDER = "(Processed)"
REJECTED_US_FOLDER = "(Rejections_US)"
REJECTED_REPEAT_TXHASH_FOLDER = "(Rejections_RepeatTxHash)"
PHOTOS_DIR = "photos//"
WORKING = 'xchanger_working//'
ARCHIVE = 'archive//'
FOLLOW_UP = 'followUp//'
ALL_PARTICIPANTS = 'allParticipants'
REJECTED_PARTICIPANTS = 'rejectedParticipants'
FILTERED_PARTICIPANTS = 'filteredParticipants'
ROLLOVER_IDENTIFIER = 'I want my contribution to be applied to the ICO instead of being refunded.'

POLLING_INTERVAL = 600

ALL_PARTS_HEADER = ['EMAIL TIMESTAMP', 'PROCESSED TIMESTAMP', 'PARTICIPANT EMAIL',
                    'TELEPHONE NUMBER', 'IP', 'COUNTRY', 'DATA FROM', 'TX HASH', 'TAELIUM ADDRESS',
                    'FORM SUBMITTED ON', 'CARRY OVER TO ICO']

REJ_PARTS_HEADER = ['EMAIL TIMESTAMP', 'PROCESSED TIMESTAMP', 'PARTICIPANT EMAIL', 'TELEPHONE NUMBER', 'IP', 'COUNTRY', 'DATA FROM', 'TX HASH', 'TAELIUM ADDRESS', 'FORM SUBMITTED ON', 'CARRY OVER TO ICO']

FIL_PARTS_HEADER = ['EMAIL TIMESTAMP', 'PROCESSED TIMESTAMP', 'PARTICIPANT EMAIL', 'TELEPHONE NUMBER', 'IP', 'COUNTRY', 'DATA FROM', 'TX HASH', 'TAELIUM ADDRESS', 'FORM SUBMITTED ON', 'CARRY OVER TO ICO']


def countdown(interval):
    for i in range(interval,-1,-1):
        sys.stdout.write("\r" +str(i) + ' seconds left to chill.')
        sys.stdout.flush()
        time.sleep(1)

def create_csv(filename, header):

    with open(filename, 'wb') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow(header)

    print 'Created:',filename


def append_to_csv(fileName, data):
    with open(WORKING + fileName + '.csv', 'ab') as f:
        writer = csv.writer(f)
        writer.writerow(data)


    '''
    allParticipants, filteredParticipants, rejectedParticipants:
    EMAIL TIMESTAMP, PROCESSED TIMESTAMP, PARTICIPANT EMAIL, TELEPHONE NUMBER,
    IP, COUNTRY, DATA FROM, TX HASH, TAELIUM ADDRESS, FORM SUBMITTED ON
    '''

def findFiles(dir):
    csvList = []
    os.chdir(dir)
    for file in glob.glob("*.csv"):
        csvList.append(dir+'//'+file)

    os.chdir(CURR_DIR)

    return csvList

def getOldCsvTxHashes():
    global oldCsvTxHashList
    oldCsvTxHashList= []

    oldCsvList = findFiles('archive//filteredParticipants')

    for eachFile in oldCsvList:
        with open(eachFile, 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                oldCsvTxHashList.append(row[7])


def checkRepeatTxHash(txHash, current_timestamp):
    txHashList = []
    with open(WORKING+FILTERED_PARTICIPANTS+'_'+current_timestamp+'.csv', 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            txHashList.append(row[7])

    txHashList = txHashList + oldCsvTxHashList

    if txHash in txHashList:
        print "Duplicate Tx Hash Found!!!!"
        return True #danger!!
    return False #all clear


def process_mailbox(M, current_timestamp):
    """
    Do something with emails messages in the folder.  
    For the sake of this example, print some headers.
    """

    rv, data = M.search(None, "ALL")
    if rv != 'OK':
        print "No messages found!"
        return

    items = data[0].split()

    for num in items:
        if True:
            print
            print num, 'of', items[-1], 'items left to process in Inbox..'
            # print num

            rv, dataThis = M.fetch(num, '(RFC822)')
            if rv != 'OK':
                print "ERROR getting message", num
                return


            msg = email.message_from_string(dataThis[0][1])
            decode = email.header.decode_header(msg['Subject'])[0]
            subject = unicode(decode[0])

            country = 'Unspecified' #initialize at start of each message

            if not (SUBJECT_IDENTIFIER in subject):
                print 'Disregarding email with subject: ',subject
                continue


            email_timestamp = msg['date']
            processed_timestamp = datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S.%f")[:-3]


            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    msg_body = part.get_payload()

                    # print msg_body

                    lines = re.split('\r\n|\r|\n', msg_body)


                    for each in lines:
                        # print 'Line:',each
                        text = each.split(':')
                        if text[0] == 'Email address':
                            participant_email = text[1].strip()
                        elif text[0] == 'Telephone number':
                            telephone_number = text[1].strip()
                        elif text[0] == 'IP of the user':
                            ip = text[1].strip()
                        elif text[0] == 'Country':
                            country = text[1].strip()
                        elif text[0] == 'Data from':
                            data_from = text[1].strip()
                        elif text[0] == 'TxHash':
                            tx_hash = text[1].strip()
                        elif text[0] == 'Taelium address':
                            taelium_address = text[1].strip()
                        elif text[0] == 'Form submitted on':
                            form_submitted_on = text[1].strip()
                        elif text[0] == 'Rollover':
                            rollover = text[1].strip()
                            if ROLLOVER_IDENTIFIER in rollover:
                                rolloverBool = 'Yes'
                            else:
                                rolloverBool = 'No'

            try:
                csvData = [email_timestamp, processed_timestamp, participant_email, telephone_number, ip, country, data_from, tx_hash, taelium_address, form_submitted_on, rolloverBool]
                append_to_csv(ALL_PARTICIPANTS+'_'+current_timestamp, csvData)
                if (country.upper() == 'UNITED STATES') or (country.upper()=='UNITED STATES MINOR OUTLYING ISLANDS'):
                    append_to_csv(REJECTED_PARTICIPANTS+'_'+current_timestamp, csvData)
                    print 'Rejected US Participant:', participant_email
                    # Move to 'Rejected US' Folder
                    result = M.store(num, '+X-GM-LABELS', REJECTED_US_FOLDER)
                    result2 = M.store(num, '+FLAGS', '\\Deleted')
                    # M.expunge()

                    if (result[0] == 'OK') and (result2[0] == 'OK'):
                        print 'Moved Msg to Rejected US Folder.'

                elif checkRepeatTxHash(tx_hash, current_timestamp):
                    append_to_csv(REJECTED_PARTICIPANTS+'_'+current_timestamp, csvData)
                    print 'Repeat of TxHash:', tx_hash, 'by', participant_email, '. Rejected.'
                    # Move to 'Rejected Repeat TxHash' Folder
                    # result = M.store(num, '+X-GM-LABELS', REJECTED_REPEAT_TXHASH_FOLDER)
                    # result2 = M.store(num, '+FLAGS', '\\Deleted')

                else:
                    append_to_csv(FILTERED_PARTICIPANTS+'_'+current_timestamp, csvData)

                    #save Attachments
                    if not os.path.exists(PHOTOS_DIR+current_timestamp):
                        os.makedirs(PHOTOS_DIR+current_timestamp)

                    counter = 1

                    for part in msg.walk():
                        if (part.get('Content-Disposition') is not None):
                            ext = part.get_filename().split('.')[-1]
                            filename = participant_email.split('@')[0] + '_' +str(counter)+'_' + tx_hash + '.' + ext

                            final_path = os.path.join(PHOTOS_DIR+current_timestamp+'//' + filename)

                            if not os.path.isfile(final_path):
                                fp = open(final_path, 'wb')
                                fp.write(part.get_payload(decode=True))
                                fp.close()
                                counter += 1
                                print 'Saved attachement', filename

                    print 'Added Participant:', participant_email

                    # Move to 'Processed' Folder
                    result = M.store(num, '+X-GM-LABELS', PROCESSED_FOLDER)
                    result2 = M.store(num, '+FLAGS', '\\Deleted')
                    # M.expunge()

                    if (result[0] == 'OK') and (result2[0] == 'OK'):
                        print 'Moved Msg to Processed Folder.'

            except Exception, e:
                print 'Error processing submission form. Email Timestamp:', email_timestamp
                print str(e)


def overallXchanger():
    while True:

        global current_timestamp;
        current_timestamp = datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S")

        print 'Starting xchanger process. Timestamp:', current_timestamp

        create_csv(WORKING+ALL_PARTICIPANTS+'_'+current_timestamp+'.csv', ALL_PARTS_HEADER)
        create_csv(WORKING + REJECTED_PARTICIPANTS + '_' + current_timestamp + '.csv', REJ_PARTS_HEADER)
        create_csv(WORKING + FILTERED_PARTICIPANTS + '_' + current_timestamp + '.csv', FIL_PARTS_HEADER)

        getOldCsvTxHashes()

        M = imaplib.IMAP4_SSL('imap.gmail.com')

        try:
            rv, data = M.login(EMAIL_ACCOUNT, "lotsoftael")
        except imaplib.IMAP4.error:
            print "LOGIN FAILED!!! "

        print rv, data

        rv, mailboxes = M.list()
        # if rv == 'OK':
        #     print "Mailboxes:"
        #     print mailboxes

        rv, data = M.select(EMAIL_FOLDER)
        if rv == 'OK':
            print "Processing mailbox...\n"
            process_mailbox(M, current_timestamp)
            M.close()
        else:
            print "ERROR: Unable to open mailbox ", rv

        M.logout()

        #move files after done

        os.rename(WORKING + ALL_PARTICIPANTS + '_' + current_timestamp + '.csv',
                  ARCHIVE + ALL_PARTICIPANTS + '//' + ALL_PARTICIPANTS + '_' + current_timestamp + '.csv')
        os.rename(WORKING + REJECTED_PARTICIPANTS + '_' + current_timestamp + '.csv',
                  FOLLOW_UP + REJECTED_PARTICIPANTS + '//' + REJECTED_PARTICIPANTS + '_' + current_timestamp + '.csv')
        os.rename(WORKING + FILTERED_PARTICIPANTS + '_' + current_timestamp + '.csv',
                  'txHashValidator_working//' + FILTERED_PARTICIPANTS + '//' + FILTERED_PARTICIPANTS + '_' + current_timestamp + '.csv')


        print 'xchanger process with timestamp', current_timestamp, 'complete.'
        countdown(POLLING_INTERVAL)

if __name__ == '__main__':
    overallXchanger()