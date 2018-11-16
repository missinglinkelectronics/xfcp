#!/usr/bin/env python
"""

Copyright (c) 2017 Alex Forencich

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

from myhdl import *
import os
import struct

import xfcp
import uart_ep
import eth_ep
import arp_ep
import udp_ep
import gmii_ep

module = 'fpga_core'
testbench = 'test_%s' % module

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("../lib/xfcp/rtl/xfcp_interface_uart.v")
srcs.append("../lib/xfcp/rtl/xfcp_interface_udp.v")
srcs.append("../lib/xfcp/rtl/xfcp_mod_wb.v")
srcs.append("../lib/xfcp/rtl/xfcp_switch_1x4.v")
srcs.append("../lib/xfcp/rtl/xfcp_switch_2x1.v")
srcs.append("../lib/eth/rtl/iddr.v")
srcs.append("../lib/eth/rtl/oddr.v")
srcs.append("../lib/eth/rtl/ssio_sdr_in.v")
srcs.append("../lib/eth/rtl/ssio_sdr_out.v")
srcs.append("../lib/eth/rtl/gmii_phy_if.v")
srcs.append("../lib/eth/rtl/eth_mac_1g_gmii_fifo.v")
srcs.append("../lib/eth/rtl/eth_mac_1g_gmii.v")
srcs.append("../lib/eth/rtl/eth_mac_1g.v")
srcs.append("../lib/eth/rtl/axis_gmii_rx.v")
srcs.append("../lib/eth/rtl/axis_gmii_tx.v")
srcs.append("../lib/eth/rtl/lfsr.v")
srcs.append("../lib/eth/rtl/eth_axis_rx.v")
srcs.append("../lib/eth/rtl/eth_axis_tx.v")
srcs.append("../lib/eth/rtl/udp_complete.v")
srcs.append("../lib/eth/rtl/udp_checksum_gen.v")
srcs.append("../lib/eth/rtl/udp.v")
srcs.append("../lib/eth/rtl/udp_ip_rx.v")
srcs.append("../lib/eth/rtl/udp_ip_tx.v")
srcs.append("../lib/eth/rtl/ip_complete.v")
srcs.append("../lib/eth/rtl/ip.v")
srcs.append("../lib/eth/rtl/ip_eth_rx.v")
srcs.append("../lib/eth/rtl/ip_eth_tx.v")
srcs.append("../lib/eth/rtl/ip_arb_mux.v")
srcs.append("../lib/eth/rtl/arp.v")
srcs.append("../lib/eth/rtl/arp_cache.v")
srcs.append("../lib/eth/rtl/arp_eth_rx.v")
srcs.append("../lib/eth/rtl/arp_eth_tx.v")
srcs.append("../lib/eth/rtl/eth_arb_mux.v")
srcs.append("../lib/uart/rtl/uart.v")
srcs.append("../lib/uart/rtl/uart_rx.v")
srcs.append("../lib/uart/rtl/uart_tx.v")
srcs.append("../lib/wb/rtl/wb_ram.v")
srcs.append("../lib/axis/rtl/arbiter.v")
srcs.append("../lib/axis/rtl/priority_encoder.v")
srcs.append("../lib/axis/rtl/axis_cobs_encode.v")
srcs.append("../lib/axis/rtl/axis_cobs_decode.v")
srcs.append("../lib/axis/rtl/axis_fifo.v")
srcs.append("../lib/axis/rtl/axis_async_fifo.v")
srcs.append("%s.v" % testbench)

src = ' '.join(srcs)

build_cmd = "iverilog -o %s.vvp %s" % (testbench, src)

def bench():

    # Parameters
    TARGET = "SIM"

    # Inputs
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    btnu = Signal(bool(0))
    btnl = Signal(bool(0))
    btnd = Signal(bool(0))
    btnr = Signal(bool(0))
    btnc = Signal(bool(0))
    sw = Signal(intbv(0)[8:])
    phy_rx_clk = Signal(bool(0))
    phy_rxd = Signal(intbv(0)[8:])
    phy_rx_dv = Signal(bool(0))
    phy_rx_er = Signal(bool(0))
    phy_tx_clk = Signal(bool(0))
    uart_rxd = Signal(bool(1))

    # Outputs
    led = Signal(intbv(0)[8:])
    phy_gtx_clk = Signal(bool(0))
    phy_txd = Signal(intbv(0)[8:])
    phy_tx_en = Signal(bool(0))
    phy_tx_er = Signal(bool(0))
    phy_reset_n = Signal(bool(0))
    uart_txd = Signal(bool(1))

    # sources and sinks
    mii_select = Signal(bool(0))

    gmii_source = gmii_ep.GMIISource()

    gmii_source_logic = gmii_source.create_logic(
        phy_rx_clk,
        rst,
        txd=phy_rxd,
        tx_en=phy_rx_dv,
        tx_er=phy_rx_er,
        mii_select=mii_select,
        name='gmii_source'
    )

    gmii_sink = gmii_ep.GMIISink()

    gmii_sink_logic = gmii_sink.create_logic(
        phy_tx_clk,
        rst,
        rxd=phy_txd,
        rx_dv=phy_tx_en,
        rx_er=phy_tx_er,
        mii_select=mii_select,
        name='gmii_sink'
    )

    uart_source = uart_ep.UARTSource()

    uart_source_logic = uart_source.create_logic(
        clk,
        rst,
        txd=uart_rxd,
        prescale=int(125000000/(115200*8)),
        name='uart_source'
    )

    uart_sink = uart_ep.UARTSink()

    uart_sink_logic = uart_sink.create_logic(
        clk,
        rst,
        rxd=uart_txd,
        prescale=int(125000000/(115200*8)),
        name='uart_sink'
    )

    # DUT
    if os.system(build_cmd):
        raise Exception("Error running build command")

    dut = Cosimulation(
        "vvp -m myhdl %s.vvp -lxt2" % testbench,
        clk=clk,
        rst=rst,
        current_test=current_test,

        btnu=btnu,
        btnl=btnl,
        btnd=btnd,
        btnr=btnr,
        btnc=btnc,
        sw=sw,
        led=led,

        phy_rx_clk=phy_rx_clk,
        phy_rxd=phy_rxd,
        phy_rx_dv=phy_rx_dv,
        phy_rx_er=phy_rx_er,
        phy_gtx_clk=phy_gtx_clk,
        phy_tx_clk=phy_tx_clk,
        phy_txd=phy_txd,
        phy_tx_en=phy_tx_en,
        phy_tx_er=phy_tx_er,
        phy_reset_n=phy_reset_n,

        uart_rxd=uart_rxd,
        uart_txd=uart_txd
    )

    @always(delay(4))
    def clkgen():
        clk.next = not clk

    rx_clk_hp = Signal(int(4))

    @instance
    def rx_clk_gen():
        while True:
            yield delay(int(rx_clk_hp))
            phy_rx_clk.next = not phy_rx_clk
            phy_tx_clk.next = not phy_tx_clk

    @instance
    def check():
        yield delay(100)
        yield clk.posedge
        rst.next = 1
        yield clk.posedge
        rst.next = 0
        yield clk.posedge
        yield delay(100)
        yield clk.posedge

        # testbench stimulus

        yield clk.posedge
        print("test 1: enumerate via UDP")
        current_test.next = 1

        pkt = xfcp.XFCPFrame()
        pkt.path = []
        pkt.rpath = []
        pkt.ptype = 0xfe
        pkt.payload = b''

        test_frame = udp_ep.UDPFrame()
        test_frame.eth_dest_mac = 0x020000000000
        test_frame.eth_src_mac = 0xDAD1D2D3D4D5
        test_frame.eth_type = 0x0800
        test_frame.ip_version = 4
        test_frame.ip_ihl = 5
        test_frame.ip_dscp = 0
        test_frame.ip_ecn = 0
        test_frame.ip_length = None
        test_frame.ip_identification = 0
        test_frame.ip_flags = 2
        test_frame.ip_fragment_offset = 0
        test_frame.ip_ttl = 64
        test_frame.ip_protocol = 0x11
        test_frame.ip_header_checksum = None
        test_frame.ip_source_ip = 0xc0a80181
        test_frame.ip_dest_ip = 0xc0a80180
        test_frame.udp_source_port = 1234
        test_frame.udp_dest_port = 14000
        test_frame.payload = pkt.build_axis()
        test_frame.build()

        gmii_source.send(b'\x55\x55\x55\x55\x55\x55\x55\xD5'+test_frame.build_eth().build_axis_fcs().data)

        # wait for ARP request packet
        rx_frame = None
        while rx_frame is None:
            yield clk.posedge
            rx_frame = gmii_sink.recv()

        check_eth_frame = eth_ep.EthFrame()
        check_eth_frame.parse_axis_fcs(rx_frame.data[8:])
        check_frame = arp_ep.ARPFrame()
        check_frame.parse_eth(check_eth_frame)

        print(check_frame)

        assert check_frame.eth_dest_mac == 0xFFFFFFFFFFFF
        assert check_frame.eth_src_mac == 0x020000000000
        assert check_frame.eth_type == 0x0806
        assert check_frame.arp_htype == 0x0001
        assert check_frame.arp_ptype == 0x0800
        assert check_frame.arp_hlen == 6
        assert check_frame.arp_plen == 4
        assert check_frame.arp_oper == 1
        assert check_frame.arp_sha == 0x020000000000
        assert check_frame.arp_spa == 0xc0a80180
        assert check_frame.arp_tha == 0x000000000000
        assert check_frame.arp_tpa == 0xc0a80181

        # generate response
        arp_frame = arp_ep.ARPFrame()
        arp_frame.eth_dest_mac = 0x020000000000
        arp_frame.eth_src_mac = 0xDAD1D2D3D4D5
        arp_frame.eth_type = 0x0806
        arp_frame.arp_htype = 0x0001
        arp_frame.arp_ptype = 0x0800
        arp_frame.arp_hlen = 6
        arp_frame.arp_plen = 4
        arp_frame.arp_oper = 2
        arp_frame.arp_sha = 0xDAD1D2D3D4D5
        arp_frame.arp_spa = 0xc0a80181
        arp_frame.arp_tha = 0x020000000000
        arp_frame.arp_tpa = 0xc0a80180

        gmii_source.send(b'\x55\x55\x55\x55\x55\x55\x55\xD5'+arp_frame.build_eth().build_axis_fcs().data)

        rx_frame = None
        while rx_frame is None:
            yield clk.posedge
            rx_frame = gmii_sink.recv()

        check_eth_frame = eth_ep.EthFrame()
        check_eth_frame.parse_axis_fcs(rx_frame.data[8:])
        check_frame = udp_ep.UDPFrame()
        check_frame.parse_eth(check_eth_frame)

        print(check_frame)

        assert check_frame.eth_dest_mac == 0xDAD1D2D3D4D5
        assert check_frame.eth_src_mac == 0x020000000000
        assert check_frame.eth_type == 0x0800
        assert check_frame.ip_version == 4
        assert check_frame.ip_ihl == 5
        assert check_frame.ip_dscp == 0
        assert check_frame.ip_ecn == 0
        assert check_frame.ip_identification == 0
        assert check_frame.ip_flags == 2
        assert check_frame.ip_fragment_offset == 0
        assert check_frame.ip_ttl == 64
        assert check_frame.ip_protocol == 0x11
        assert check_frame.ip_source_ip == 0xc0a80180
        assert check_frame.ip_dest_ip == 0xc0a80181
        assert check_frame.udp_source_port == 14000
        assert check_frame.udp_dest_port == 1234

        rx_pkt = xfcp.XFCPFrame()
        rx_pkt.parse_axis(check_frame.payload.data)

        print(rx_pkt)

        assert rx_pkt.ptype == 0xff
        assert rx_pkt.path == []
        assert rx_pkt.rpath == []
        assert len(rx_pkt.payload.data) == 64

        pkt = xfcp.XFCPFrame()
        pkt.path = [0]
        pkt.rpath = []
        pkt.ptype = 0xfe
        pkt.payload = b''

        test_frame = udp_ep.UDPFrame()
        test_frame.eth_dest_mac = 0x020000000000
        test_frame.eth_src_mac = 0xDAD1D2D3D4D5
        test_frame.eth_type = 0x0800
        test_frame.ip_version = 4
        test_frame.ip_ihl = 5
        test_frame.ip_dscp = 0
        test_frame.ip_ecn = 0
        test_frame.ip_length = None
        test_frame.ip_identification = 0
        test_frame.ip_flags = 2
        test_frame.ip_fragment_offset = 0
        test_frame.ip_ttl = 64
        test_frame.ip_protocol = 0x11
        test_frame.ip_header_checksum = None
        test_frame.ip_source_ip = 0xc0a80181
        test_frame.ip_dest_ip = 0xc0a80180
        test_frame.udp_source_port = 1234
        test_frame.udp_dest_port = 14000
        test_frame.payload = pkt.build_axis()
        test_frame.build()

        gmii_source.send(b'\x55\x55\x55\x55\x55\x55\x55\xD5'+test_frame.build_eth().build_axis_fcs().data)

        rx_frame = None
        while rx_frame is None:
            yield clk.posedge
            rx_frame = gmii_sink.recv()

        check_eth_frame = eth_ep.EthFrame()
        check_eth_frame.parse_axis_fcs(rx_frame.data[8:])
        check_frame = udp_ep.UDPFrame()
        check_frame.parse_eth(check_eth_frame)

        print(check_frame)

        assert check_frame.eth_dest_mac == 0xDAD1D2D3D4D5
        assert check_frame.eth_src_mac == 0x020000000000
        assert check_frame.eth_type == 0x0800
        assert check_frame.ip_version == 4
        assert check_frame.ip_ihl == 5
        assert check_frame.ip_dscp == 0
        assert check_frame.ip_ecn == 0
        assert check_frame.ip_identification == 0
        assert check_frame.ip_flags == 2
        assert check_frame.ip_fragment_offset == 0
        assert check_frame.ip_ttl == 64
        assert check_frame.ip_protocol == 0x11
        assert check_frame.ip_source_ip == 0xc0a80180
        assert check_frame.ip_dest_ip == 0xc0a80181
        assert check_frame.udp_source_port == 14000
        assert check_frame.udp_dest_port == 1234

        rx_pkt = xfcp.XFCPFrame()
        rx_pkt.parse_axis(check_frame.payload.data)

        print(rx_pkt)

        assert rx_pkt.ptype == 0xff
        assert rx_pkt.path == [0]
        assert rx_pkt.rpath == []
        assert len(rx_pkt.payload.data) == 32

        assert gmii_source.empty()
        assert gmii_sink.empty()

        yield delay(100)

        yield clk.posedge
        print("test 1: test write and read RAM 0")
        current_test.next = 1

        pkt1 = xfcp.XFCPFrame()
        pkt1.path = [0]
        pkt1.ptype = 0x12
        pkt1.payload = bytearray(struct.pack('<BH', 0, 4)+b'\x11\x22\x33\x44')

        pkt2 = xfcp.XFCPFrame()
        pkt2.path = [0]
        pkt2.ptype = 0x10
        pkt2.payload = bytearray(struct.pack('<BH', 0, 4))

        test_frame1 = udp_ep.UDPFrame()
        test_frame1.eth_dest_mac = 0x020000000000
        test_frame1.eth_src_mac = 0xDAD1D2D3D4D5
        test_frame1.eth_type = 0x0800
        test_frame1.ip_version = 4
        test_frame1.ip_ihl = 5
        test_frame1.ip_dscp = 0
        test_frame1.ip_ecn = 0
        test_frame1.ip_length = None
        test_frame1.ip_identification = 0
        test_frame1.ip_flags = 2
        test_frame1.ip_fragment_offset = 0
        test_frame1.ip_ttl = 64
        test_frame1.ip_protocol = 0x11
        test_frame1.ip_header_checksum = None
        test_frame1.ip_source_ip = 0xc0a80181
        test_frame1.ip_dest_ip = 0xc0a80180
        test_frame1.udp_source_port = 1234
        test_frame1.udp_dest_port = 14000
        test_frame1.payload = pkt1.build_axis()
        test_frame1.build()

        test_frame2 = udp_ep.UDPFrame(test_frame1)
        test_frame2.payload = pkt2.build_axis()
        test_frame2.build()

        gmii_source.send(b'\x55\x55\x55\x55\x55\x55\x55\xD5'+test_frame1.build_eth().build_axis_fcs().data)
        gmii_source.send(b'\x55\x55\x55\x55\x55\x55\x55\xD5'+test_frame2.build_eth().build_axis_fcs().data)

        rx_frame = None
        while rx_frame is None:
            yield clk.posedge
            rx_frame = gmii_sink.recv()

        check_eth_frame = eth_ep.EthFrame()
        check_eth_frame.parse_axis_fcs(rx_frame.data[8:])
        check_frame = udp_ep.UDPFrame()
        check_frame.parse_eth(check_eth_frame)

        print(check_frame)

        rx_pkt = xfcp.XFCPFrame()
        rx_pkt.parse_axis(check_frame.payload.data)

        print(rx_pkt)
        assert rx_pkt.ptype == 0x13
        assert rx_pkt.payload.data == struct.pack('<BH', 0, 4)

        rx_frame = None
        while rx_frame is None:
            yield clk.posedge
            rx_frame = gmii_sink.recv()

        check_eth_frame = eth_ep.EthFrame()
        check_eth_frame.parse_axis_fcs(rx_frame.data[8:])
        check_frame = udp_ep.UDPFrame()
        check_frame.parse_eth(check_eth_frame)

        print(check_frame)

        rx_pkt = xfcp.XFCPFrame()
        rx_pkt.parse_axis(check_frame.payload.data)

        print(rx_pkt)
        assert rx_pkt.ptype == 0x11
        assert rx_pkt.payload.data == struct.pack('<BH', 0, 4)+b'\x11\x22\x33\x44'

        assert gmii_source.empty()
        assert gmii_sink.empty()

        yield delay(100)

        yield clk.posedge
        print("test 3: enumerate via UART")
        current_test.next = 3

        pkt = xfcp.XFCPFrame()
        pkt.path = []
        pkt.rpath = []
        pkt.ptype = 0xfe
        pkt.payload = b''

        uart_source.write(pkt.build_axis_cobs().data+b'\x00')

        yield clk.posedge

        rx_data = b''
        while True:
            if not uart_sink.empty():
                b = bytearray(uart_sink.read(1))
                rx_data += b
                if b[0] == 0:
                    break
            yield clk.posedge

        rx_pkt = xfcp.XFCPFrame()
        rx_pkt.parse_axis_cobs(rx_data[:-1])

        print(rx_pkt)

        assert rx_pkt.ptype == 0xff
        assert rx_pkt.path == []
        assert rx_pkt.rpath == []
        assert len(rx_pkt.payload.data) == 64

        pkt = xfcp.XFCPFrame()
        pkt.path = [0]
        pkt.rpath = []
        pkt.ptype = 0xfe
        pkt.payload = b''

        uart_source.write(pkt.build_axis_cobs().data+b'\x00')

        yield clk.posedge

        rx_data = b''
        while True:
            if not uart_sink.empty():
                b = bytearray(uart_sink.read(1))
                rx_data += b
                if b[0] == 0:
                    break
            yield clk.posedge

        rx_pkt = xfcp.XFCPFrame()
        rx_pkt.parse_axis_cobs(rx_data[:-1])

        print(rx_pkt)

        assert rx_pkt.ptype == 0xff
        assert rx_pkt.path == [0]
        assert rx_pkt.rpath == []
        assert len(rx_pkt.payload.data) == 32

        yield delay(100)

        raise StopSimulation

    return instances()

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()
