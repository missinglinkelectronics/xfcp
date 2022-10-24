/*

Copyright (c) 2022 Missing Link Electronics, Inc.

Author: Karol Budniak

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

Description: The XFCP Avalon-MM wrapper with XFCP to AXI4-Lite converter
AXI4-Lite to Avalon-MM converter and Avalon-MM address converter instances

*/

// Language: Verilog 2001

`timescale 1ns / 1ps

module xfcp_mod_avmm #
(
    parameter XFCP_ID_TYPE = 16'h0001,
    parameter XFCP_ID_STR = "AXIL Master",
    /*
     * The only one tested use case is ADDR_WIDTH = 32
     * not all widths are supported neither have not been
     * tested however may work as well
     */
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32,
    parameter STRB_WIDTH = (DATA_WIDTH/8),
    parameter BYTEENABLE_WIDTH = (DATA_WIDTH/8),
    parameter USE_ADDR_CONVERTER = 0
)
(
    input  wire                         clk,
    input  wire                         rst,

    /*
     * XFCP upstream interface
     */
    input  wire [7:0]                   up_xfcp_in_tdata,
    input  wire                         up_xfcp_in_tvalid,
    output wire                         up_xfcp_in_tready,
    input  wire                         up_xfcp_in_tlast,
    input  wire                         up_xfcp_in_tuser,

    output wire [7:0]                   up_xfcp_out_tdata,
    output wire                         up_xfcp_out_tvalid,
    input  wire                         up_xfcp_out_tready,
    output wire                         up_xfcp_out_tlast,
    output wire                         up_xfcp_out_tuser,

    /*
     * Avalon MM host interface
     */
    output wire [ADDR_WIDTH-1:0]        h_avalon_mm_address,
    output wire [BYTEENABLE_WIDTH-1:0]  h_avalon_mm_byteenable,
    output wire                         h_avalon_mm_read,
    input  wire [DATA_WIDTH-1:0]        h_avalon_mm_readdata,
    input  wire [1:0]                   h_avalon_mm_response,
    output wire                         h_avalon_mm_write,
    output wire [DATA_WIDTH-1:0]        h_avalon_mm_writedata,
    input  wire                         h_avalon_mm_waitrequest
);

/*
 * AXI4-Lite internal interface
 */
wire [ADDR_WIDTH-1:0] axil_awaddr;
wire [2:0] axil_awprot;
wire axil_awvalid;
wire axil_awready;
wire [DATA_WIDTH-1:0] axil_wdata;
wire [STRB_WIDTH-1:0] axil_wstrb;
wire axil_wvalid;
wire axil_wready;
wire [1:0] axil_bresp;
wire axil_bvalid;
wire axil_bready;
wire [ADDR_WIDTH-1:0] axil_araddr;
wire [2:0] axil_arprot;
wire axil_arvalid;
wire axil_arready;
wire [DATA_WIDTH-1:0] axil_rdata;
wire [1:0] axil_rresp;
wire axil_rvalid;
wire axil_rready;


/*
 * Avalon MM internal interface
 */
wire [ADDR_WIDTH-1:0] avalon_mm_address;
wire [BYTEENABLE_WIDTH-1:0] avalon_mm_byteenable;
wire avalon_mm_read;
wire [DATA_WIDTH-1:0] avalon_mm_readdata;
wire [1:0] avalon_mm_response;
wire avalon_mm_write;
wire [DATA_WIDTH-1:0] avalon_mm_writedata;
wire avalon_mm_waitrequest;

xfcp_mod_axil #(
    .XFCP_ID_TYPE(XFCP_ID_TYPE),
    .XFCP_ID_STR(XFCP_ID_STR),
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH)
)
xfcp_mod_axil_inst (
    .clk(clk),
    .rst(rst),
    .up_xfcp_in_tdata(up_xfcp_in_tdata),
    .up_xfcp_in_tvalid(up_xfcp_in_tvalid),
    .up_xfcp_in_tready(up_xfcp_in_tready),
    .up_xfcp_in_tlast(up_xfcp_in_tlast),
    .up_xfcp_in_tuser(up_xfcp_in_tuser),
    .up_xfcp_out_tdata(up_xfcp_out_tdata),
    .up_xfcp_out_tvalid(up_xfcp_out_tvalid),
    .up_xfcp_out_tready(up_xfcp_out_tready),
    .up_xfcp_out_tlast(up_xfcp_out_tlast),
    .up_xfcp_out_tuser(up_xfcp_out_tuser),
    .m_axil_awaddr(axil_awaddr),
    .m_axil_awprot(axil_awprot),
    .m_axil_awvalid(axil_awvalid),
    .m_axil_awready(axil_awready),
    .m_axil_wdata(axil_wdata),
    .m_axil_wstrb(axil_wstrb),
    .m_axil_wvalid(axil_wvalid),
    .m_axil_wready(axil_wready),
    .m_axil_bresp(axil_bresp),
    .m_axil_bvalid(axil_bvalid),
    .m_axil_bready(axil_bready),
    .m_axil_araddr(axil_araddr),
    .m_axil_arprot(axil_arprot),
    .m_axil_arvalid(axil_arvalid),
    .m_axil_arready(axil_arready),
    .m_axil_rdata(axil_rdata),
    .m_axil_rresp(axil_rresp),
    .m_axil_rvalid(axil_rvalid),
    .m_axil_rready(axil_rready)
);


axil_avalon_mm #(
    .ADDR_WIDTH(ADDR_WIDTH),
    .DATA_WIDTH(DATA_WIDTH)
)
axil_avalon_mm_inst (
    .clk(clk),
    .rst(rst),

    .s_axil_awaddr(axil_awaddr),
    .s_axil_awprot(axil_awprot),
    .s_axil_awvalid(axil_awvalid),
    .s_axil_awready(axil_awready),
    .s_axil_wdata(axil_wdata),
    .s_axil_wstrb(axil_wstrb),
    .s_axil_wvalid(axil_wvalid),
    .s_axil_wready(axil_wready),
    .s_axil_bresp(axil_bresp),
    .s_axil_bvalid(axil_bvalid),
    .s_axil_bready(axil_bready),
    .s_axil_araddr(axil_araddr),
    .s_axil_arprot(axil_arprot),
    .s_axil_arvalid(axil_arvalid),
    .s_axil_arready(axil_arready),
    .s_axil_rdata(axil_rdata),
    .s_axil_rresp(axil_rresp),
    .s_axil_rvalid(axil_rvalid),
    .s_axil_rready(axil_rready),


    .h_avalon_mm_address(avalon_mm_address),
    .h_avalon_mm_byteenable(avalon_mm_byteenable),
    .h_avalon_mm_read(avalon_mm_read),
    .h_avalon_mm_readdata(avalon_mm_readdata),
    .h_avalon_mm_response(avalon_mm_response),
    .h_avalon_mm_write(avalon_mm_write),
    .h_avalon_mm_writedata(avalon_mm_writedata),
    .h_avalon_mm_waitrequest(avalon_mm_waitrequest)
);

generate
if (USE_ADDR_CONVERTER) begin

    avalon_mm_addr_conv #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    )
    avalon_mm_addr_conv_inst (
        .avalon_mm_in_address(avalon_mm_address),
        .avalon_mm_in_byteenable(avalon_mm_byteenable),
        .avalon_mm_in_read(avalon_mm_read),
        .avalon_mm_in_readdata(avalon_mm_readdata),
        .avalon_mm_in_response(avalon_mm_response),
        .avalon_mm_in_write(avalon_mm_write),
        .avalon_mm_in_writedata(avalon_mm_writedata),
        .avalon_mm_in_waitrequest(avalon_mm_waitrequest),
    
        .avalon_mm_out_address(h_avalon_mm_address),
        .avalon_mm_out_byteenable(h_avalon_mm_byteenable),
        .avalon_mm_out_read(h_avalon_mm_read),
        .avalon_mm_out_readdata(h_avalon_mm_readdata),
        .avalon_mm_out_response(h_avalon_mm_response),
        .avalon_mm_out_write(h_avalon_mm_write),
        .avalon_mm_out_writedata(h_avalon_mm_writedata),
        .avalon_mm_out_waitrequest(h_avalon_mm_waitrequest)
    );
end else begin

    assign h_avalon_mm_address = avalon_mm_address;
    assign h_avalon_mm_byteenable = avalon_mm_byteenable;
    assign h_avalon_mm_read = avalon_mm_read;
    assign avalon_mm_readdata = h_avalon_mm_readdata;
    assign avalon_mm_response = h_avalon_mm_response;
    assign h_avalon_mm_write = avalon_mm_write;
    assign h_avalon_mm_writedata = avalon_mm_writedata;
    assign avalon_mm_waitrequest = h_avalon_mm_waitrequest;
end

endgenerate

endmodule
