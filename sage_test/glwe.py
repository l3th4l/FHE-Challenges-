from math import floor
from sage.arith.misc import Integer, euler_phi
from sage.misc.functional import cyclotomic_polynomial
from sage.modules.free_module_element import vector
from sage.rings.finite_rings.integer_mod_ring import IntegerModRing, Zmod
from sage.rings.integer_ring import ZZ
from sage.stats.distributions.discrete_gaussian_integer import DiscreteGaussianDistributionIntegerSampler
from sage.stats.distributions.discrete_gaussian_polynomial import DiscreteGaussianDistributionPolynomialSampler
from sage.structure.element import parent
from sage.structure.sage_object import SageObject
from sage.symbolic.constants import pi
from sage.symbolic.ring import SR

class GLWE(SageObject):
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

        return vector(a), self.R_q(a * (self.__s) + self.delta * M + E)

    def decrypt(self, A, B):

        temp_ct = B.lift() - self.R_q(A * self.__s).lift() 
        return [ round(c.lift() / self.delta) % self.p for c in temp_ct.list()]

if __name__ == "__main__":

    from sage.all import * 
    message = b'fhe{this is a test hehe how many bytes can we go}'
    flag = b'fhe{well_aint_this_awesome}'

    G1 = GLWE(2**7, 2**5, 257, next_prime(2**30))
    A1, B1 = G1.encrypt(list(message)) 
    dec = G1.decrypt(A1, B1)
    print(bytes(dec))
