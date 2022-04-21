# Extensible FPGA Control Platform

For more information and updates: http://alexforencich.com/wiki/en/verilog/xfcp/start

GitHub repository: https://github.com/alexforencich/xfcp

## Introduction

The Extensible FPGA control platform (XFCP) is a framework that enables simple interfacing between an FPGA design in verilog and control software.  XFCP uses a source-routed packet switched bus over AXI stream to interconnect components in an FPGA design, eliminating the need to assign and manage addresses, enabling simple bus enumeration, and vastly reducing dependencies between the FPGA design and the control software.  XFCP currently supports operation over serial or UDP.  XFCP includes interface modules for serial and UDP, a parametrizable arbiter to enable simultaneous use of multiple interfaces, a parametrizable switch to connect multiple on-FPGA components, bridges for interfacing with various devices, and a Python framework for enumerating XFCP buses and controlling connected devices.

## Software Usage

The python tool is based on Python 3.x and requires pySerial to be installed. It has been used and tested with Python 3.6 (on Ubuntu 18.04) and pySerial 3.5 installed via pip into a venv.

Please note that the I2C read routines do not support reading from specific addresses within a device as, e.g. i2c-tools allows for.

When the xfcp\_ctrl tool is used without any further arguments other than required to connect to the remote system, e.g. via Eth/IP/UDP or a serial port, it enumerates the available modules attached to the XFCP port in the FPGA.

