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

Description: This module implements a conversion from (double-word aligned)
Byte-Addressing (the two LSBs are always zero) to Word-Addressing by removing
the two LSBs and optionally expanding the MSBs with zero, if required to
satisfy the requested target address width.

*/

// Language: Verilog 2001

`timescale 1ns / 1ps

module avalon_mm_addr_conv #(
    /*
     * The only one tested use case is ADDR_WIDTH = 32
     * not all widths are supported neither have not been
     * tested however may work as well
     */
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32,
    parameter BYTEENABLE_WIDTH = (DATA_WIDTH/8)
)
(
    /*
     * Avalon MM in interface
     */
    input  wire [ADDR_WIDTH-1:0]        avalon_mm_in_address,
    input  wire [BYTEENABLE_WIDTH-1:0]  avalon_mm_in_byteenable,
    input  wire                         avalon_mm_in_read,
    output wire [DATA_WIDTH-1:0]        avalon_mm_in_readdata,
    output wire [1:0]                   avalon_mm_in_response,
    input  wire                         avalon_mm_in_write,
    input  wire [DATA_WIDTH-1:0]        avalon_mm_in_writedata,
    output wire                         avalon_mm_in_waitrequest,

    /*
     * Avalon MM out interface
     */
    output wire [ADDR_WIDTH-1:0]        avalon_mm_out_address,
    output wire [BYTEENABLE_WIDTH-1:0]  avalon_mm_out_byteenable,
    output wire                         avalon_mm_out_read,
    input  wire [DATA_WIDTH-1:0]        avalon_mm_out_readdata,
    input  wire [1:0]                   avalon_mm_out_response,
    output wire                         avalon_mm_out_write,
    output wire [DATA_WIDTH-1:0]        avalon_mm_out_writedata,
    input  wire                         avalon_mm_out_waitrequest
);

// bus width assertions
initial begin
    if (ADDR_WIDTH < 4) begin
        $error("Error: Avalon-MM address width smaller than 4, this is not supported");
        $finish;
    end
end

/*
 * double word address becomes byte address
 */
assign avalon_mm_out_address = {2'b00, avalon_mm_in_address[ADDR_WIDTH-1:2]};
assign avalon_mm_out_byteenable = avalon_mm_in_byteenable;
assign avalon_mm_out_read = avalon_mm_in_read;
assign avalon_mm_in_readdata = avalon_mm_out_readdata;
assign avalon_mm_in_response = avalon_mm_out_response;
assign avalon_mm_out_write = avalon_mm_in_write;
assign avalon_mm_out_writedata = avalon_mm_in_writedata;
assign avalon_mm_in_waitrequest = avalon_mm_out_waitrequest;

endmodule

