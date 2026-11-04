//Copyright (C)2014-2026 Gowin Semiconductor Corporation.
//All rights reserved.
//File Title: Template file for instantiation
//Tool Version: V1.9.12.03 (64-bit)
//IP Version: 1.0
//Part Number: GW5AST-LV138FPG676AES
//Device: GW5AST-138
//Device Version: B
//Created Time: Thu Sep  3 22:21:38 2026

//Change the instance name and port connections to the signal names
//--------Copy here to design--------

    Gowin_SDP36KE your_instance_name(
        .secco(secco), //output secco
        .decco(decco), //output decco
        .dout(dout), //output [23:0] dout
        .dop(dop), //output [7:0] dop
        .eccp(eccp), //output [7:0] eccp
        .clka(clka), //input clka
        .clkb(clkb), //input clkb
        .cea(cea), //input cea
        .ceb(ceb), //input ceb
        .oce(oce), //input oce
        .reset(reset), //input reset
        .ada(ada), //input [9:0] ada
        .adb(adb), //input [9:0] adb
        .din(din) //input [23:0] din
    );

//--------Copy end-------------------
