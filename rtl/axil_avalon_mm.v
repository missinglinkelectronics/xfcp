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


Description: The AXI4-Lite to Avalon-MM bridge implementation.

Convert a single AXI4-Lite read/write transfer into Avalon-MM transfer
Avalon-MM specification taken from Intel Avalon Interface Specifications
version 683091 | 2022.01.24

Features not supported:
a) write/read burst
b) AXI4-Lite protection
c) Avalon-MM interface: 'lock' signal, pipelined read with
   fixed and with variable latency, other than default properties
*/

// Language: Verilog 2001

`timescale 1ns / 1ps

module axil_avalon_mm #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32,
    parameter STRB_WIDTH = (DATA_WIDTH/8),
    parameter BYTEENABLE_WIDTH = (DATA_WIDTH/8)
)
(
    input  wire                         clk,
    input  wire                         rst,

    /*
     * AXI lite slave interface
     */
    input  wire [ADDR_WIDTH-1:0]        s_axil_awaddr,
    input  wire [2:0]                   s_axil_awprot,
    input  wire                         s_axil_awvalid,
    output wire                         s_axil_awready,
    input  wire [DATA_WIDTH-1:0]        s_axil_wdata,
    input  wire [STRB_WIDTH-1:0]        s_axil_wstrb,
    input  wire                         s_axil_wvalid,
    output wire                         s_axil_wready,
    output wire [1:0]                   s_axil_bresp,
    output wire                         s_axil_bvalid,
    input  wire                         s_axil_bready,
    input  wire [ADDR_WIDTH-1:0]        s_axil_araddr,
    input  wire [2:0]                   s_axil_arprot,
    input  wire                         s_axil_arvalid,
    output wire                         s_axil_arready,
    output wire [DATA_WIDTH-1:0]        s_axil_rdata,
    output wire [1:0]                   s_axil_rresp,
    output wire                         s_axil_rvalid,
    input  wire                         s_axil_rready,

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

reg s_axil_awready_reg = 1'b0;
reg s_axil_wready_reg = 1'b0;
reg [1:0] s_axil_bresp_reg;
reg s_axil_bvalid_reg = 1'b0;
reg s_axil_arready_reg = 1'b0;
reg [DATA_WIDTH-1:0] s_axil_rdata_reg;
reg [1:0] s_axil_rresp_reg;
reg s_axil_rvalid_reg = 1'b0;

assign s_axil_awready = s_axil_awready_reg;
assign s_axil_wready = s_axil_wready_reg;
assign s_axil_bresp = s_axil_bresp_reg;
assign s_axil_bvalid = s_axil_bvalid_reg;
assign s_axil_arready = s_axil_arready_reg;
assign s_axil_rdata = s_axil_rdata_reg;
assign s_axil_rresp = s_axil_rresp_reg;
assign s_axil_rvalid = s_axil_rvalid_reg;

reg [ADDR_WIDTH-1:0] h_avalon_mm_address_reg = 0;
reg [BYTEENABLE_WIDTH-1:0] h_avalon_mm_byteenable_reg = 0;
reg h_avalon_mm_read_reg = 1'b0;
reg h_avalon_mm_write_reg = 1'b0;
reg [DATA_WIDTH-1:0] h_avalon_mm_writedata_reg = 0;

assign h_avalon_mm_address = h_avalon_mm_address_reg;
assign h_avalon_mm_byteenable = h_avalon_mm_byteenable_reg;
assign h_avalon_mm_read = h_avalon_mm_read_reg;
assign h_avalon_mm_write = h_avalon_mm_write_reg;
assign h_avalon_mm_writedata = h_avalon_mm_writedata_reg;

localparam [2:0]
    STATE_IDLE = 4'd0,
    STATE_START_AVALON_WRITE = 4'd1,
    STATE_START_AVALON_READ = 4'd2,
    STATE_CHECK_AVALON_WAITREQUEST = 4'd3,
    STATE_VALIDATE_AXI_BRESP = 4'd4,
    STATE_WAIT_AXI_BREADY = 4'd5,
    STATE_VALIDATE_AXI_RVALID = 4'd6,
    STATE_WAIT_AXI_RREADY = 4'd7;

reg [2:0] state_reg = STATE_IDLE;
reg [2:0] state_next;
reg rnw = 1'b0;
reg [ADDR_WIDTH-1:0] address;
reg [DATA_WIDTH-1:0] writedata;
reg [DATA_WIDTH-1:0] readdata;
reg [BYTEENABLE_WIDTH-1:0] byteenable;
reg [1:0] response;

always @(posedge clk) begin
    state_reg <= state_next;
    if (rst) begin
        state_reg <= STATE_IDLE;
    end
end

always @* begin
    state_next = state_reg;
    case (state_reg)
        STATE_IDLE: begin
            if (s_axil_awvalid && s_axil_awready &&
                    s_axil_wvalid && s_axil_wready)
            begin
                state_next = STATE_START_AVALON_WRITE;
            end else if (s_axil_arvalid && s_axil_arready) begin
                state_next = STATE_START_AVALON_READ;
            end
        end
        STATE_START_AVALON_WRITE,
        STATE_START_AVALON_READ: begin
            state_next = STATE_CHECK_AVALON_WAITREQUEST;
        end
        STATE_CHECK_AVALON_WAITREQUEST: begin
            if (!h_avalon_mm_waitrequest) begin
                if (rnw) begin
                    state_next = STATE_VALIDATE_AXI_RVALID;
                end else begin
                    state_next = STATE_VALIDATE_AXI_BRESP;
                end
            end
        end
        STATE_VALIDATE_AXI_BRESP: begin
            state_next = STATE_WAIT_AXI_BREADY;
        end
        STATE_WAIT_AXI_BREADY: begin
            if (s_axil_bready) begin
                state_next = STATE_IDLE;
            end
        end
        STATE_VALIDATE_AXI_RVALID: begin
            state_next = STATE_WAIT_AXI_RREADY;
        end
        STATE_WAIT_AXI_RREADY: begin
            if (s_axil_rready) begin
                state_next = STATE_IDLE;
            end
        end
        default: begin
            state_next = STATE_IDLE;
        end
    endcase
end

always @(posedge clk) begin
    s_axil_awready_reg <= 1'b0;
    s_axil_wready_reg <= 1'b0;
    s_axil_arready_reg <= 1'b0;

    case (state_reg)
        STATE_IDLE: begin
            if (s_axil_awvalid && !s_axil_awready &&
                    s_axil_wvalid && !s_axil_wready)
            begin
                s_axil_awready_reg <= 1'b1;
                s_axil_wready_reg <= 1'b1;
                address <= s_axil_awaddr;
                writedata <= s_axil_wdata;
                byteenable <= s_axil_wstrb;
            end else if (s_axil_arvalid && !s_axil_arready) begin
                s_axil_arready_reg <= 1'b1;
                address <= s_axil_araddr;
            end
        end
        STATE_START_AVALON_WRITE: begin
            h_avalon_mm_address_reg <= address;
            h_avalon_mm_byteenable_reg <= byteenable;
            h_avalon_mm_writedata_reg <= writedata;
            h_avalon_mm_write_reg <= 1'b1;
            rnw <= 1'b0;
        end
        STATE_START_AVALON_READ: begin
            h_avalon_mm_address_reg <= address;
            h_avalon_mm_byteenable_reg <= byteenable;
            h_avalon_mm_read_reg <= 1'b1;
            rnw <= 1'b1;
        end
        STATE_CHECK_AVALON_WAITREQUEST: begin
            if (!h_avalon_mm_waitrequest) begin
                h_avalon_mm_write_reg <= 1'b0;
                h_avalon_mm_read_reg <= 1'b0;
                // capture read data also in case of write transfer
                // it will not be used but makes will simplify logic
                readdata <= h_avalon_mm_readdata;
                // response encoding is the same for AXI4-Lite and Avalon-MM
                // according to specification Intel Avalon Interface
                // Specifications 683091 | 2022.01.24
                // chapter 3.2 Avalon Memory Mapped Interface Signal Roles
                response <= h_avalon_mm_response;
            end
        end
        STATE_VALIDATE_AXI_BRESP: begin
            s_axil_bresp_reg <= response;
            s_axil_bvalid_reg <= 1'b1;
        end
        STATE_WAIT_AXI_BREADY: begin
            if (s_axil_bready) begin
                s_axil_bvalid_reg <= 1'b0;
            end
        end
        STATE_VALIDATE_AXI_RVALID: begin
            s_axil_rdata_reg <= readdata;
            s_axil_rresp_reg <= response;
            s_axil_rvalid_reg <= 1'b1;
        end
        STATE_WAIT_AXI_RREADY: begin
            if (s_axil_rready) begin
                s_axil_rvalid_reg <= 1'b0;
            end
        end
        default: begin
            s_axil_bvalid_reg <= 1'b0;
            s_axil_rvalid_reg <= 1'b0;
            h_avalon_mm_write_reg <= 1'b0;
            h_avalon_mm_read_reg <= 1'b0;
        end
    endcase

    if (rst) begin
        s_axil_bvalid_reg <= 1'b0;
        s_axil_rvalid_reg <= 1'b0;
        h_avalon_mm_write_reg <= 1'b0;
        h_avalon_mm_read_reg <= 1'b0;
    end
end

endmodule

