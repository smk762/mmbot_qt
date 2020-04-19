from web3.auto import w3

def get_checksum_addr(addr):
    return w3.toChecksumAddress(addr)
