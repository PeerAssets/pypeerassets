from ecdsa import scalar_mult
from base64 import b64encode

class ECDH:
    def __init__(self, privkey, pubkey):

        self.p = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f
        self.n = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141

        if not isinstance(privkey,str):
            privkey = privkey.decode() 

        if not isinstance(pubkey,str):
            pubkey = pubkey.decode() 
        
        self.privkey = privkey
        self.pubkey = pubkey
        self.secret = self.get_secret()

    def process_generator(self, G):
        p = self.p
        if not isinstance(G,str):
            G = G.decode()
        prefix = G[:2]
        Gx = int(G[2:], 16)
        y2 = (pow(Gx,3,p)+7) % p
        Gy = pow(y2,(p+1)//4,p) 
        
        if prefix == '03':
            Gy = (-Gy) % p
        
        return (Gx,Gy)

    def get_secret(self):
        privkey = int(self.privkey,16)
        pubkey = self.process_generator(self.pubkey)
        x,y = scalar_mult(privkey,pubkey, self.p, self.n)
        if (y % 2):
            y = (-y) % self.p

        self.full_secret = (hex(x),hex(y))
        return b64encode((x).to_bytes(32,'big'))
