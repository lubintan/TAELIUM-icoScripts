#!/usr/bin/env python
#
# Very basic example of using Python and IMAP to iterate over emails in a
# gmail folder/label.  This code is released into the public domain.
#
# RKI July 2013
# http://www.voidynullness.net/blog/2013/07/25/gmail-email-with-python-via-imap/
#
import sys, os
import getpass
import imaplib, email, email.header, datetime, csv,re

EMAIL_ACCOUNT = "taelium.participationform@gmail.com"
EMAIL_FOLDER = "Inbox"
SUBJECT_IDENTIFIER = "Participation Form Submitted"
PROCESSED_FOLDER = "(Processed)"
REJECTED_US_FOLDER = "(Rejections_US)"
REJECTED_REPEAT_TXHASH_FOLDER = "(Rejections_RepeatTxHash)"
LOCAL_DATA_DIR = "local_data//"
PHOTOS_DIR = "photos//"


def append_to_csv(fileName, data):
    with open(LOCAL_DATA_DIR + fileName + '.csv', 'ab') as f:
        writer = csv.writer(f)
        writer.writerow(data)


    '''
    allParticipants, filteredParticipants, rejectedParticipants:
    EMAIL TIMESTAMP, PROCESSED TIMESTAMP, PARTICIPANT EMAIL, TELEPHONE NUMBER,
    IP, COUNTRY, DATA FROM, TX HASH, TAELIUM ADDRESS, FORM SUBMITTED ON

    ethTxSuccess
    TX HASH, VERIFICATION TIMESTAMP

    ethTxFailure
    TX HASH, FAILURE TIMESTAMP

    taeliumSuccess
    TAELIUM TX ID, TAELIUM BLOCK ID, TAELIUM BLOCK HEIGHT, ETH TX HASH, PARTICIPANT EMAIL, TAELIUM TIMESTAMP

    taeliumFailure
    ETH TX HASH, PARTICIPANT EMAIL, PROCESSING TIMESTAMP, ERROR
    '''

def checkRepeatTxHash(txHash):
    txHashList = []
    with open(LOCAL_DATA_DIR+'filteredParticipants.csv', 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            txHashList.append(row[7])

    if txHash in txHashList:
        print "Duplicate Tx Hash Found!!!!"
        return True #danger!!
    return False #all clear


def process_mailbox(M):
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

            try:
                csvData = [email_timestamp, processed_timestamp, participant_email, telephone_number, ip, country, data_from, tx_hash, taelium_address, form_submitted_on]
                append_to_csv('allParticipants', csvData)
                if (country == 'United States'):
                    append_to_csv('rejectedParticipants', csvData)
                    print 'Rejected US Participant:', participant_email
                    # Move to 'Rejected US' Folder
                    result = M.store(num, '+X-GM-LABELS', REJECTED_US_FOLDER)
                    result2 = M.store(num, '+FLAGS', '\\Deleted')
                    # M.expunge()

                    if (result[0] == 'OK') and (result2[0] == 'OK'):
                        print 'Moved Msg to Rejected US Folder.'

                elif checkRepeatTxHash(tx_hash):
                    append_to_csv('rejectedParticipants', csvData)
                    print 'Repeat of TxHash:', tx_hash, 'by', participant_email, '. Rejected.'
                    # Move to 'Rejected Repeat TxHash' Folder
                    result = M.store(num, '+X-GM-LABELS', REJECTED_REPEAT_TXHASH_FOLDER)
                    result2 = M.store(num, '+FLAGS', '\\Deleted')

                else:
                    append_to_csv('filteredParticipants', csvData)

                    #save Attachments
                    for part in msg.walk():
                        if (part.get('Content-Disposition') is not None):
                            ext = part.get_filename().split('.')[-1]
                            filename = participant_email.split('@')[0] + '_' + tx_hash + '.' + ext

                            final_path = os.path.join(PHOTOS_DIR + filename)

                            if not os.path.isfile(final_path):
                                fp = open(final_path, 'wb')
                                fp.write(part.get_payload(decode=True))
                                fp.close()
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


if __name__ == '__main__':

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
        process_mailbox(M)
        M.close()
    else:
        print "ERROR: Unable to open mailbox ", rv

    M.logout()
