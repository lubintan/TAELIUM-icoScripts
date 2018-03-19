# importing the requests library
import requests, csv, datetime, time, os, glob, sys

'''
http://localhost:7876/nxt?
  requestType=sendMoney&
  secretPhrase=IWontTellYou&
  recipient=NXT-4VNQ-RWZC-4WWQ-GVM8S&
  amountNQT=100000000&
  feeNQT=100000000&
  deadline=60
'''
EIGHT_ZEROES = 100000000
ETH_TO_TAEL_RATE = 100.5
sendingAccounts = [['TAEL-VXVQ-APCC-UHDD-7A3ZX','password1'],
        ['TAEL-PGDQ-XR6X-2EAS-9H2KM','password2'],
          ['TAEL-D6PA-3TCG-AXGA-BVHW4','password3'],
          ['TAEL-Y4LF-K6UK-AT74-CT6JS','password4'],
          ['TAEL-J4YD-K25L-6AAS-E6Y9C','password5'],
          ['TAEL-D8XY-HTU7-QWM5-2YHMZ','password6'],
          ['TAEL-PQMA-6CS2-XU9J-AWZY7','password7'],
          ['TAEL-N7LT-FNZN-A9QJ-GPXMA','password8'],
          ['TAEL-KXHS-8A7R-5FF5-5PFS6','password9'],
          ['TAEL-DLMP-5UTD-LDQQ-8929X','password10']]

CURR_DIR = os.getcwd()
WORKING = 'taelSender_working//'
ARCHIVE = 'archive//'
FOLLOW_UP = 'followUp//'
TAELIUM_SUCCESS = 'taeliumSuccess'
TAELIUM_FAILURE = 'taeliumFailure'
TAELIUM_SUCCESS_HEADER = ['TAELIUM TX ID', 'TAELIUM ADDRESS', 'TAELS AMOUNT', 'TAELIUM BLOCK ID', 'TAELIUM BLOCK HEIGHT', 'ETH AMOUNT', 'ETH TX HASH', 'PARTICIPANT EMAIL', 'TAELIUM TIMESTAMP', 'CARRY OVER TO ICO']
TAELIUM_FAILURE_HEADER = ['ETH TX HASH', 'ETH AMOUNT', 'TAELS AMOUNT', 'PARTICIPANT EMAIL', 'ERROR', 'CARRY OVER TO ICO']
ETH_TX_SUCCESS = 'ethTxSuccess'

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

def append_to_csv(fileName, data):
    with open(WORKING + fileName, 'ab') as f:
        writer = csv.writer(f)
        writer.writerow(data)


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

def getSuccessfulEthTxes(inputFile, workingFailureFile):

    unconfirmedTxes = []

    with open(inputFile, 'rb') as f:
        reader = csv.reader(f)

        for row in reader:
            processed_timestamp = datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S.%f")[:-3]
            if row[0]=='TX HASH': continue
            ethAmount = row[1]
            amountToSend = long(ethAmount * (EIGHT_ZEROES*ETH_TO_TAEL_RATE))
            taelAddr = row[7]
            ethTxHash = row[0]
            participantEmail = row[6]
            rolloverBool = row[8]

            sender = ''
            password=''
            for each in sendingAccounts:
                balance = getAccountBalance(each[0])
                if balance >= amountToSend:
                    sender = each[0]
                    password = each[1]

            if sender=='':
                print 'COULD NOT FIND A SENDER WITH ENOUGH TAELS!!'
                append_to_csv(workingFailureFile, [ethTxHash,amountToSend, participantEmail,processed_timestamp, 'Could not find sender with enough taels.', rolloverBool])
                continue

            txId = sendMoney(taelAddr, amountToSend, password)
            unconfirmedTxes.append([txId,ethAmount,taelAddr,amountToSend,participantEmail,ethTxHash, rolloverBool])

    return unconfirmedTxes


def getLatestBlock():
    '''
    http://localhost:7876/nxt?
  requestType=getBlockchainStatus
    :return:
    '''

    URL = 'http://localhost:43250/nxt?' +\
  'requestType=getBlockchainStatus'

    r = requests.post(url=URL)
    data = r.json()
    return data['lastBlock']

def checkTxesWentThrough(unconfirmedTxes, taeliumSuccessFile, taeliumFailureFile):
    latestBlock = getLatestBlock()
    nextLatestBlock = latestBlock

    print 'Waiting for New Block to be forged'

    while latestBlock==nextLatestBlock:
        time.sleep(5)
        nextLatestBlock = getLatestBlock()

    print 'New Block Forged!'

    for each in unconfirmedTxes:
        blockId, timestamp, height = getTxInfo(each[0])
        if blockId!=None:
            append_to_csv(taeliumSuccessFile, [each[0], each[2], each[3], blockId, height, each[1], each[5], each[4], timestamp, each[6]])
            print 'Successfully sent to', each[5]
        else:
            append_to_csv(taeliumFailureFile, [each[5], each[1], each[3], each[4], "Unconfirmed. Check back again.", each[6]])
            print 'Tx ID:', each[0], 'still unconfirmed. Manually check back later.'


def getTxInfo(txId):
    #now check if tx went through
    '''
    http: // localhost:7876 / nxt?
    requestType = getTransaction &
    transaction = 15200507403046301754
    '''

    try:
        URL = 'http://localhost:48250/nxt?' +\
      'requestType=getTransaction&' +\
      'transaction=' + txId

        r = requests.post(url=URL)
        data = r.json()

        return data['block'], data['blockTimestamp'],data['height']
    except Exception,e:
        print str(e)
        return None, None, None

def getAccountBalance(account):
    '''
    http://localhost:7876/nxt?
  requestType=getAccount&
  account=NXT-4VNQ-RWZC-4WWQ-GVM8S
    :param account:
    :return:
    '''
    URL = 'http://localhost:43250/nxt?' +\
  'requestType=getAccount&' +\
  'account=' + account

    r = requests.post(url=URL)
    data = r.json()

    return data['unconfirmedBalanceNQT']

def sendMoney(recipient, amount, password):
    # api-endpoint
    URL = "http://localhost:43250/nxt?" +\
      'requestType=sendMoney&' +\
      'secretPhrase=' + password +'&'+\
      'recipient=' + recipient + '&' +\
      'amountNQT=' + amount + '&' +\
      'feeNQT=10000&' +\
      'deadline=60'


    # sending get request and saving the response as response object
    r = requests.post(url=URL)

    # extracting data in json format
    data = r.json()

    return data['transaction']


def overallTaelSender():
    while(True):
        workingFiles = findFiles(WORKING + ETH_TX_SUCCESS)

        if len(workingFiles) != 0:
            for eachFile in workingFiles:
                tempString = eachFile

                fileTimestamp = tempString.split('_')[1].split('.')[0]
                TAELIUM_SUCCESS_FILENAME = TAELIUM_SUCCESS + '_' + fileTimestamp + '.csv'
                TAELIUM_FAILURE_FILENAME = TAELIUM_FAILURE + '_' + fileTimestamp + '.csv'



                create_csv(WORKING + TAELIUM_SUCCESS_FILENAME, TAELIUM_SUCCESS_HEADER)
                create_csv(WORKING + TAELIUM_FAILURE_FILENAME, TAELIUM_FAILURE_HEADER)

                current_timestamp = datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S")
                print 'Starting taelSender process. Timestamp:', current_timestamp, 'Working File:', eachFile

                unconfirmedTxesList = getSuccessfulEthTxes(WORKING+ETH_TX_SUCCESS+'//'+eachFile, WORKING + TAELIUM_FAILURE_FILENAME)
                checkTxesWentThrough(unconfirmedTxesList, WORKING + TAELIUM_SUCCESS_FILENAME, WORKING + TAELIUM_FAILURE_FILENAME)

                print 'taelSender process with timestamp', current_timestamp, 'complete.'
        
                # move files after done
        
                os.rename(WORKING + ETH_TX_SUCCESS + '//' + eachFile,
                          ARCHIVE + ETH_TX_SUCCESS + '//' + eachFile)
                os.rename(WORKING + TAELIUM_FAILURE_FILENAME,
                          FOLLOW_UP + TAELIUM_FAILURE + '//' + TAELIUM_FAILURE_FILENAME)
                os.rename(WORKING + TAELIUM_SUCCESS_FILENAME,
                          'emailSender_working' + TAELIUM_SUCCESS + '//' + TAELIUM_SUCCESS_FILENAME)

        countdown(POLLING_INTERVAL)


if __name__ == '__main__':
    # sendMoney(recipient=sendingAccounts[3][0], amount=str(2500000000), password=sendingAccounts[6][1])
    # getAccountBalance(sendingAccounts[0][0])

    overallTaelSender()