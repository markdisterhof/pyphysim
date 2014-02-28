#!/usr/bin/env python
# -*- coding: utf-8 -*-

# http://www.doughellmann.com/PyMOTW/struct/
# import struct
# import binascii

"""Implement class for several modulators, such as PSK and M-QAM.

All modulators inherit from the `Modulator` class and should call the
self.setConstellation method in their __init__ method, as well as implement
the calcTheoreticalSER and calcTheoreticalBER methods.
"""

__revision__ = "$Revision: $"

__all__ = ['Modulator', 'PSK', 'QPSK', 'BPSK', 'QAM']

try:
    import matplotlib.pyplot as plt
    _MATPLOTLIB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _MATPLOTLIB_AVAILABLE = False

import numpy as np
import math

from ..util.misc import level2bits, qfunc
from ..util.conversion import gray2binary, binary2gray, dB2Linear

PI = np.pi


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxx Modulator Class xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
class Modulator(object):
    """Base class for digital modulators.

    The derived classes need to at least call setConstellation to set the
    constellation in their constructors as well as implement
    calcTheoreticalSER and calcTheoreticalBER.

    Examples
    --------
    >>> constellation = np.array([1+1j, -1+1j, -1-1j, 1-1j])
    >>> m=Modulator()
    >>> m.setConstellation(constellation)
    >>> m.symbols
    array([ 1.+1.j, -1.+1.j, -1.-1.j,  1.-1.j])
    >>> m.M
    4
    >>> m.K
    2.0
    >>> m
    4-Modulator object
    >>> m.modulate(np.array([0, 0, 3, 3, 1, 3, 3, 3, 2, 2]))
    array([ 1.+1.j,  1.+1.j,  1.-1.j,  1.-1.j, -1.+1.j,  1.-1.j,  1.-1.j,
            1.-1.j, -1.-1.j, -1.-1.j])

    >>> m.demodulate(np.array([ 1.+1.j, 1.+1.j, 1.-1.j, 1.-1.j, -1.+1.j, \
                                1.-1.j, 1.-1.j, 1.-1.j, -1.-1.j, -1.-1.j]))
    array([0, 0, 3, 3, 1, 3, 3, 3, 2, 2])
    """

    def __init__(self):
        """Initializes the Modulator object.
        """
        # This should be set in a subclass of the Modulator Class by
        # calling the setConstellation method..
        self._M = 0  # Constellation size (modulation cardinality)
        self._K = 0  # Number of bits represented by each symbol in the
                     # constellation
        self.symbols = np.array([])

    @property
    def name(self):
        """Get method for the 'name' property."""
        return "{0:d}-{1:s}".format(self._M, self.__class__.__name__)

    def _get_M(self):
        """Get method for the M property.

        The `M` property corresponds to the number of symbols in the
        constellation.

        See also
        --------
        K
        """
        return self._M
    M = property(_get_M)

    def _get_K(self):
        """Get method for the K property.

        The `K` property corresponds to the number of bits represented by
        each symbol in the constellation. It is equal to log2(M), where `M`
        is the constellation size.

        See also
        --------
        M
        """
        return self._K
    K = property(_get_K)

    def __repr__(self):  # pragma: no cover
        return "{0} object".format(self.name)

    def setConstellation(self, symbols):
        """Set the constellation of the modulator.

        This function should be called in the constructor of the derived
        classes.

        Parameters
        ----------
        symbols : numpy array
            A an numpy array with the symbol table.

        """
        M = symbols.size
        self._M = M
        self._K = np.log2(M)
        self.symbols = symbols

    def plotConstellation(self):  # pragma: no cover
        """Plot the constellation (in a scatter plot).
        """
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)  # one row, one column, first plot
        # circlePatch = patches.Circle((0,0),1)
        # circlePatch.set_fill(False)
        # ax.add_patch(circlePatch)
        ax.scatter(self.symbols.real, self.symbols.imag)

        ax.axis('equal')
        ax.grid()

        formatString = "{0:0=" + str(level2bits(self._M)) + "b} ({0})"

        index = 0
        for symbol in self.symbols:
            ax.text(
                symbol.real,  # Coordinate X
                symbol.imag + 0.03,  # Coordinate Y
                formatString.format(index, format_spec="0"),  # Text
                verticalalignment='bottom',  # From now on, text properties
                horizontalalignment='center')
            index += 1

        plt.show()

    def modulate(self, inputData):
        """Modulate the input data (decimal data).

        Parameters
        ----------
        inputData : Numpy array
            Data to be modulated.

        Returns
        -------
        modulated_data : numpy array
            The modulated data

        Raises
        ------
        ValueError
            If inputData has any invalid value such as values greater than
            self._M - 1. Note that inputData should not have negative values
            but no check is done for this.

        """
        try:
            return self.symbols[inputData]
        except IndexError:
            raise ValueError("Input data must be between 0 and 2^M")

    def demodulate(self, receivedData):
        """Demodulate the data.

        Parameters
        ----------
        receivedData : numpy array
            Data to be demodulated.

        Returns
        -------
        demodulated_data : numpy array
            The demodulated data.
        """
        ### First Try xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        # def getClosestSymbol(symb):
        #     closestSymbolIndex = np.abs(self.symbols - symb).argmin()
        #     return closestSymbolIndex
        # getClosestSymbol = np.frompyfunc(getClosestSymbol, 1, 1)
        # return getClosestSymbol(receivedData).astype(int)
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # ### Second Try xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        # # This versions is a little faster then the first version
        # shape = receivedData.shape
        # num_symbols = receivedData.size
        # output = np.empty(num_symbols, dtype=int)
        # reshaped_received_data = receivedData.flatten()

        # # import pudb
        # # pudb.set_trace()
        # for ii in xrange(num_symbols):
        #     output[ii] = np.abs(self.symbols - reshaped_received_data[ii]).argmin()
        # output.shape = shape
        # return output
        # # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        ### Third Try xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        # This version uses more memory because of the numpy broadcasting,
        # but it is much faster.
        shape = receivedData.shape
        num_symbols = receivedData.size
        output = np.empty(num_symbols, dtype=int)
        reshaped_received_data = receivedData.flatten()

        constellation = np.reshape(self.symbols, [self.symbols.size, 1])
        output = np.abs(constellation - reshaped_received_data).argmin(axis=0)
        output.shape = shape

        return output
        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

    def calcTheoreticalSER(self, SNR):  # pragma: no cover
        """Calculates the theoretical symbol error rate.

        Parameters
        ----------
        SNR : float or array like
            Signal-to-noise-value (in dB).

        Returns
        -------
        SER : float or array like
            The theoretical symbol error rate.

        See also
        --------
        calcTheoreticalBER,
        calcTheoreticalPER

        Notes
        -----
        This function should be implemented in the derived classes
        """
        raise NotImplementedError("calcTheoreticalSER: Not implemented")

    def calcTheoreticalBER(self, SNR):  # pragma: no cover
        """Calculates the theoretical bit error rate.

        Parameters
        ----------
        SNR : float or array like
            Signal-to-noise-value (in dB).

        Returns
        -------
        BER : float or array like
            The theoretical bit error rate.

        See also
        --------
        calcTheoreticalSER,
        calcTheoreticalPER

        Notes
        -----
        This function should be implemented in the derived classes
        """
        raise NotImplementedError("calcTheoreticalBER: Not implemented")

    def calcTheoreticalPER(self, SNR, packet_length):
        """Calculates the theoretical package error rate.

        A package is a group of bits, where if a single bit is in error
        then the whole package is considered to be in error.

        The package error rate (PER) is a direct mapping of the bit error
        rate (BER), such that

        .. math::
           PER = 1 - (1 - BER)^{L}

        where :math:`L` is the package_length.

        Parameters
        ----------
        SNR : float or array like
            Signal-to-noise-value (in dB).
        packet_length : int
            The package length. That is, the number of bits in each
            package.

        Returns
        -------
        PER : float
            The theoretical package error rate.

        See also
        --------
        calcTheoreticalBER,
        calcTheoreticalSER
        calcTheoreticalSpectralEfficiency
        """
        BER = self.calcTheoreticalBER(SNR)
        PER = 1 - ((1 - BER) ** packet_length)
        return PER

    def calcTheoreticalSpectralEfficiency(self, SNR, packet_length=None):
        """Calculates the theoretical spectral efficiency.

        If there was no error in the transmission, the spectral efficiency
        would be equal to the `K` property, that is, equal to the number of
        bits represented by each symbol in the constellation. However, due
        to bit errors the effective spectral efficiency will be lower.

        The calcTheoreticalSpectralEfficiency method calculates the
        effective spectral efficiency from the `K` property and the package
        error rate (PER) for the given SNR and packet_length 'L', such that

        .. math::
           se = K * (1 - PER)

        Parameters
        ----------
        SNR : float or array like
            Signal-to-noise-value (in dB).
        packet_length : int
            The package length. That is, the number of bits in each
            package.

        Returns
        -------
        se : float of array like (same as the SNR attribute)
            The theoretical spectral efficiency.

        See also
        --------
        calcTheoreticalBER,
        calcTheoreticalPER,
        K

        """
        if packet_length is None:
            se = self.K * (1 - self.calcTheoreticalBER(SNR))
        else:
            se = self.K * (1 - self.calcTheoreticalPER(SNR, packet_length))
        return se

# xxxxx End of Modulator Class xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxx PSK Class xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
class PSK(Modulator):
    """PSK Class
    """
    def __init__(self, M, phaseOffset=0):
        """Initializes the PSK object.

        Parameters
        ----------
        M : int
            The modulation cardinality
        phaseOffset: float, optional (default to 0)
            A phase offset (in radians) to be applied to the PSK
            constellation.

        """
        Modulator.__init__(self)
        # Check if M is a power of 2
        assert 2 ** math.log(M, 2) == M

        # Generates the constellation
        symbols = self._createConstellation(M, phaseOffset)

        # Change to Gray mapping
        symbols = symbols[gray2binary(np.arange(0, M))]

        self.setConstellation(symbols)

    @staticmethod
    def _createConstellation(M, phaseOffset):
        """Generates the Constellation for the PSK modulation scheme.

        Parameters
        ----------
        M : int
            The modulation cardinality
        phaseOffset: float
            A phase offset (in radians) to be applied to the PSK
            constellation.

        Returns
        -------
        symbols : numpy array
            The PSK constellation with the desired cardinality and phase
            offset.

        """
        phases = 2. * PI / M * np.arange(0, M) + phaseOffset
        realPart = np.cos(phases)
        imagPart = np.sin(phases)

        # Any number inferior to 1e-15 will be considered as 0
        realPart[abs(realPart) < 1e-15] = 0
        imagPart[abs(imagPart) < 1e-15] = 0
        return realPart + 1j * imagPart

    def setPhaseOffset(self, phaseOffset):
        """Set a new phase offset for the constellation

        Parameters
        ----------
        phaseOffset: float
            A phase offset (in radians) to be applied to the PSK
            constellation.
        """
        self.setConstellation(self._createConstellation(self._M, phaseOffset))

    def calcTheoreticalSER(self, SNR):
        """Calculates the theoretical (approximation for high M and high
        SNR) symbol error rate for the M-PSK scheme.

        Parameters
        ----------
        SNR : float or array like
            Signal-to-noise-value (in dB).

        Returns
        -------
        SER : float or array like
            The theoretical symbol error rate.
        """
        snr = dB2Linear(SNR)

        # $P_s \approx 2Q\left(\sqrt{2\gamma_s}\sin\frac{\pi}{M}\right)$
        # Alternative formula (same result)
        # $P_s = erfc \left ( \sqrt{\gamma_s} \sin(\frac{\pi}{M})  \right )$
        ser = 2. * qfunc(np.sqrt(2. * snr) * math.sin(PI / self._M))
        return ser

    def calcTheoreticalBER(self, SNR):
        """Calculates the theoretical (approximation) bit error rate for
        the M-PSK scheme using Gray coding.

        Parameters
        ----------
        SNR : float or array like
            Signal-to-noise-value (in dB).

        Returns
        -------
        BER : float or array like
            The theoretical bit error rate.
        """
        # $P_b = \frac{1}{k}P_s$
        # Number of bits per symbol
        k = level2bits(self._M)
        return 1.0 / k * self.calcTheoreticalSER(SNR)


# xxxxx End of PSK Class xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxx QPSK Class xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
class QPSK(PSK):  # pragma: no cover
    """QPSK Class
    """

    def __init__(self):
        PSK.__init__(self, 4, PI / 4.)

    def __repr__(self):  # pragma: no cover
        return "QPSK object"
# xxxxx End of QPSK Class xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxx BPSK Class xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
class BPSK(Modulator):
    """BPSK Class
    """
    def __init__(self):
        Modulator.__init__(self)
        # The number "1" will be mapped to "-1" and the number "0" will be
        # mapped to "1"
        self.setConstellation(np.array([1, -1]))

    @property
    def name(self):
        return "{0:s}".format(self.__class__.__name__)

    def __repr__(self):  # pragma: no cover
        return "BPSK object"

    def calcTheoreticalSER(self, SNR):
        """Calculates the theoretical (approximation) symbol error rate for
        the BPSK scheme.

        Parameters
        ----------
        SNR : float or array like
            Signal-to-noise-value (in dB).

        Returns
        -------
        SER : float or array like
            The theoretical symbol error rate.
        """
        snr = dB2Linear(SNR)
        # $P_b = Q\left(\sqrt{\frac{2E_b}{N_0}}\right)$
        # Alternative formula (same result)
        # $P_b = \frac{1}{2}erfc \left ( \sqrt{\frac{E_b}{N_0}} \right )$
        ser = qfunc(np.sqrt(2 * snr))
        return ser

    def calcTheoreticalBER(self, SNR):
        """Calculates the theoretical (approximation) bit error rate for
        the BPSK scheme.

        Parameters
        ----------
        SNR : float or array like
            Signal-to-noise-value (in dB).

        Returns
        -------
        BER : float or array like
            The theoretical bit error rate.
        """
        return self.calcTheoreticalSER(SNR)

    def modulate(self, inputData):
        """Modulate the input data (decimal data).

        Parameters
        ----------
        inputData : Numpy array
            Data to be modulated.

        Returns
        -------
        modulated_data : numpy array
            The modulated data

        Raises
        ------
        ValueError
            If inputData has any invalid value such as values greater than
            self._M - 1. Note that inputData should not have negative values
            but no check is done for this.

        """
        if np.any(inputData > 1):
            raise ValueError("Input data can only contains '0's and '1's")
        return 1 - 2 * inputData

    def demodulate(self, receivedData):
        """Demodulate the data.

        Parameters
        ----------
        receivedData : numpy array
            Data to be demodulated.

        Returns
        -------
        demodulated_data : numpy array
            The demodulated data.
        """
        return (receivedData < 0).astype(int)

# xxxxx End of BPSK Class xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxx QAM Class xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
class QAM(Modulator):
    """QAM Class
    """

    def __init__(self, M):
        """Initializes the QAM object.

        Parameters
        ----------
        M : int
            The modulation cardinality

        Raises
        ------
        ValueError
            If M is not a square power of 2.
        """
        Modulator.__init__(self)

        # Check if M is an even power of 2
        power = math.log(M, 2)
        if (power % 2 != 0) or (2 ** power != M):
            raise ValueError("M must be a square power of 2")

        symbols = self._createConstellation(M)

        L = int(round(math.sqrt(M)))
        grayMappingIndexes = self._calculateGrayMappingIndexQAM(L)
        symbols = symbols[grayMappingIndexes]

        # Set the constellation
        self.setConstellation(symbols)

    @staticmethod
    def _createConstellation(M):
        """Generates the Constellation for the (SQUARE) M-QAM modulation
        scheme.

        Parameters
        ----------
        M : int
            The modulation cardinality

        Returns
        -------
        symbols : numpy array
            The QAM constellation with the desired cardinality.
        """
        # Size of the square. The square root is exact
        symbols = np.empty(M, dtype=complex)
        L = int(round(math.sqrt(M)))
        for jj in range(0, L):
            for ii in range(0, L):
                symbol = complex(-(L - 1) + jj * 2, (L - 1) - ii * 2)
                #print symbol
                symbols[ii * L + jj] = symbol

        average_energy = (M - 1) * 2.0 / 3.0
        # Normalize the constellation, so that the mean symbol energy is
        # equal to one.
        return symbols / math.sqrt(average_energy)

    @staticmethod
    def _calculateGrayMappingIndexQAM(L):
        """Calculates the indexes that should be applied to the
        constellation created by _createConstellation in order to
        correspond to Gray mapping.

        Notice that the square M-QAM constellation is a matrix of dimension
        L x L, where L is the square root of M. Since the constellation was
        generated without taking into account the Gray mapping, then we
        need to reorder the generated constellation and this function
        calculates the indexes that can be applied to the original
        constellation in order to do exactly that.

        As an example, for the 16-QAM modulation the indexes can be
        organized (row order) in the matrix below

        .. aafig::
                  00     01     11     10
               +------+------+------+------+
            00 | 0000 | 0001 | 0011 | 0010 |
            01 | 0100 | 0101 | 0111 | 0110 |
            11 | 1100 | 1101 | 1111 | 1110 |
            10 | 1000 | 1001 | 1011 | 1010 |
               +------+------+------+------+

        This is equivalent to concatenate a Gray mapping for the row with a
        Gray mapping for the column, and the corresponding indexes are
        [0, 1, 3, 2, 4, 5, 7, 6, 12, 13, 15, 14, 8, 9, 11, 10]

        Parameters
        ----------
        L : int
            Square root of the modulation cardinality (must be an integer).

        Returns
        -------
        indexes : numpy array of integers
            indexes that should be applied to the constellation created by
            _createConstellation in order to correspond to Gray mapping

        """
        # Row vector with the column variation (second half of the index in
        # binary form)
        column = binary2gray(np.arange(0, L, dtype=int))
        # Column vector with the row variation
        row = column.reshape(L, 1)  # Column vector with the row variation
                                    # (first half of the index in binary
                                    # form)
        columns = np.tile(column, (L, 1))
        rows = np.tile(row, (1, L))
        # Shift the first part by half the number of bits and sum with the
        # second part to form each element in the index matrix
        index_matrix = (rows << (level2bits(L ** 2) // 2)) + columns

        # Return the indexes as a vector (row order, which is the default
        # in numpy)
        return np.reshape(index_matrix, L ** 2)

    def _calcTheoreticalSingleCarrierErrorRate(self, SNR):
        """Calculates the theoretical (approximation) error rate of a
        single carrier in the QAM system (QAM has two carriers).

        Parameters
        ----------
        SNR : float or array like
            Signal-to-noise-value (in dB).

        Returns
        -------
        Psc : float or array like
            The theoretical single carrier error rate.

        Notes
        -----
        This method is used in the :meth:`calcTheoreticalSER`
        implementation.

        See also
        --------
        calcTheoreticalSER

        """
        snr = dB2Linear(SNR)
        # Probability of error of each carrier in a square QAM
        # $P_{sc} = 2\left(1 - \frac{1}{\sqrt M}\right)Q\left(\sqrt{\frac{3}{M-1}\frac{E_s}{N_0}}\right)$
        sqrtM = np.sqrt(self._M)
        Psc = 2. * (1. - (1. / sqrtM)) * qfunc(np.sqrt(snr * 3. / (self._M - 1.)))
        return Psc

    def calcTheoreticalSER(self, SNR):
        """Calculates the theoretical (approximation) symbol error rate for
        the QAM scheme.

        Parameters
        ----------
        SNR : float or array like
            Signal-to-noise-value (in dB).

        Returns
        -------
        SER : float or array like
            The theoretical symbol error rate.
        """
        Psc = self._calcTheoreticalSingleCarrierErrorRate(SNR)
        # The SER is then given by
        # $ser = 1 - (1 - Psc)^2$
        ser = 1 - (1 - Psc) ** 2
        return ser

    def calcTheoreticalBER(self, SNR):
        """Calculates the theoretical (approximation) bit error rate for
        the QAM scheme.

        Parameters
        ----------
        SNR : float or array like
            Signal-to-noise-value (in dB).

        Returns
        -------
        BER : float or array like
            The theoretical bit error rate.
        """
        # For higher SNR values and gray mapping, each symbol error
        # corresponds to approximately a single bit error. The BER is then
        # given by the probability of error of a single carrier in the QAM
        # system divided by the number of bits transported in that carrier.
        k = level2bits(self._M)
        Psc = self._calcTheoreticalSingleCarrierErrorRate(SNR)
        ber = (2. * Psc) / k
        return ber
# xxxxx End of QAM Class xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx