from fastapi import FastAPI
from web3 import Web3
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Request
import requests
from fastapi import Header, HTTPException
from fastapi import Depends
from typing import Dict
import json
import time

# import uvicorn

app = FastAPI(title="Random Number Generator for VoucherHub: Hà-Trọng-Hiếu")


# Define a CORS middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# redirect to the docs
@app.get("/", tags=["Docs"])
async def redirect_docs():
    #return RedirectResponse("http://localhost:8000/docs")
    return RedirectResponse("https://random-number-generator-8ziv.onrender.com/docs")

@app.get("/getRequestId", tags=["GET Request Id"])
async def get_request_id():
    alchemy_url = "https://polygon-mumbai.g.alchemy.com/v2/otDAa-dr9OXd2WCnsq8_UEiL7tL7cSv7"
    w3 = Web3(Web3.HTTPProvider(alchemy_url))
    contract_details = {}
    with open('contract.json') as file:
        contract_details = json.load(file)

    my_address = "0xBdbF33b0C19205ceE5d2E67e1d229193D4EFA313"
    private_key = "c4673cc8094493a2a08d20d1c462e97f2eb6cd7b8d2d5b6879e1da1035d6c6d7"

    contract = w3.eth.contract(address=contract_details.get(
        'address'), abi=contract_details.get('abi'))
    nonce = w3.eth.get_transaction_count(my_address)

    # Build tx for requestRandomWords
    tx = contract.functions.requestRandomWords().build_transaction({
        'chainId': 80001,
        'gas': 2500000,
        'maxFeePerGas': w3.to_wei('2', 'gwei'),
        'maxPriorityFeePerGas': w3.to_wei('2', 'gwei'),
        'nonce': nonce
    })
    # sign with private key
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)

    # send signed_tx
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # wait for tx to be mined
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # check if tx is successful
    if (tx_receipt.get('status')):
        # process receipt - might fail due to micro timeout of 10s
        requestId = str(contract.events.RequestSent(
        ).process_receipt(tx_receipt)[0]['args']['requestId'])
             
        new_data = {
            "requestId": requestId,
            "transectionLog": f'https://mumbai.polygonscan.com/tx/{w3.to_hex(tx_hash)}'
        }
        
        return new_data 
    else:
        # error
        raise HTTPException(
            status_code=500, detail="Request Not Processed, Kindly try again later")


@app.get("/getRandomNumber/{requestId}", tags=["GET data by request Id"])
async def get_ramdom_number(requestId: int):
    alchemy_url = "https://polygon-mumbai.g.alchemy.com/v2/otDAa-dr9OXd2WCnsq8_UEiL7tL7cSv7"
    w3 = Web3(Web3.HTTPProvider(alchemy_url))
    contract_details = {}
    with open('contract.json') as file:
        contract_details = json.load(file)

    my_address = "0xBdbF33b0C19205ceE5d2E67e1d229193D4EFA313"
    private_key = "c4673cc8094493a2a08d20d1c462e97f2eb6cd7b8d2d5b6879e1da1035d6c6d7"

    contract = w3.eth.contract(address=contract_details.get(
        'address'), abi=contract_details.get('abi'))
    requests = contract.functions.getRequestStatus(requestId).call()
    total_time = 0
    while True:
        if requests[0]:
            break
        time.sleep(1)
        total_time += 1
        requests = contract.functions.getRequestStatus(requestId).call()
        if total_time >= 180:
            break
    if requests[0]:
        random_number = requests[1][0]
        #link = f'https://mumbai.polygonscan.com/tx/{w3.to_hex(tx_hash)}'
        
        
        data = {
            "randomNum": str(random_number),
            "mappingNum": random_number % 100 + 1,
            #"transectionLog": link
        }
        return data
    
    raise HTTPException(
        status_code=500, detail="Request Not Processed, Kindly try again later")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title + " - Swagger UI"
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return get_openapi(
        title=app.title + " - OpenAPI Schema",
        version="1.0.0",
        description="This is the auto-generated OpenAPI schema for the API",
        routes=app.routes
    )
    
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)