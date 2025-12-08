from core import Blockchain
blockchain = Blockchain()

print("----- Mining Block 1 -----")
transaction_1 = "Alice pays Bob 5 BTC"
blockchain.create_block(transaction_1)
print(f"previous hash: {blockchain.chain[-2].current_hash}")
print(f"current hash: {blockchain.get_previous_block.current_hash}\n")


print("----- Mining Block 2 -----")
transaction_2 = "Bob pays Charlie 2 BTC"
blockchain.create_block(transaction_2)
print(f"previous hash: {blockchain.chain[-2].current_hash}")
print(f"current hash: {blockchain.get_previous_block.current_hash}\n")

print(f"Chain valid? {'Valid' if blockchain.is_chain_valid() else 'Invalid'}\n")


'''
# สถานการณ์จำลอง มีการแก้ไขข้อมูลในบล็อก
print("[HACKER] is trying to tamper with the blockchain...")
blockchain.chain[1].body = "Alice pays Bob 5000 BTC"  # แก้ไขข้อมูลธุรกรรมในบล็อกที่ 1
blockchain.chain[1].current_hash = blockchain.chain[1].hash()

if blockchain.is_chain_valid():
    print("Chain is valid.")
else:
    print("Chain is invalid!")
print("--------------------------------------------\n")
'''