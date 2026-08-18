from sage.arith.misc import euler_phi, next_prime
from sage.functions.log import log
from sage.functions.other import floor, ceil
from sage.misc.functional import cyclotomic_polynomial, round
from sage.misc.functional import sqrt
from sage.misc.prandom import randint
from sage.misc.randstate import set_random_seed
from sage.modules.free_module import FreeModule
from sage.modules.free_module_element import random_vector, vector
from sage.numerical.optimize import find_root
from sage.rings.finite_rings.integer_mod_ring import IntegerModRing
from sage.rings.integer_ring import ZZ
from sage.rings.real_mpfr import RR
from sage.stats.distributions.discrete_gaussian_integer import DiscreteGaussianDistributionIntegerSampler
from sage.stats.distributions.discrete_gaussian_polynomial import DiscreteGaussianDistributionPolynomialSampler
from sage.structure.element import parent
from sage.structure.sage_object import SageObject
from sage.symbolic.constants import pi
from sage.symbolic.ring import SR


class RingLWE(SageObject):
    """
    Ring Learning with Errors oracle.

    .. automethod:: __init__
    .. automethod:: __call__
    """
    def __init__(self, N, q, D, poly=None, secret_dist='uniform', m=None):
        """
        Construct a Ring-LWE oracle in dimension ``n=phi(N)`` over a ring of order
        ``q`` with noise distribution ``D``.

        INPUT:

        - ``N`` -- index of cyclotomic polynomial (integer > 0, must be power of 2)
        - ``q`` -- modulus typically > N (integer > 0)
        - ``D`` -- an error distribution such as an instance of
          :class:`DiscreteGaussianDistributionPolynomialSampler` or :class:`UniformSampler`
        - ``poly`` -- a polynomial of degree ``phi(N)``. If ``None`` the
          cyclotomic polynomial used (default: ``None``).
        - ``secret_dist`` -- distribution of the secret. See documentation of
          :class:`LWE` for details (default='uniform')
        - ``m`` -- number of allowed samples or ``None`` if no such limit exists
          (default: ``None``)

        EXAMPLES::

            sage: from sage.crypto.lwe import RingLWE
            sage: from sage.stats.distributions.discrete_gaussian_polynomial import DiscreteGaussianDistributionPolynomialSampler
            sage: D = DiscreteGaussianDistributionPolynomialSampler(ZZ['x'], n=euler_phi(20), sigma=3.0)                # needs sage.libs.pari
            sage: RingLWE(N=20, q=next_prime(800), D=D)                                 # needs sage.libs.pari
            RingLWE(20, 809, Discrete Gaussian sampler for polynomials of degree < 8 with σ=3.000000 in each component, x^8 - x^6 + x^4 - x^2 + 1, 'uniform', None)
        """
        self.N = ZZ(N)
        self.n = euler_phi(N)
        self.m = m
        self.__i = 0
        self.K = IntegerModRing(q)

        if self.n != D.n:
            raise ValueError("Noise distribution has dimensions %d != %d" % (D.n, self.n))

        self.D = D
        self.q = q
        if poly is not None:
            self.poly = poly
        else:
            self.poly = cyclotomic_polynomial(self.N, 'x')

        self.R_q = self.K['x'].quotient(self.poly, 'x')

        self.secret_dist = secret_dist
        if secret_dist == 'uniform':
            self.__s = self.R_q.random_element()  # uniform sampling of secret
        elif secret_dist == 'noise':
            self.__s = self.D()
        else:
            raise TypeError("Parameter secret_dist=%s not understood." % (secret_dist))

        self.secret_poly = self.__s

    def _repr_(self):
        """
        EXAMPLES::

            sage: from sage.crypto.lwe import DiscreteGaussianDistributionPolynomialSampler, RingLWE
            sage: D = DiscreteGaussianDistributionPolynomialSampler(ZZ['x'], n=8, sigma=3.0)
            sage: RingLWE(N=16, q=next_prime(400), D=D)
            RingLWE(16, 401, Discrete Gaussian sampler for polynomials of degree < 8 with σ=3.000000 in each component, x^8 + 1, 'uniform', None)
        """
        if isinstance(self.secret_dist, str):
            return "RingLWE(%d, %d, %s, %s, '%s', %s)" % (self.N, self.K.order(), self.D, self.poly, self.secret_dist, self.m)
        return "RingLWE(%d, %d, %s, %s, %s, %s)" % (self.N, self.K.order(), self.D, self.poly, self.secret_dist, self.m)

    def __call__(self):
        """
        EXAMPLES::

            sage: # needs sage.libs.pari
            sage: from sage.crypto.lwe import DiscreteGaussianDistributionPolynomialSampler, RingLWE
            sage: N = 16
            sage: n = euler_phi(N)
            sage: D = DiscreteGaussianDistributionPolynomialSampler(ZZ['x'], n, 5)
            sage: ringlwe = RingLWE(N, 257, D, secret_dist='uniform')
            sage: ringlwe()[0].parent()
            Vector space of dimension 8 over Ring of integers modulo 257
            sage: ringlwe()[1].parent()
            Vector space of dimension 8 over Ring of integers modulo 257
        """
        if self.m is not None:
            if self.__i >= self.m:
                raise IndexError("Number of available samples exhausted.")
        self.__i += 1
        a = self.R_q.random_element()
        return vector(a), vector(a * (self.__s) + self.D())


