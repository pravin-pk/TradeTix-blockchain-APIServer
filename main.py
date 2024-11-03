from fastapi import FastAPI, HTTPException
from web3 import Web3
from pydantic import BaseModel
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Blockchain-API-Server", description="This app connects to the private blockchain network and communicates with the smart contract for our TradeTix App", version="0.1.0")

# Connect to Ganache RPC 
w3 = Web3(Web3.HTTPProvider(os.getenv("GANACHE_RPC")))

if not w3.is_connected():
    raise Exception("Failed to connect to the Ganache Private Blockchain network.")


@app.get("/eth/accounts")
def get_accounts():
    return {
        "Available Accounts": w3.eth.accounts,
        "Total Number of blocks": w3.eth.get_block_number()
        }

@app.get("/eth/account/{account}")
def get_account_key(account: str):
    return w3.eth.get_code(account)

@app.get("/eth/balance/{address}")
def get_balance(address: str):
    try:
        balance = w3.eth.get_balance(address)
        return {"address": address, "balance": str(w3.from_wei(balance, 'ether')) + " ETH"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/block/{blockNumber}")
def get_block_details(blockNumber: int):
    try:
        return json.loads(w3.to_json(w3.eth.get_block(blockNumber)))
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "msg": f"Error while fetching details fof block {blockNumber}",
            "error": str(e)
        })

    
class TrasactionModel(BaseModel):
    from_address: str
    to_address: str
    amount: float

@app.post("/eth/transfer/")
def transfer(transactionModel: TrasactionModel):
    if (not w3.is_address(transactionModel.from_address) or not w3.is_address(transactionModel.to_address)):
        raise HTTPException(status_code=400, detail="Invalid Addresses. Please recheck")
    try:
        nonce = w3.eth.get_transaction_count(transactionModel.from_address)
        tx = {
            'to': transactionModel.to_address,
            'value': w3.to_wei(transactionModel.amount, 'ether'),
            'gas': 2000000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'nonce': nonce,
        }
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=os.getenv("PRIVATE_KEY"))
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return {
            "transaction_hash": w3.to_hex(tx_hash),
            "total Transactions": w3.eth.get_transaction_count(transactionModel.from_address)
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app', host="0.0.0.0", port=8090, reload=True)