from time import time
from sage.all import * 
from generate_f_q import generate_prime, irreducible_poly_mod_q

from lagrange_interpolation import recostruct_polynomial 

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

xs = []
ys = []

for alpha, _ in R_q(f).roots():
    xs.append(int(alpha))
    ys.append(int(cipher.secret_poly.lift()(alpha)))

rec = recostruct_polynomial(xs, ys, N, modulo = q)
print(rec)
print(cipher.secret_poly)


