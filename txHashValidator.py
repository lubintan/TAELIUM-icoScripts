# import libraries
import urllib2, datetime, csv
from pytz import timezone
from bs4 import BeautifulSoup

INPUT_FILE = 'local_data//filteredParticipants.csv'
LOCAL_DATA_DIR = "local_data//"



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

def append_to_csv(fileName, data):
    with open(LOCAL_DATA_DIR + fileName + '.csv', 'ab') as f:
        writer = csv.writer(f)
        writer.writerow(data)

def checkTxHashes():
    with open(INPUT_FILE, 'rb') as f:
        reader = csv.reader(f)

        for row in reader:
            if row[0] == 'EMAIL TIMESTAMP': continue
            txHash = row[7]
            email = row[2]
            result, data = validateTxHash(txHash)
            data.append(email)
            if result:
                append_to_csv('ethTxSuccess',data)
                print 'Validate TxHash passed. Participant', email
            else:
                append_to_csv('ethTxFailure', data)
                print 'Validate TxHash failed. Participant', email
            print


if __name__ == '__main__':
    checkTxHashes()
    # validateTxHash('0x120c430d8eaa27b59e5974c8382ffabf9e87d3c3cfbcc4058ffc588e2627391b')