#!/usr/bin/env python
"""

Copyright (c) 2022 Karol Budniak <karol.budniak@missinglinkelectronics.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

from . import node


PRINT_VERBOSITY_TRACE = 4
PRINT_VERBOSITY_INFO = 3
PRINT_VERBOSITY_WARN = 2
PRINT_VERBOSITY_ERROR = 1
PRINT_VERBOSITY_QUIET = 0
PRINT_VERBOSITY = PRINT_VERBOSITY_INFO

# register offsets taken from Intel document:
# L- and H-Tile Transceiver PHY User Guide 683621 | 2022.07.20
# chapter A. Logical View of the L-Tile/H-Tile Transceiver Registers
# pages 480-504

PRBS_MODE_OFF    = 0b00000
PRBS_MODE_PRBS7  = 0b00001
PRBS_MODE_PRBS9  = 0b00010
PRBS_MODE_PRBS15 = 0b00100
PRBS_MODE_PRBS23 = 0b01000
PRBS_MODE_PRBS31 = 0b10000

prbs_mode_mapping = {
    'off': PRBS_MODE_OFF,
    'prbs7': PRBS_MODE_PRBS7,
    'prbs9': PRBS_MODE_PRBS9,
    'prbs15': PRBS_MODE_PRBS15,
    'prbs23': PRBS_MODE_PRBS23,
    'prbs31': PRBS_MODE_PRBS31
}

PRBS_GENERATOR_TX_PMA_DATA_SEL_SQUARE_WAVE = 0b00101
PRBS_GENERATOR_TX_PMA_DATA_SEL_PRBS_PATTERN = 0b00100

PRBS_GENERATOR_PRBS9_DWIDTH_ENABLE = 0b1
PRBS_GENERATOR_PRBS9_DWIDTH_DISABLE = 0b0

PRBS_GENERATOR_SERIALIZER_MODE_64BIT = 0b011
PRBS_GENERATOR_SERIALIZER_MODE_10BIT = 0b100

prbs_generator_serializer_mode_mapping = {
    64: PRBS_GENERATOR_SERIALIZER_MODE_64BIT,
    10: PRBS_GENERATOR_SERIALIZER_MODE_10BIT
}

PRBS_VERIFIER_DESERIALIZER_FACTOR_64BIT = 0xE
PRBS_VERIFIER_DESERIALIZER_FACTOR_10BIT = 0x1

prbs_verifier_deserializer_factor_mapping = {
    64: PRBS_VERIFIER_DESERIALIZER_FACTOR_64BIT,
    10: PRBS_VERIFIER_DESERIALIZER_FACTOR_10BIT
}

class LTileHTileNode(node.MemoryNode):
    # expected byte address
    def masked_read(self, addr, mask):
        # multiple byte address by 4 so it does not get
        # truncated because of 32 bit access of AXI4-Lite (converted to Avalon-MM)
        val = self.read_word(addr << 2) & mask
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: masked_read: address: " + str(hex(addr)) + ", mask: " + str(hex(mask)) + ", data: " + str(hex(val)))
        return val

    # expected byte address
    def masked_write(self, addr, mask, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: masked_write: address: " + str(hex(addr)) + ", mask: " + str(hex(mask) + ", data: " + str(hex(val))))
        # multiple byte address by 4 so it does not get
        # truncated because of 32 bit access of AXI4-Lite (converted to Avalon-MM)
        return self.write_word(addr << 2, (self.read_word(addr << 2) & ~mask) | (val & mask))

    def dump_reg_space(self, addr_off, start, stop):
        for addr in range(start, stop, 0x001):
            print("Address: " + str(hex(addr)) + ": " + str(hex(self.masked_read(addr_off, addr, 0xFF))))

    # return True if the receiver is locked to data
    def get_rx_locked_to_data(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_rx_locked_to_data")
        return bool(self.masked_read((addr_off << 11) + 0x480, 0x0001))

    # return True if the receiver is locked to reference clock
    def get_rx_locked_to_ref(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_rx_locked_to_ref")
        return bool(self.masked_read((addr_off << 11) + 0x480, 0x0002))

    # steps to follow to view Eyescan may also apply to run BER measurement
    # presented in documentation L- and H-Tile Transceiver PHY User Guide 683621 | 2022.07.20
    # on pages 161 - 162
    def disable_background_calibration(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: disable_background_calibration")
        self.masked_write((addr_off << 11) + 0x542, 0x01, 0x00)

    def is_avmm_bus_busy(self, addr_off):
        # return True if PreSICE has control of the internal configuration bus
        # return False if you have control of internal configuration bus
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: is_avmm_bus_busy")
        return bool(self.masked_read((addr_off << 11) + 0x481, 0x04))

    def is_rx_adaption_mode_manual(self, addr_off):
        # return True if RX adaptation is in manual mode, return False otherwise
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: is_rx_adaption_mode_manual")
        return bool(self.masked_read((addr_off << 11) + 0x161, 0x20))

    def release_adaptation_from_reset(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: release_adaptation_from_reset")
        self.masked_write((addr_off << 11) + 0x148, 0x01, 0x01)

    def enable_cnt_to_detect_error_bits(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: enable_cnt_to_detect_error_bits")
        self.masked_write((addr_off << 11) + 0x169, 0x40, 0x01)

    def enable_serial_bit_checker(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: enable_serial_bit_checker")
        self.masked_write((addr_off << 11) + 0x168, 0x01, 0x01)

    def is_dfe_enabled(self, addr_off):
        # return True if DFE is enabled, return False otherwise
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: is_dfe_enabled")
        return True if (self.masked_read((addr_off << 11) + 0x161, 0x40) == 0) else False

    def enable_dfe_speculation(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: enable_dfe_speculation")
        self.masked_write((addr_off << 11) + 0x169, 0x04, 0x04)

    def disable_dfe_speculation(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: disable_dfe_speculation")
        self.masked_write((addr_off << 11) + 0x169, 0x04, 0x00)

    def enable_serial_bit_checker_control(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: enable_serial_bit_checker_control")
        self.masked_write((addr_off << 11) + 0x158, 0x20, 0x20)

    # PRBS Generator registers
    def get_prbs_gen_prbs_tx_pma_data_sel(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_gen_prbs_tx_pma_data_sel")
        # bits[4:3] from 0x008[6:5]
        msb = self.masked_read((addr_off << 11) + 0x008, 0b1100000) >> 5
        # bits[2:0] from 0x006[2:0]
        lsb = self.masked_read((addr_off << 11) + 0x006, 0b00111) >> 0
        val = (msb << 3) + lsb
        return val

    def set_prbs_gen_prbs_tx_pma_data_sel(self, addr_off, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_gen_prbs_tx_pma_data_sel")
        if ((val != PRBS_GENERATOR_TX_PMA_DATA_SEL_SQUARE_WAVE) and \
                (val != PRBS_GENERATOR_TX_PMA_DATA_SEL_PRBS_PATTERN)):
            if (PRINT_VERBOSITY >= PRINT_VERBOSITY_ERROR):
                print("ERROR: set_prbs_gen_prbs_tx_pma_data_sel: unsupport TX PMA data selected: " + str(hex(val)))
            exit(1)
        # bits[4:3] to 0x008[6:5]
        self.masked_write((addr_off << 11) + 0x008, 0b1100000, (val & 0b11000) << 2)
        # bits[2:0] to 0x006[2:0]
        self.masked_write((addr_off << 11) + 0x006, 0b00111, val & 0b00111)

    def get_prbs_gen_prbs9_dwidth(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_gen_prbs9_dwidth")
        return bool(self.masked_read((addr_off << 11) + 0x006, 0x0008))

    def set_prbs_gen_prbs9_dwidth(self, addr_off, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_gen_prbs9_dwidth")
        self.masked_write((addr_off << 11) + 0x006, 0x0008, 0x0008 if val else 0x0000)

    def get_prbs_gen_prbs_clken(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_gen_prbs_clken")
        return bool(self.masked_read((addr_off << 11) + 0x006, 0x0040))

    def set_prbs_gen_prbs_clken(self, addr_off, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_gen_prbs_clken")
        self.masked_write((addr_off << 11) + 0x006, 0x0040, 0x0040 if val else 0x0000)

    def get_prbs_gen_prbs_pat(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_gen_prbs_pat")
        # bit[4] from 0x008[4]
        msb = self.masked_read((addr_off << 11) + 0x008, 0x0010)
        # bits[3:0] from 0x007[7:4]
        lsb = self.masked_read((addr_off << 11) + 0x007, 0x00F0) >> 4
        val = msb + lsb
        return val

    def set_prbs_gen_prbs_pat(self, addr_off, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_gen_prbs_pat")
        # check if argument is a string and map it to register value
        if type(val) is str:
            val = prbs_mode_mapping[val]
        else:
            if (PRINT_VERBOSITY >= PRINT_VERBOSITY_ERROR):
                print("ERROR: set_prbs_gen_prbs_pat: argument given is not a string")
            exit(1)
        if ((val != PRBS_MODE_OFF) and \
                 (val != PRBS_MODE_PRBS7) and \
                 (val != PRBS_MODE_PRBS9) and \
                 (val != PRBS_MODE_PRBS15) and \
                 (val != PRBS_MODE_PRBS23) and \
                 (val != PRBS_MODE_PRBS31)):
            if (PRINT_VERBOSITY >= PRINT_VERBOSITY_ERROR):
                print("ERROR: set_prbs_gen_prbs_pat: unsupported PRBS pattern selected: " + str(hex(val)))
            exit(1)
        # bit[4] to 0x008[4]
        self.masked_write((addr_off << 11) + 0x008, 0x0010, val & 0x0010)
        # bits[3:0] to 0x007[7:4]
        self.masked_write((addr_off << 11) + 0x007, 0x00F0, (val & 0x000F) << 4)

    def get_prbs_gen_ser_mode(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_gen_ser_mode")
        read = self.masked_read((addr_off << 11) + 0x110, 0x0007)
        if (read == PRBS_GENERATOR_SERIALIZER_MODE_64BIT):
            return 64
        elif (read == PRBS_GENERATOR_SERIALIZER_MODE_10BIT):
            return 10
        else:
            if (PRINT_VERBOSITY >= PRINT_VERBOSITY_WARN):
                print("WARN: get_prbs_gen_ser_mode: unknown PRBS generator serializer mode: " + str(hex(read)))
            return 0

    def set_prbs_gen_ser_mode(self, addr_off, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_gen_ser_mode")
        if type(val) is int:
            val = prbs_generator_serializer_mode_mapping[val]
        else:
            if (PRINT_VERBOSITY >= PRINT_VERBOSITY_ERROR):
                print("ERROR: set_prbs_gen_ser_mode: argument given is not an integer")
            exit(1)
        if ((val != PRBS_GENERATOR_SERIALIZER_MODE_64BIT) and
                (val != PRBS_GENERATOR_SERIALIZER_MODE_10BIT)):
            if (PRINT_VERBOSITY >= PRINT_VERBOSITY_ERROR):
                print("ERROR: set_prbs_gen_ser_mode: unsupported PRBS generator serializer mode: " + str(hex(val)))
            exit(1)
        self.masked_write((addr_off << 11) + 0x110, 0x0007, val & 0x0007)

    # PRBS Verifier registers
    def get_prbs_ver_prbs_clken(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_ver_prbs_clken")
        return bool(self.masked_read((addr_off << 11) + 0x00A, 0x0080))

    def set_prbs_ver_prbs_clken(self, addr_off, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_ver_prbs_clken")
        self.masked_write((addr_off << 11) + 0x00A, 0x0080, 0x0080 if val else 0x0000)

    def get_prbs_ver_rx_prbs_mask(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_ver_rx_prbs_mask")
        return (self.masked_read((addr_off << 11) + 0x00B, 0x000C) >> 2)

    def set_prbs_ver_rx_prbs_mask(self, addr_off, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_ver_rx_prbs_mask")
        self.masked_write((addr_off << 11) + 0x00B, 0x000C, val << 2)

    def get_prbs_ver_prbs_pat(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_ver_prbs_pat")
        # bit[4] from 0x00C[0]
        msb = self.masked_read((addr_off << 11) + 0x00C, 0x0001)
        # bits[3:0] from 0x00B[7:4]
        lsb = self.masked_read((addr_off << 11) + 0x00B, 0x00F0) >> 4
        val = (msb << 4) + lsb
        return val

    def set_prbs_ver_prbs_pat(self, addr_off, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_ver_prbs_pat")
        # check if argument is a string and map it to register value
        if type(val) is str:
            val = prbs_mode_mapping[val]
        else:
            if (PRINT_VERBOSITY >= PRINT_VERBOSITY_ERROR):
                print("ERROR: set_prbs_ver_prbs_pat: argument given is not a string")
            exit(1)
        if ((val != PRBS_MODE_OFF) and \
                 (val != PRBS_MODE_PRBS7) and \
                 (val != PRBS_MODE_PRBS9) and \
                 (val != PRBS_MODE_PRBS15) and \
                 (val != PRBS_MODE_PRBS23) and \
                 (val != PRBS_MODE_PRBS31)):
            if (PRINT_VERBOSITY >= PRINT_VERBOSITY_ERROR):
                print("ERROR: set_prbs_ver_prbs_pat: unsupported PRBS pattern selected: " + str(hex(val)))
            exit(1)
        # bit[4] to 0x00C[0]
        self.masked_write((addr_off << 11) + 0x00C, 0x0001, (val & 0x0010) >> 4)
        # bits[3:0] to 0x00B[7:4]
        self.masked_write((addr_off << 11) + 0x00B, 0x00F0, (val & 0x000F) << 4)

    def get_prbs_ver_prbs9_dwidth(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_ver_prbs9_dwidth")
        return bool(self.masked_read((addr_off << 11) + 0x00C, 0x0008))

    def set_prbs_ver_prbs9_dwidth(self, addr_off, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_ver_prbs9_dwidth")
        self.masked_write((addr_off << 11) + 0x00C, 0x0008, 0x0008 if val else 0x0000)

    def get_prbs_ver_deser_factor(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_ver_deser_factor")
        read = self.masked_read((addr_off << 11) + 0x13F, 0x000F)
        if (read == PRBS_VERIFIER_DESERIALIZER_FACTOR_64BIT):
            return 64
        elif (read == PRBS_VERIFIER_DESERIALIZER_FACTOR_10BIT):
            return 10
        else:
            if (PRINT_VERBOSITY >= PRINT_VERBOSITY_WARN):
                print("WARN: get_prbs_ver_deser_factor: unknown PRBS verifier deserializer factor: " + str(hex(read)))
            return 0

    def set_prbs_ver_deser_factor(self, addr_off, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_ver_deser_factor")
        if type(val) is int:
            val = prbs_verifier_deserializer_factor_mapping[val]
        else:
            if (PRINT_VERBOSITY >= PRINT_VERBOSITY_ERROR):
                print("ERROR: set_prbs_ver_deser_factor: argument given is not an integer")
            exit(1)
        if ((val != PRBS_VERIFIER_DESERIALIZER_FACTOR_64BIT) and
                (val != PRBS_VERIFIER_DESERIALIZER_FACTOR_10BIT)):
            if (PRINT_VERBOSITY >= PRINT_VERBOSITY_ERROR):
                print("ERROR: set_prbs_ver_deser_factor: unsupported PRBS verifier deserializer factor: " + str(hex(val)))
            exit(1)
        self.masked_write((addr_off << 11) + 0x13F, 0x000F, val & 0x000F)

    # PRBS Soft Accumulators registers
    def get_prbs_soft_acc_prbs_counter_en(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_soft_acc_prbs_counter_en")
        return bool(self.masked_read((addr_off << 11) + 0x500, 0x0001))

    def set_prbs_soft_acc_prbs_counter_en(self, addr_off, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_soft_acc_prbs_counter_en")
        self.masked_write((addr_off << 11) + 0x500, 0x0001, 0x0001 if val else 0x0000)

    def get_prbs_soft_acc_prbs_reset(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_soft_acc_prbs_reset")
        return bool(self.masked_read((addr_off << 11) + 0x500, 0x0002))

    def set_prbs_soft_acc_prbs_reset(self, addr_off, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_soft_acc_prbs_reset")
        self.masked_write((addr_off << 11) + 0x500, 0x0002, 0x0002 if val else 0x0000)

    def get_prbs_soft_acc_prbs_snap(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_soft_acc_prbs_snap")
        return bool(self.masked_read((addr_off << 11) + 0x500, 0x0004))

    def set_prbs_soft_acc_prbs_snap(self, addr_off, val):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_soft_acc_prbs_snap")
        self.masked_write((addr_off << 11) + 0x500, 0x0004, 0x0004 if val else 0x0000)

    def get_prbs_soft_acc_prbs_done(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_soft_acc_prbs_done")
        return bool(self.masked_read((addr_off << 11) + 0x500, 0x0008))

    def get_prbs_soft_acc_prbs_acc_err_cnt(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_soft_acc_prbs_acc_err_cnt")
        val = 0
        move_iter = 0
        # accumulated error count under addresses 0x507 - 0x501
        for addr in range(0x501, 0x508):
            # use only two bits from the most significant byte
            if (addr == 0x507):
                mask = 0x0003
            else:
                mask = 0x00FF
            read = self.masked_read((addr_off << 11) + addr, mask)
            # move each byte (8 * byte indicator) bits to the right
            val += read << (move_iter * 8)
            move_iter += 1
        return val

    def get_prbs_soft_acc_prbs_acc_bit_cnt(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: get_prbs_soft_acc_prbs_acc_bit_cnt")
        val = 0
        move_iter = 0
        # accumulated bit count under addresses 0x513 - 0x50D
        for addr in range(0x50D, 0x514):
            # use only two bits from the most significant byte
            if (addr == 0x513):
                mask = 0x0003
            else:
                mask = 0x00FF
            read = self.masked_read((addr_off << 11) + addr, mask)
            # move each byte (8 * byte indicator) bits to the right
            val += read << (move_iter * 8)
            move_iter += 1
        return val

    # function sets transceiver PRBS components to do BER measurement according to Intel example found on
    # https://community.intel.com/t5/FPGA-Wiki/High-Speed-Transceiver-Demo-Designs-Stratix-10-GX-Series/ta-p/735749
    # and downloaded via link https://www.intel.com/content/dam/altera-www/global/en_US/uploads/1/1c/Stratix10GX_software_lib.zip
    # no guide references for these operations have ben found in L- and H-Tile Transceiver PHY User Guide 683621 | 2022.07.20
    def set_transceiver_prbs_components(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_transceiver_prbs_components")
        self.masked_write((addr_off << 11) + 0x164, 0x80, 0x80)
        self.masked_write((addr_off << 11) + 0x210, 0x1F, 0x09)
        self.masked_write((addr_off << 11) + 0x212, 0xE0, 0x00)
        self.masked_write((addr_off << 11) + 0x213, 0xFF, 0x47)
        self.masked_write((addr_off << 11) + 0x214, 0x01, 0x00)
        self.masked_write((addr_off << 11) + 0x215, 0x01, 0x00)
        self.masked_write((addr_off << 11) + 0x218, 0xC1, 0x40)
        self.masked_write((addr_off << 11) + 0x223, 0x1F, 0x00)
        self.masked_write((addr_off << 11) + 0x300, 0x3F, 0x00)
        self.masked_write((addr_off << 11) + 0x312, 0xFF, 0x07)
        self.masked_write((addr_off << 11) + 0x313, 0xFF, 0x02)
        self.masked_write((addr_off << 11) + 0x315, 0x47, 0x00)
        self.masked_write((addr_off << 11) + 0x318, 0x03, 0x02)
        self.masked_write((addr_off << 11) + 0x31A, 0x1C, 0x04)
        self.masked_write((addr_off << 11) + 0x320, 0x07, 0x02)
        self.masked_write((addr_off << 11) + 0x321, 0x1E, 0x18)
        self.masked_write((addr_off << 11) + 0x322, 0x73, 0x41)

    # function sets PRBS generator and PRBS verifier
    def set_prbs_gen_and_ver(self, addr_off, \
            prbs_pattern = "prbs31", \
            serializer_mode = 64, \
            deserializer_factor = 64):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_gen_and_ver")
        self.set_prbs_gen_prbs_pat(addr_off, prbs_pattern)
        self.set_prbs_ver_prbs_pat(addr_off, prbs_pattern)
        self.set_prbs_gen_ser_mode(addr_off, serializer_mode)
        self.masked_write((addr_off << 11) + 0x06, 0xCF, 0x44)
        self.masked_write((addr_off << 11) + 0x0B, 0x0E, 0x00)
        self.masked_write((addr_off << 11) + 0x0C, 0x0A, 0x00)
        self.set_prbs_ver_deser_factor(addr_off, serializer_mode)
        self.masked_write((addr_off << 11) + 0x0A, 0x80, 0x80)
        self.masked_write((addr_off << 11) + 0x500, 0x07, 0x01)

    def set_transceiver_bounded_channels_configuration(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_transceiver_bounded_channels_configuration")
        self.masked_write((addr_off << 11) + 0x0B, 0x02, 0x02)
        self.masked_write((addr_off << 11) + 0x0C, 0x02, 0x02)
        self.masked_write((addr_off << 11) + 0x10A, 0x01, 0x00)
        self.masked_write((addr_off << 11) + 0x10B, 0x01, 0x01)
        self.masked_write((addr_off << 11) + 0x111, 0x19, 0x18)
        self.masked_write((addr_off << 11) + 0x123, 0xC0, 0x80)
        self.masked_write((addr_off << 11) + 0x12A, 0x90, 0x90)

    # function sets PRBS accumulator
    def set_prbs_soft_accumulator(self, addr_off):
        if (PRINT_VERBOSITY >= PRINT_VERBOSITY_TRACE):
            print("TRACE: set_prbs_soft_accumulator")
        self.set_prbs_soft_acc_prbs_counter_en(addr_off, 1)
        self.set_prbs_soft_acc_prbs_reset(addr_off, 1)
        self.set_prbs_soft_acc_prbs_reset(addr_off, 0)
        self.set_prbs_soft_acc_prbs_snap(addr_off, 0)
        if (self.get_prbs_soft_acc_prbs_acc_err_cnt(addr_off)):
            if (PRINT_VERBOSITY >= PRINT_VERBOSITY_ERROR):
                print("ERROR: set_prbs_soft_accumulator: PRBS error counter has not been reseted")
            exit(1)
        if (self.get_prbs_soft_acc_prbs_acc_bit_cnt(addr_off)):
            if (PRINT_VERBOSITY >= PRINT_VERBOSITY_ERROR):
                print("ERROR: set_prbs_soft_accumulator: PRBS bit counter has not been reseted")
            exit(1)

node.register(LTileHTileNode, 0x9A83)

