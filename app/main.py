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

# Deployed Smart Contract init
# deployedContract = w3.eth.contract(address=os.getenv("CONTRACT_ADDRESS"), abi=(os.getenv("ABI")))


# ------------------ENDPOINTS------------------------
@app.get("/eth/accounts")
def get_accounts():
    return {
        "Available Accounts": w3.eth.accounts,
        "Total Number of blocks": w3.eth.get_block_number()
        }

@app.get("/eth/account/create")
def create_new_account():
    acc = w3.eth.account.create()
    return {
        "account": acc.address,
        "private key": w3.to_hex(acc.key)    
    }

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

# TRANSFERING FUNDS
class TransactionModel(BaseModel):
    from_address: str
    to_address: str
    amount: float
    
@app.post("/eth/estimateGas")
def estimateGas(transactionModel: TransactionModel):
    estimatedGas = w3.eth.estimate_gas(
        {'to': transactionModel.to_address, 
        'from': transactionModel.from_address, 
        'value': hex(int(transactionModel.amount))
        }
    )
    return {
            "estimatedGas": estimatedGas,
            "gasPrice": w3.from_wei(w3.to_wei('50', 'gwei'), "ether"),
            "contractFee": 0.18 * transactionModel.amount,
            "totalTransactionFee":  transactionModel.amount + (0.18 * transactionModel.amount) + float(w3.from_wei(w3.to_wei(estimatedGas * 50, 'gwei'), "ether"))
            }

@app.post("/eth/transfer/")
def transfer(transactionModel: TransactionModel):
    if (not w3.is_address(transactionModel.from_address) or not w3.is_address(transactionModel.to_address)):
        raise HTTPException(status_code=400, detail="Invalid Addresses. Please recheck")
    try:
        nonce = w3.eth.get_transaction_count(transactionModel.from_address)
        tx = {
            'to': transactionModel.to_address,
            'value': w3.to_wei(transactionModel.amount, 'ether'),
            'gas': estimateGas(transactionModel),
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
    

@app.get("/contract/balance")
def get_contract_balance():
    return {
        "address": deployedContract.address,
        "TradeTix Contract Balance": w3.from_wei(deployedContract.caller().contractBalance(), "ether")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app', host="0.0.0.0", port=8090, reload=True)