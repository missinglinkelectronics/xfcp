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

DBG_PRINT = False

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

class LTileHTileNode(node.MemoryNode):
    # expected byte address
    def masked_read(self, addr, mask):
        # multiple byte address by 4 so it does not get
        # truncated because of 32 bit access of AXI4-Lite (converted to Avalon-MM)
        val = self.read_word(addr << 2) & mask
        if (DBG_PRINT):
            print("TRACE: masked_read: address: " + str(hex(addr)) + ", mask: " + str(hex(mask)) + ", data: " + str(hex(val)))
        return val

    # expected byte address
    def masked_write(self, addr, mask, val):
        if (DBG_PRINT):
            print("TRACE: masked_write: address: " + str(hex(addr)) + ", mask: " + str(hex(mask) + ", data: " + str(hex(val))))
        # multiple byte address by 4 so it does not get
        # truncated because of 32 bit access of AXI4-Lite (converted to Avalon-MM)
        return self.write_word(addr << 2, (self.read_word(addr << 2) & ~mask) | (val & mask))

    def dump_reg_space(self, start, stop):
        for addr in range(start, stop, 0x001):
            print("Address: " + str(hex(addr)) + ": " + str(hex(self.masked_read(addr, 0xFF))))

    # return True if the receiver is locked to data
    def get_rx_locked_to_data(self):
        if (DBG_PRINT):
            print("TRACE: get_rx_locked_to_data")
        return bool(self.masked_read(0x480, 0x0001))

    # return True if the receiver is locked to reference clock
    def get_rx_locked_to_ref(self):
        if (DBG_PRINT):
            print("TRACE: get_rx_locked_to_ref")
        return bool(self.masked_read(0x480, 0x0002))

    # steps to follow to view Eyescan may also apply to run BER measurement
    # presented in documentation L- and H-Tile Transceiver PHY User Guide 683621 | 2022.07.20
    # on pages 161 - 162
    def disable_background_calibration(self):
        if (DBG_PRINT):
            print("TRACE: disable_background_calibration")
        self.masked_write(0x542, 0x01, 0x00)

    def is_avmm_bus_busy(self):
        # return True if PreSICE has control of the internal configuration bus
        # return False if you have control of internal configuration bus
        if (DBG_PRINT):
            print("TRACE: is_avmm_bus_busy")
        return bool(self.masked_read(0x481, 0x04))

    def is_rx_adaption_mode_manual(self):
        # return True if RX adaptation is in manual mode, return False otherwise
        if (DBG_PRINT):
            print("TRACE: is_rx_adaption_mode_manual")
        return bool(self.masked_read(0x161, 0x20))

    def release_adaptation_from_reset(self):
        if (DBG_PRINT):
            print("TRACE: release_adaptation_from_reset")
        self.masked_write(0x148, 0x01, 0x01)

    def enable_cnt_to_detect_error_bits(self):
        if (DBG_PRINT):
            print("TRACE: enable_cnt_to_detect_error_bits")
        self.masked_write(0x169, 0x40, 0x01)

    def enable_serial_bit_checker(self):
        if (DBG_PRINT):
            print("TRACE: enable_serial_bit_checker")
        self.masked_write(0x168, 0x01, 0x01)

    def is_dfe_enabled(self):
        # return True if DFE is enabled, return False otherwise
        if (DBG_PRINT):
            print("TRACE: is_dfe_enabled")
        return True if (self.masked_read(0x161, 0x40) == 0) else False

    def enable_dfe_speculation(self):
        if (DBG_PRINT):
            print("TRACE: enable_dfe_speculation")
        self.masked_write(0x169, 0x04, 0x04)

    def disable_dfe_speculation(self):
        if (DBG_PRINT):
            print("TRACE: disable_dfe_speculation")
        self.masked_write(0x169, 0x04, 0x00)

    def enable_serial_bit_checker_control(self):
        if (DBG_PRINT):
            print("TRACE: enable_serial_bit_checker_control")
        self.masked_write(0x158, 0x20, 0x20)

    # PRBS Generator registers
    def get_prbs_gen_prbs_tx_pma_data_sel(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_gen_prbs_tx_pma_data_sel")
        # bits[4:3] from 0x008[6:5]
        msb = self.masked_read(0x008, 0b1100000) >> 5
        # bits[2:0] from 0x006[2:0]
        lsb = self.masked_read(0x006, 0b00111) >> 0
        val = (msb << 3) + lsb
        return val

    def set_prbs_gen_prbs_tx_pma_data_sel(self, val):
        if (DBG_PRINT):
            print("TRACE: set_prbs_gen_prbs_tx_pma_data_sel")
        # bits[4:3] to 0x008[6:5]
        self.masked_write(0x008, 0b1100000, (val & 0b11000) << 2)
        # bits[2:0] to 0x006[2:0]
        self.masked_write(0x006, 0b00111, val & 0b00111)

    def get_prbs_gen_prbs9_dwidth(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_gen_prbs9_dwidth")
        return bool(self.masked_read(0x006, 0x0008))

    def set_prbs_gen_prbs9_dwidth(self, val):
        if (DBG_PRINT):
            print("TRACE: set_prbs_gen_prbs9_dwidth")
        self.masked_write(0x006, 0x0008, 0x0008 if val else 0x0000)

    def get_prbs_gen_prbs_clken(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_gen_prbs_clken")
        return bool(self.masked_read(0x006, 0x0040))

    def set_prbs_gen_prbs_clken(self, val):
        if (DBG_PRINT):
            print("TRACE: set_prbs_gen_prbs_clken")
        self.masked_write(0x006, 0x0040, 0x0040 if val else 0x0000)

    def get_prbs_gen_prbs_pat(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_gen_prbs_pat")
        # bit[4] from 0x008[4]
        msb = self.masked_read(0x008, 0x0010)
        # bits[3:0] from 0x007[7:4]
        lsb = self.masked_read(0x007, 0x00F0) >> 4
        val = msb + lsb
        return val

    def set_prbs_gen_prbs_pat(self, val):
        if (DBG_PRINT):
            print("TRACE: set_prbs_gen_prbs_pat")
        if type(val) is str:
            val = prbs_mode_mapping[val]
        # bit[4] to 0x008[4]
        self.masked_write(0x008, 0x0010, val & 0x0010)
        # bits[3:0] to 0x007[7:4]
        self.masked_write(0x007, 0x00F0, (val & 0x000F) << 4)

    def get_prbs_gen_ser_mode(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_gen_ser_mode")
        return (self.masked_read(0x110, 0x0007))

    def set_prbs_gen_ser_mode(self, val):
        if (DBG_PRINT):
            print("TRACE: set_prbs_gen_ser_mode")
        self.masked_write(0x110, 0x0007, val & 0x0007)

    # PRBS Verifier registers
    def get_prbs_ver_prbs_clken(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_ver_prbs_clken")
        return bool(self.masked_read(0x00A, 0x0080))

    def set_prbs_ver_prbs_clken(self, val):
        if (DBG_PRINT):
            print("TRACE: set_prbs_ver_prbs_clken")
        self.masked_write(0x00A, 0x0080, 0x0080 if val else 0x0000)

    def get_prbs_ver_rx_prbs_mask(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_ver_rx_prbs_mask")
        return (self.masked_read(0x00B, 0x000C) >> 2)

    def set_prbs_ver_rx_prbs_mask(self, val):
        if (DBG_PRINT):
            print("TRACE: set_prbs_ver_rx_prbs_mask")
        self.masked_write(0x00B, 0x000C, val << 2)

    def get_prbs_ver_prbs_pat(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_ver_prbs_pat")
        # bit[4] from 0x00C[0]
        msb = self.masked_read(0x00C, 0x0001)
        # bits[3:0] from 0x00B[7:4]
        lsb = self.masked_read(0x00B, 0x00F0) >> 4
        val = (msb << 4) + lsb
        return val

    def set_prbs_ver_prbs_pat(self, val):
        if (DBG_PRINT):
            print("TRACE: set_prbs_ver_prbs_pat")
        if type(val) is str:
            val = prbs_mode_mapping[val]
        # bit[4] to 0x00C[0]
        self.masked_write(0x00C, 0x0001, (val & 0x0010) >> 4)
        # bits[3:0] to 0x00B[7:4]
        self.masked_write(0x00B, 0x00F0, (val & 0x000F) << 4)

    def get_prbs_ver_prbs9_dwidth(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_ver_prbs9_dwidth")
        return bool(self.masked_read(0x00C, 0x0008))

    def set_prbs_ver_prbs9_dwidth(self, val):
        if (DBG_PRINT):
            print("TRACE: set_prbs_ver_prbs9_dwidth")
        self.masked_write(0x00C, 0x0008, 0x0008 if val else 0x0000)

    def get_prbs_ver_deser_factor(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_ver_deser_factor")
        return (self.masked_read(0x13F, 0x000F))

    def set_prbs_ver_deser_factor(self, val):
        if (DBG_PRINT):
            print("TRACE: set_prbs_ver_deser_factor")
        self.masked_write(0x13F, 0x000F, val & 0x000F)

    # PRBS Soft Accumulators registers
    def get_prbs_soft_acc_prbs_counter_en(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_soft_acc_prbs_counter_en")
        return bool(self.masked_read(0x500, 0x0001))

    def set_prbs_soft_acc_prbs_counter_en(self, val):
        if (DBG_PRINT):
            print("TRACE: set_prbs_soft_acc_prbs_counter_en")
        self.masked_write(0x500, 0x0001, 0x0001 if val else 0x0000)

    def get_prbs_soft_acc_prbs_reset(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_soft_acc_prbs_reset")
        return bool(self.masked_read(0x500, 0x0002))

    def set_prbs_soft_acc_prbs_reset(self, val):
        if (DBG_PRINT):
            print("TRACE: set_prbs_soft_acc_prbs_reset")
        self.masked_write(0x500, 0x0002, 0x0002 if val else 0x0000)

    def get_prbs_soft_acc_prbs_snap(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_soft_acc_prbs_snap")
        return bool(self.masked_read(0x500, 0x0004))

    def set_prbs_soft_acc_prbs_snap(self, val):
        if (DBG_PRINT):
            print("TRACE: set_prbs_soft_acc_prbs_snap")
        self.masked_write(0x500, 0x0004, 0x0004 if val else 0x0000)

    def get_prbs_soft_acc_prbs_done(self):
        if (DBG_PRINT):
            print("TRACE: get_prbs_soft_acc_prbs_done")
        return bool(self.masked_read(0x500, 0x0008))

    def get_prbs_soft_acc_prbs_acc_err_cnt(self):
        if (DBG_PRINT):
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
            read = self.masked_read(addr, mask)
            # move each byte (8 * byte indicator) bits to the right
            val += read << (move_iter * 8)
            move_iter += 1
        return val

    def get_prbs_soft_acc_prbs_acc_bit_cnt(self):
        if (DBG_PRINT):
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
            read = self.masked_read(addr, mask)
            # move each byte (8 * byte indicator) bits to the right
            val += read << (move_iter * 8)
            move_iter += 1
        return val

node.register(LTileHTileNode, 0x9A83)

