# import libraries
import urllib2, datetime, csv, os, glob, time, sys, math, googleSheets,taelSender
from pytz import timezone
from bs4 import BeautifulSoup

CURR_DIR = os.getcwd()

WORKING = 'txHashValidator_working//'
ARCHIVE = 'archive//'
FOLLOW_UP = 'followUp//'
ETH_TX_SUCCESS = 'ethTxSuccess'
ETH_TX_FAILURE = 'ethTxFailure'
FILTERED_PARTICIPANTS = 'filteredParticipants'
ETH_TX_SUCCESS_HEADER = ['TX HASH', 'ETH AMOUNT', 'VERIFICATION TIMESTAMP', 'BLOCK HEIGHT', 'UTC TIME', 'LOCAL TIME', 'PUBLIC KEY', 'PARTICIPANT EMAIL', 'TAELIUM ADDRESS', 'CARRY OVER TO ICO']
ETH_TX_FAILURE_HEADER = ['TX HASH', 'FAILURE TIMESTAMP', 'ERROR MSG', 'PARTICIPANT EMAIL', 'CARRY OVER TO ICO']

POLLING_INTERVAL = 60

etherscanUrl = 'https://ropsten.etherscan.io/tx/'

CONTRACT_ADDRESS = '0x34316aea2c3ea15069a8020210032ba97f246a68'

HEX_CHARACTERS = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']

EIGHT_ZEROES = 1e8
TAELS_PER_ETH = 7800
PRE_ICO_TARGET = 120e6
PRE_ICO_BUFFER = 20 * TAELS_PER_ETH

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

    print 'Created:', filename


def append_to_csv(fileName, data):
    with open(WORKING + fileName, 'ab') as f:
        writer = csv.writer(f)
        writer.writerow(data)


    '''
    allParticipants, filteredParticipants, rejectedParticipants:
    EMAIL TIMESTAMP, PROCESSED TIMESTAMP, PARTICIPANT EMAIL, TELEPHONE NUMBER,
    IP, COUNTRY, DATA FROM, TX HASH, TAELIUM ADDRESS, FORM SUBMITTED ON
    '''

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



def validateTxHash(txHash):
    try:
        processed_timestamp = datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S.%f")[:-3]

        url = etherscanUrl + txHash

        # page = urllib2.urlopen(quote_page, headers={'User-Agent': "Magic Browser"})
        request = urllib2.Request(url, headers={'User-Agent': "Magic Browser"})
        page = urllib2.urlopen(request)
        soup = BeautifulSoup(page, 'html5lib')


        content = soup.find('div', attrs={'id': 'ContentPlaceHolder1_maintable'})

        if content==None:
            return False, [txHash, processed_timestamp, 'Tx not found.']

        body = content.text.strip().split()

        # for i in range(0, len(body)):
        #     print i, body[i]
        # exit(1)

        websiteTxHash = body[body.index('TxHash:')+1]

        print 'Tx Hash:', websiteTxHash

        if websiteTxHash!=txHash:
            return False, [txHash, processed_timestamp, 'Tx hash does not match.']


        status = body[body.index('TxReceipt')+1]
        print 'Receipt Status:', status

        if status != 'Status:Success':
            return False, [txHash, processed_timestamp, 'No success receipt.']

        #### Check recipient is contract. ########
        recipientAddress = body[body.index('To:')+2]
        print 'To:', recipientAddress

        if recipientAddress.lower()!=CONTRACT_ADDRESS.lower():
            return False, [txHash, processed_timestamp, 'Sent to wrong ETH address.']

        blockHeight = body[body.index('Height:')+1]
        print 'block height:', blockHeight


        timeIndex = body.index('ago') + 1
        time = body[timeIndex]+' '+body[timeIndex+1]+' '+body[timeIndex+2]+' '+body[timeIndex+3]
        print 'Time:', time


        ethAmount = body[body.index('Value:')+1]
        print 'Value:', ethAmount,'ETH'

        if float(ethAmount) <= 0:
            return False, [txHash, processed_timestamp, 'Eth amount is zero.']


############# Settle Public Key here ############
        pubKey = body[body.index('Data:')+1]


        pubKey.replace(" ", "")

        pubKey.strip()
        pubKey = pubKey[2:]


        if (len(pubKey)!= 64):
            ##### DANGER WRONG PUBLIC KEY! #####
            return False, [txHash, processed_timestamp, 'Public key wrong length.']

        for eachChar in pubKey:
            if (not (eachChar in HEX_CHARACTERS)):
                return False, [txHash, processed_timestamp, 'Public key wrong characters.']


########### End Settle Public Key #################

        #convert to local time for easier viewing
        utcTime = datetime.datetime.strptime(time.strip('(').strip(')'),'%b-%d-%Y %H:%M:%S %p +%Z')
        utcTime = utcTime.replace(tzinfo=timezone('UTC'))
        localTime = utcTime.astimezone(timezone('Singapore'))
        localTime = localTime.strftime("%Y-%b-%d %H:%M:%S.%f")[:-3]

        print "Public Key: " + pubKey

        return True, [txHash, ethAmount, processed_timestamp, blockHeight, utcTime, localTime, pubKey]

    except Exception, e:
        print 'Error validating Tx Hash on Etherscan.'
        print str(e)
        return False, [txHash, processed_timestamp, 'Exception error.']

def updateTallies(ethPaidTally, taelsOrderedTally, fileTimeStamp):

    with open("tallies//etherPaid.txt", "r+") as file:
        data = file.read()
        data.strip()
        currentEth = float(data)
        ethPaidTally += currentEth
        file.seek(0)
        file.write('%f'%ethPaidTally)

    with open("tallies//taelsOrdered.txt", "r+") as file:
        data = file.read()
        data.strip()
        currentTaelsOrdered = float(data)
        taelsOrderedTally += currentTaelsOrdered

        file.seek(0)
        file.write('%f'%taelsOrderedTally)

    #Google tallies - Ether Paid, Taels Ordered, Gap from target, timestamp
    googleSheets.updateOrdered(taelsOrderedTally)
    googleSheets.updateEth(ethPaidTally)
    googleSheets.updateOrderedTime(fileTimeStamp)


    if (taelsOrderedTally >= (PRE_ICO_TARGET-PRE_ICO_BUFFER)):
        googleSheets.soundAlarm('Orders')
        exit('taels disbursed: ' + taelsOrderedTally + ' is over the target!!')


def overallTxHashValidator():
    while True:
        workingFiles = findFiles(WORKING+FILTERED_PARTICIPANTS)

        if len(workingFiles)!=0:



            for eachFile in workingFiles:

                tempString = eachFile

                fileTimestamp = tempString.split('_')[2].split('.')[0]


                ETH_TX_SUCCESS_FILENAME = ETH_TX_SUCCESS + '_' + fileTimestamp + '.csv'
                ETH_TX_FAILURE_FILENAME = ETH_TX_FAILURE + '_' + fileTimestamp + '.csv'



                create_csv(WORKING + ETH_TX_SUCCESS_FILENAME, ETH_TX_SUCCESS_HEADER)
                create_csv(WORKING + ETH_TX_FAILURE_FILENAME, ETH_TX_FAILURE_HEADER)

                current_timestamp = datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S")
                print 'Starting txHashValidator process. Timestamp:', current_timestamp, 'Working File:', eachFile


                ethPaidTally = 0
                taelsOrderedTally = 0


                with open(eachFile, 'rb') as f:
                    reader = csv.reader(f)

                    for row in reader:
                        if row[0] == 'EMAIL TIMESTAMP': continue
                        txHash = row[7]
                        email = row[2]
                        taelAddr = row[8]
                        rolloverBool = row[10]
                        result, data = validateTxHash(txHash)
                        data.append(email)
                        data.append(taelAddr)
                        data.append(rolloverBool)
                        if result:
                            append_to_csv(ETH_TX_SUCCESS_FILENAME,data)
                            print 'Validate TxHash PASSED. Participant', email, 'ETH AMT:', data[1]

                            ethPaidTally += float(data[1])
                            taelsOrderedTally += float(math.ceil(float(data[1]) * TAELS_PER_ETH * EIGHT_ZEROES)) / float(EIGHT_ZEROES)





                        else:
                            append_to_csv(ETH_TX_FAILURE_FILENAME, data)
                            print 'Validate TxHash failed. Participant', email
                        print

                    updateTallies(ethPaidTally, taelsOrderedTally, fileTimestamp)

                print 'txHashValidator process with timestamp', current_timestamp, 'complete.'

                # move files after done

                print 'taelSender_working//' + ETH_TX_SUCCESS + '//' + ETH_TX_SUCCESS_FILENAME

                pathless_filename = eachFile.split('//')[-1]

                os.rename(WORKING + FILTERED_PARTICIPANTS + '//' + pathless_filename,
                         ARCHIVE + FILTERED_PARTICIPANTS + '//' + pathless_filename)
                os.rename(WORKING + ETH_TX_FAILURE_FILENAME,
                          FOLLOW_UP + ETH_TX_FAILURE + '//' + ETH_TX_FAILURE_FILENAME)
                os.rename(WORKING + ETH_TX_SUCCESS_FILENAME,
                          'taelSender_working//' + ETH_TX_SUCCESS + '//' + ETH_TX_SUCCESS_FILENAME)

        countdown(POLLING_INTERVAL)



if __name__ == '__main__':
    overallTxHashValidator()
    # validateTxHash('0xff6040e0002e9f379155ff59e64f1f374257f3845d55675a77edd40741418fa0')