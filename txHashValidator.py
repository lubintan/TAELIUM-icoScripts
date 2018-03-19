# import libraries
import urllib2, datetime, csv, os, glob, time, sys
from pytz import timezone
from bs4 import BeautifulSoup

CURR_DIR = os.getcwd()

WORKING = 'txHashValidator_working//'
ARCHIVE = 'archive//'
FOLLOW_UP = 'followUp//'
ETH_TX_SUCCESS = 'ethTxSuccess'
ETH_TX_FAILURE = 'ethTxFailure'
FILTERED_PARTICIPANTS = 'filteredParticipants'
ETH_TX_SUCCESS_HEADER = ['TX HASH', 'ETH AMOUNT', 'VERIFICATION TIMESTAMP', 'BLOCK HEIGHT', 'UTC TIME', 'LOCAL TIME', 'PARTICIPANT EMAIL', 'TAELIUM ADDRESS', 'CARRY OVER TO ICO']
ETH_TX_FAILURE_HEADER = ['TX HASH', 'FAILURE TIMESTAMP', 'ERROR MSG', 'PARTICIPANT EMAIL', 'CARRY OVER TO ICO']
FILTERED_PARTICIPANTS = 'filteredParticipants'

POLLING_INTERVAL = 600

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

        url = 'https://etherscan.io/tx/' + txHash

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

        websiteTxHash = body[body.index('TxHash:')+1]
        if websiteTxHash!=txHash:
            return False, [txHash, processed_timestamp, 'Tx hash does not match.']
        status = body[body.index('TxReceipt')+1]
        if status != 'Status:Success':
            return False, [txHash, processed_timestamp, 'No success receipt.']

        blockHeight = body[body.index('Height:')+1]

        timeIndex = body.index('ago') + 1
        time = body[timeIndex]+' '+body[timeIndex+1]+' '+body[timeIndex+2]+' '+body[timeIndex+3]

        ethAmount = body[body.index('Value:')+1]
        if float(ethAmount) <= 0:
            return False, [txHash, processed_timestamp, 'Eth amount is zero.']
        #
        # print websiteTxHash
        # print status
        # print blockHeight
        # print time
        # print ethAmount

        #convert to local time for easier viewing
        utcTime = datetime.datetime.strptime(time.strip('(').strip(')'),'%b-%d-%Y %H:%M:%S %p +%Z')
        utcTime = utcTime.replace(tzinfo=timezone('UTC'))
        localTime = utcTime.astimezone(timezone('Singapore'))
        localTime = localTime.strftime("%Y-%b-%d %H:%M:%S.%f")[:-3]


        return True, [txHash, ethAmount, processed_timestamp, blockHeight, utcTime, localTime]

    except Exception, e:
        print 'Error validating Tx Hash on Etherscan.'
        print str(e)
        return False, [txHash, processed_timestamp, 'Exception error.']


def overallTxHashValidator():
    while True:
        workingFiles = findFiles(WORKING+FILTERED_PARTICIPANTS)

        if len(workingFiles)!=0:



            for eachFile in workingFiles:

                tempString = eachFile

                fileTimestamp = tempString.split('_')[1].split('.')[0]
                ETH_TX_SUCCESS_FILENAME = ETH_TX_SUCCESS + '_' + fileTimestamp + '.csv'
                ETH_TX_FAILURE_FILENAME = ETH_TX_FAILURE + '_' + fileTimestamp + '.csv'



                create_csv(WORKING + ETH_TX_SUCCESS_FILENAME, ETH_TX_SUCCESS_HEADER)
                create_csv(WORKING + ETH_TX_FAILURE_FILENAME, ETH_TX_FAILURE_HEADER)

                current_timestamp = datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S")
                print 'Starting txHashValidator process. Timestamp:', current_timestamp, 'Working File:', eachFile

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
                            print 'Validate TxHash passed. Participant', email
                        else:
                            append_to_csv(ETH_TX_FAILURE_FILENAME, data)
                            print 'Validate TxHash failed. Participant', email
                        print

                print 'txHashValidator process with timestamp', current_timestamp, 'complete.'

                # move files after done

                os.rename(WORKING + FILTERED_PARTICIPANTS + '//' + eachFile,
                         ARCHIVE + FILTERED_PARTICIPANTS + '//' + eachFile)
                os.rename(WORKING + ETH_TX_FAILURE_FILENAME,
                          FOLLOW_UP + ETH_TX_FAILURE + '//' + ETH_TX_FAILURE_FILENAME)
                os.rename(WORKING + ETH_TX_SUCCESS_FILENAME,
                          'taelSender_working' + ETH_TX_SUCCESS + '//' + ETH_TX_SUCCESS_FILENAME)

        countdown(POLLING_INTERVAL)



if __name__ == '__main__':
    overallTxHashValidator()
    # validateTxHash('0x120c430d8eaa27b59e5974c8382ffabf9e87d3c3cfbcc4058ffc588e2627391b')