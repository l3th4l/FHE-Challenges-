
from math import floor
from random import randbytes
from sage.all import * 

import os
import ast
from utils import listener 

flag      = os.environ["FLAG1"].encode() # b'fhe{test_flag_424242}'
message   = randbytes(len(flag))


class GLWE():
    """
    General Learning with Errors.
    """
    def __init__(self, N, k, p, q):
        self.N = N 
        self.n = euler_phi(N)
        self.K = IntegerModRing(q)
        self.k = k 

        self.q = q
        self.p = p 
        self.delta = floor(q/p)

        self.poly = cyclotomic_polynomial(self.N, 'x')

        self.R_q = self.K['x'].quotient(self.poly, 'x')
        self.R_q_k = self.R_q ** k 
       
        self.__s = self.R_q_k.random_element()  # uniform sampling of secret

    
    def encrypt(self, msg : list[int]):
        
        assert len(msg) <= self.N 
        
        padded_msg_coeffs = msg + [0] * (self.N - len(msg)) 
        
        M = self.R_q(padded_msg_coeffs) 
        a = self.R_q_k.random_element()

        E = self.R_q([randint(-15, 15) for _ in range(self.N)])

        return Matrix([vector(col) for col in a]), vector(a * (self.__s) + self.delta * M + E)

    def decrypt(self, A, B):

        _A = self.R_q_k(A) 
        _B = self.R_q(B)

        temp_ct = _B - self.R_q(_A * self.__s) 
        return [round(c.lift() / self.delta) % self.p for c in temp_ct.list()]


class Challenge():
    def __init__(self):
        set_random_seed(int.from_bytes(os.urandom(32), "big"))
        self.max_payload_size = 1024*7

        self.before_input = "Welcome to the LWE decryption device! send us the ciphertext and we'll decrypt it for you with our key! \n" 

        self.G1 = GLWE(2**7, 5, 257, next_prime(20000))

        #encrypt the first message 
        self.A1, self.B1 = self.G1.encrypt(list(message)) 
    
        #add the first messsage with the flag
        
        message_plus_flag = bytes([(x + y) % self.G1.p for x, y in zip(message, flag)])

        #encrypt(message + flag) 
        self.A2, self.B2 = self.G1.encrypt(list(message_plus_flag)) 

    def challenge(self, your_input):

        if not "option" in your_input:
            return {"error": "You must send an option to this server"}

        elif your_input["option"] == "get_ciphertext":

            if not "selection" in your_input:
                return {"error": "You must send a selection"}

            if your_input["selection"] == "message":
                return {"A": str(list(self.A1)), "B": str(list(self.B1))}

            elif your_input["selection"] == "combined":
                return {"A": str(list(self.A2)), "B": str(list(self.B2))}

            elif your_input["selection"] == "flag":
                return {"error": "sorry, we cannot send you that :'("}
            else:
                return {"error": "your selection must be one of : message/combined/flag"}

        elif your_input["option"] == "decrypt":
            if (not "A" in your_input) or (not "B" in your_input):
                return {"error": "please send us A and B"} 
            try:
                A_data = ast.literal_eval(your_input["A"])
                B_data = ast.literal_eval(your_input["B"])
            except (ValueError, SyntaxError):
                return {"error": "invalid A/B format"}

            A = list(A_data)
            B = list(B_data)
            
            plaintext = bytes(self.G1.decrypt(A, B))

            if plaintext == message:
                return {"error": "We were told to not decrypt that :'("}
            
            return {"message" : plaintext.decode()}
        else:
            return {"error": "Invalid option"}

import builtins; builtins.Challenge = Challenge
listener.start_server(port=14000)
