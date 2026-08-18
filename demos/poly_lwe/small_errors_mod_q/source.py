from itertools import product as cart
from time import time
from sage.all import * 
from generate_f_q import generate_prime, irreducible_poly_mod_q

from rlwe import DiscreteGaussianDistributionPolynomialSampler, RingLWE

from matplotlib import pyplot as plt 
import numpy as np 
from math import ceil


N = 4 
d = 7 
sigma = 2

q =  generate_prime(n = 7, max_k = 50)
R_q = PolynomialRing(Zmod(q), 'x')

#find a polynomial 
f = irreducible_poly_mod_q(q, order = d, n = N)
D = DiscreteGaussianDistributionPolynomialSampler(ZZ['x'], n=euler_phi(N), sigma=sigma)

cipher = RingLWE(N, q, D, poly = f)


print(f"f(x) = {R_q(f)} (mod {q})")

print(f"[factorized] f(x) = {R_q(f).factor()} (mod {q})")

print("roots of f(x) : ", R_q(f).roots())

#Generate samples 
samples = [cipher() for _ in range(30)]

alpha = R_q(f).roots()[0][0]


def generate_all_error_coefficients(n, sigma, truncate_limit=4, moduli=None):
    """Generate all possible vectors."""
    max_val = int(math.ceil(truncate_limit * sigma))
    possible_values = range(-max_val, max_val + 1)

    for vec in cart(possible_values, repeat=n):
        if moduli:
            yield vector(Zmod(moduli), vec)        
        else:
            yield vector(vec)


def generate_error_set(alpha, d, q, n, sigma):
    alpha_is = vector(Zmod(q), [pow(alpha, i, q) for i in range(n)])
    error_coeffs = Matrix(Zmod(q), generate_all_error_coefficients(n, sigma, truncate_limit=4))
    S = error_coeffs * alpha_is
    
    return set(S)

a1,  b1 = samples[0]
a2,  b2 = samples[1]

S = generate_error_set(alpha, d, q, N, sigma)


print(f"\n\nThe homomorphic image of the secret under alpha = {alpha} should be : {cipher.secret_poly.lift()(alpha)}")

print(" ---- Searching for the secret ---- ")

start = time()
for g in range(0, q):
    valid = True
    for a, b in samples[:5]:
        e1_alpha = R_q(list(b - g*a))(alpha)
        if not(e1_alpha in S):
            valid = False
            break 
    if valid:
        print(f"\nWe've found {g} to be a valid guess for the secret during search")
        print(f"\ntime taken = {time() - start:.2f} seconds") 
       
