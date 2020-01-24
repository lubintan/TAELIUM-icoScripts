"""
Shows basic usage of the Sheets API. Prints values from a Google Spreadsheet.
"""
from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from decimal import *


def updateCell(cellNum, value):



    # Setup the Sheets API
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
    store = file.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    # Call the Sheets API
    SPREADSHEET_ID = '1tJK917pWD-IYxaU5aRucPPDY88tGZMRS55p7AQCuS0o'
    RANGE_NAME = 'Orders & Disbursement!'+cellNum+':'+cellNum




    # values = [
    #     [
    #         0,1,2,3,'four',5,6,7
    #     ],
    #     # Additional rows
    # ]
    data = [
        {
            'range': RANGE_NAME,
            'values': value
        },
        # Additional ranges to update ...
    ]
    body = {
        'valueInputOption': 'USER_ENTERED',
        'data': data
    }
    result = service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID, body=body).execute()
    # print('{0} cells updated.'.format(result.get('updatedCells')));


def updateOrdered(input):
    # integerPart = str(int(input / 1e8))
    # fractionPart = str(input)[-8:]
    #
    # # print (fractionPart)
    #
    # valueString = integerPart + "." + fractionPart

    # print (valueString)

    decValue = Decimal(input)

    result = [[str(decValue)]]

    updateCell('B3', result)
    # updateCell('B4', result)


def updateOrderedTime(input):
    updateCell('B5', [[input]])

def updateDisbursedTime(input):
    updateCell('B11', [[input]])


def updateEth(input):
    updateCell('A3',[[input]])

def updateDisbursed(input):
    # integerPart = str(int(input/ 1e8))
    # fractionPart = str(input)[-8:]
    #
    # # print (fractionPart)
    #
    # valueString = integerPart + "." + fractionPart

    # print (valueString)

    decValue = Decimal(input)

    result = [[str(decValue)]]

    updateCell('A9', result)
    # updateCell('A10', result)

if __name__ == "__main__":

    decVal = Decimal('999110207.87654323')

    # updateEth(12.509617)
    # updateOrders('B3', [[99911020787654347]])
    # updateOrders('B4', [[99911020787654347]])

# print(str(decVal))


# def soundAlarm(sheetName):
#     # Setup the Sheets API
#     SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
#     store = file.Storage('credentials.json')
#     creds = store.get()
#     if not creds or creds.invalid:
#         flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
#         creds = tools.run_flow(flow, store)
#     service = build('sheets', 'v4', http=creds.authorize(Http()))
#
#     # Call the Sheets API
#     SPREADSHEET_ID = '1tJK917pWD-IYxaU5aRucPPDY88tGZMRS55p7AQCuS0o'
#     RANGE_NAME = sheetName + '!A4:F8'
#
#     values = [
#         ['xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx'],
#         ['xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx'],
#         ['xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx'],
#         ['xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx'],
#         ['xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx', 'xx DANGER xx']
#
#         # Additional rows
#     ]
#     data = [
#         {
#             'range': RANGE_NAME,
#             'values': values
#         },
#         # Additional ranges to update ...
#     ]
#     body = {
#         'valueInputOption': 'USER_ENTERED',
#         'data': data
#     }
#     result = service.spreadsheets().values().batchUpdate(
#         spreadsheetId=SPREADSHEET_ID, body=body).execute()
#     print('{0} cells updated.'.format(result.get('updatedCells')));



