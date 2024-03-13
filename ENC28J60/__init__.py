#!/usr/bin/env python
# -*- coding: utf8 -*-

#   Port from C to Python by Przemyslaw Bereski https://github.com/przemobe/
#   based on https://www.oryx-embedded.com/doc/enc28j60__driver_8c_source.html
#
#   This implementation is for MicroPython v1.17 (RP2)
#
#   This program is free software; you can redistribute it and/or
#   modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation; either version 2
#   of the License, or (at your option) any later version.


import digitalio
from microcontroller import cpu
import time
import struct
from micropython import const

# RX buffer size
ENC28J60_ETH_RX_BUFFER_SIZE          = const(1518)

# RX error codes
_ENC28J60_ETH_RX_ERR_UNSPECIFIED      = const(-1)

# TX buffer size
_ENC28J60_ETH_TX_BUFFER_SIZE          = const(1518)

# TX error codes
_ENC28J60_ETH_TX_ERR_MSGSIZE          = const(-1)
_ENC28J60_ETH_TX_ERR_LINKDOWN         = const(-2)

# Receive and transmit buffers
_ENC28J60_RX_BUFFER_START             = const(0x0000)
_ENC28J60_RX_BUFFER_STOP              = const(0x17FF)
_ENC28J60_TX_BUFFER_START             = const(0x1800)
_ENC28J60_TX_BUFFER_STOP              = const(0x1FFF)

# SPI command set
_ENC28J60_CMD_RCR                     = const(0x00)
_ENC28J60_CMD_RBM                     = const(0x3A)
_ENC28J60_CMD_WCR                     = const(0x40)
_ENC28J60_CMD_WBM                     = const(0x7A)
_ENC28J60_CMD_BFS                     = const(0x80)
_ENC28J60_CMD_BFC                     = const(0xA0)
_ENC28J60_CMD_SRC                     = const(0xFF)

# ENC28J60 register types
_ETH_REG_TYPE                         = const(0x0000)
_MAC_REG_TYPE                         = const(0x1000)
_MII_REG_TYPE                         = const(0x2000)
_PHY_REG_TYPE                         = const(0x3000)

# ENC28J60 banks
_BANK_0                               = const(0x0000)
_BANK_1                               = const(0x0100)
_BANK_2                               = const(0x0200)
_BANK_3                               = const(0x0300)

# Related masks
_REG_TYPE_MASK                        = const(0xF000)
_REG_BANK_MASK                        = const(0x0F00)
_REG_ADDR_MASK                        = const(0x001F)

# ENC28J60 registers
_ENC28J60_ERDPTL                      = const((_ETH_REG_TYPE | _BANK_0 | 0x00))
_ENC28J60_ERDPTH                      = const((_ETH_REG_TYPE | _BANK_0 | 0x01))
_ENC28J60_EWRPTL                      = const((_ETH_REG_TYPE | _BANK_0 | 0x02))
_ENC28J60_EWRPTH                      = const((_ETH_REG_TYPE | _BANK_0 | 0x03))
_ENC28J60_ETXSTL                      = const((_ETH_REG_TYPE | _BANK_0 | 0x04))
_ENC28J60_ETXSTH                      = const((_ETH_REG_TYPE | _BANK_0 | 0x05))
_ENC28J60_ETXNDL                      = const((_ETH_REG_TYPE | _BANK_0 | 0x06))
_ENC28J60_ETXNDH                      = const((_ETH_REG_TYPE | _BANK_0 | 0x07))
_ENC28J60_ERXSTL                      = const((_ETH_REG_TYPE | _BANK_0 | 0x08))
_ENC28J60_ERXSTH                      = const((_ETH_REG_TYPE | _BANK_0 | 0x09))
_ENC28J60_ERXNDL                      = const((_ETH_REG_TYPE | _BANK_0 | 0x0A))
_ENC28J60_ERXNDH                      = const((_ETH_REG_TYPE | _BANK_0 | 0x0B))
_ENC28J60_ERXRDPTL                    = const((_ETH_REG_TYPE | _BANK_0 | 0x0C))
_ENC28J60_ERXRDPTH                    = const((_ETH_REG_TYPE | _BANK_0 | 0x0D))
_ENC28J60_ERXWRPTL                    = const((_ETH_REG_TYPE | _BANK_0 | 0x0E))
_ENC28J60_ERXWRPTH                    = const((_ETH_REG_TYPE | _BANK_0 | 0x0F))
_ENC28J60_EDMASTL                     = const((_ETH_REG_TYPE | _BANK_0 | 0x10))
_ENC28J60_EDMASTH                     = const((_ETH_REG_TYPE | _BANK_0 | 0x11))
_ENC28J60_EDMANDL                     = const((_ETH_REG_TYPE | _BANK_0 | 0x12))
_ENC28J60_EDMANDH                     = const((_ETH_REG_TYPE | _BANK_0 | 0x13))
_ENC28J60_EDMADSTL                    = const((_ETH_REG_TYPE | _BANK_0 | 0x14))
_ENC28J60_EDMADSTH                    = const((_ETH_REG_TYPE | _BANK_0 | 0x15))
_ENC28J60_EDMACSL                     = const((_ETH_REG_TYPE | _BANK_0 | 0x16))
_ENC28J60_EDMACSH                     = const((_ETH_REG_TYPE | _BANK_0 | 0x17))
_ENC28J60_EIE                         = const((_ETH_REG_TYPE | _BANK_0 | 0x1B))
_ENC28J60_EIR                         = const((_ETH_REG_TYPE | _BANK_0 | 0x1C))
_ENC28J60_ESTAT                       = const((_ETH_REG_TYPE | _BANK_0 | 0x1D))
_ENC28J60_ECON2                       = const((_ETH_REG_TYPE | _BANK_0 | 0x1E))
_ENC28J60_ECON1                       = const((_ETH_REG_TYPE | _BANK_0 | 0x1F))
_ENC28J60_EHT0                        = const((_ETH_REG_TYPE | _BANK_1 | 0x00))
_ENC28J60_EHT1                        = const((_ETH_REG_TYPE | _BANK_1 | 0x01))
_ENC28J60_EHT2                        = const((_ETH_REG_TYPE | _BANK_1 | 0x02))
_ENC28J60_EHT3                        = const((_ETH_REG_TYPE | _BANK_1 | 0x03))
_ENC28J60_EHT4                        = const((_ETH_REG_TYPE | _BANK_1 | 0x04))
_ENC28J60_EHT5                        = const((_ETH_REG_TYPE | _BANK_1 | 0x05))
_ENC28J60_EHT6                        = const((_ETH_REG_TYPE | _BANK_1 | 0x06))
_ENC28J60_EHT7                        = const((_ETH_REG_TYPE | _BANK_1 | 0x07))
_ENC28J60_EPMM0                       = const((_ETH_REG_TYPE | _BANK_1 | 0x08))
_ENC28J60_EPMM1                       = const((_ETH_REG_TYPE | _BANK_1 | 0x09))
_ENC28J60_EPMM2                       = const((_ETH_REG_TYPE | _BANK_1 | 0x0A))
_ENC28J60_EPMM3                       = const((_ETH_REG_TYPE | _BANK_1 | 0x0B))
_ENC28J60_EPMM4                       = const((_ETH_REG_TYPE | _BANK_1 | 0x0C))
_ENC28J60_EPMM5                       = const((_ETH_REG_TYPE | _BANK_1 | 0x0D))
_ENC28J60_EPMM6                       = const((_ETH_REG_TYPE | _BANK_1 | 0x0E))
_ENC28J60_EPMM7                       = const((_ETH_REG_TYPE | _BANK_1 | 0x0F))
_ENC28J60_EPMCSL                      = const((_ETH_REG_TYPE | _BANK_1 | 0x10))
_ENC28J60_EPMCSH                      = const((_ETH_REG_TYPE | _BANK_1 | 0x11))
_ENC28J60_EPMOL                       = const((_ETH_REG_TYPE | _BANK_1 | 0x14))
_ENC28J60_EPMOH                       = const((_ETH_REG_TYPE | _BANK_1 | 0x15))
_ENC28J60_EWOLIE                      = const((_ETH_REG_TYPE | _BANK_1 | 0x16))
_ENC28J60_EWOLIR                      = const((_ETH_REG_TYPE | _BANK_1 | 0x17))
_ENC28J60_ERXFCON                     = const((_ETH_REG_TYPE | _BANK_1 | 0x18))
_ENC28J60_EPKTCNT                     = const((_ETH_REG_TYPE | _BANK_1 | 0x19))
_ENC28J60_MACON1                      = const((_MAC_REG_TYPE | _BANK_2 | 0x00))
_ENC28J60_MACON2                      = const((_MAC_REG_TYPE | _BANK_2 | 0x01))
_ENC28J60_MACON3                      = const((_MAC_REG_TYPE | _BANK_2 | 0x02))
_ENC28J60_MACON4                      = const((_MAC_REG_TYPE | _BANK_2 | 0x03))
_ENC28J60_MABBIPG                     = const((_MAC_REG_TYPE | _BANK_2 | 0x04))
_ENC28J60_MAIPGL                      = const((_MAC_REG_TYPE | _BANK_2 | 0x06))
_ENC28J60_MAIPGH                      = const((_MAC_REG_TYPE | _BANK_2 | 0x07))
_ENC28J60_MACLCON1                    = const((_MAC_REG_TYPE | _BANK_2 | 0x08))
_ENC28J60_MACLCON2                    = const((_MAC_REG_TYPE | _BANK_2 | 0x09))
_ENC28J60_MAMXFLL                     = const((_MAC_REG_TYPE | _BANK_2 | 0x0A))
_ENC28J60_MAMXFLH                     = const((_MAC_REG_TYPE | _BANK_2 | 0x0B))
_ENC28J60_MAPHSUP                     = const((_MAC_REG_TYPE | _BANK_2 | 0x0D))
_ENC28J60_MICON                       = const((_MII_REG_TYPE | _BANK_2 | 0x11))
_ENC28J60_MICMD                       = const((_MII_REG_TYPE | _BANK_2 | 0x12))
_ENC28J60_MIREGADR                    = const((_MII_REG_TYPE | _BANK_2 | 0x14))
_ENC28J60_MIWRL                       = const((_MII_REG_TYPE | _BANK_2 | 0x16))
_ENC28J60_MIWRH                       = const((_MII_REG_TYPE | _BANK_2 | 0x17))
_ENC28J60_MIRDL                       = const((_MII_REG_TYPE | _BANK_2 | 0x18))
_ENC28J60_MIRDH                       = const((_MII_REG_TYPE | _BANK_2 | 0x19))
_ENC28J60_MAADR1                      = const((_MAC_REG_TYPE | _BANK_3 | 0x00))
_ENC28J60_MAADR0                      = const((_MAC_REG_TYPE | _BANK_3 | 0x01))
_ENC28J60_MAADR3                      = const((_MAC_REG_TYPE | _BANK_3 | 0x02))
_ENC28J60_MAADR2                      = const((_MAC_REG_TYPE | _BANK_3 | 0x03))
_ENC28J60_MAADR5                      = const((_MAC_REG_TYPE | _BANK_3 | 0x04))
_ENC28J60_MAADR4                      = const((_MAC_REG_TYPE | _BANK_3 | 0x05))
_ENC28J60_EBSTSD                      = const((_ETH_REG_TYPE | _BANK_3 | 0x06))
_ENC28J60_EBSTCON                     = const((_ETH_REG_TYPE | _BANK_3 | 0x07))
_ENC28J60_EBSTCSL                     = const((_ETH_REG_TYPE | _BANK_3 | 0x08))
_ENC28J60_EBSTCSH                     = const((_ETH_REG_TYPE | _BANK_3 | 0x09))
_ENC28J60_MISTAT                      = const((_MII_REG_TYPE | _BANK_3 | 0x0A))
_ENC28J60_EREVID                      = const((_ETH_REG_TYPE | _BANK_3 | 0x12))
_ENC28J60_ECOCON                      = const((_ETH_REG_TYPE | _BANK_3 | 0x15))
_ENC28J60_EFLOCON                     = const((_ETH_REG_TYPE | _BANK_3 | 0x17))
_ENC28J60_EPAUSL                      = const((_ETH_REG_TYPE | _BANK_3 | 0x18))
_ENC28J60_EPAUSH                      = const((_ETH_REG_TYPE | _BANK_3 | 0x19))

# ENC28J60 PHY registers
_ENC28J60_PHCON1                      = const((_PHY_REG_TYPE | 0x00))
_ENC28J60_PHSTAT1                     = const((_PHY_REG_TYPE | 0x01))
_ENC28J60_PHID1                       = const((_PHY_REG_TYPE | 0x02))
_ENC28J60_PHID2                       = const((_PHY_REG_TYPE | 0x03))
_ENC28J60_PHCON2                      = const((_PHY_REG_TYPE | 0x10))
_ENC28J60_PHSTAT2                     = const((_PHY_REG_TYPE | 0x11))
_ENC28J60_PHIE                        = const((_PHY_REG_TYPE | 0x12))
_ENC28J60_PHIR                        = const((_PHY_REG_TYPE | 0x13))
_ENC28J60_PHLCON                      = const((_PHY_REG_TYPE | 0x14))

# Ethernet Interrupt Enable register
_ENC28J60_EIE_INTIE                   = const(0x80)
_ENC28J60_EIE_PKTIE                   = const(0x40)
_ENC28J60_EIE_DMAIE                   = const(0x20)
_ENC28J60_EIE_LINKIE                  = const(0x10)
_ENC28J60_EIE_TXIE                    = const(0x08)
_ENC28J60_EIE_WOLIE                   = const(0x04)
_ENC28J60_EIE_TXERIE                  = const(0x02)
_ENC28J60_EIE_RXERIE                  = const(0x01)

# Ethernet Interrupt Request register
_ENC28J60_EIR_PKTIF                   = const(0x40)
_ENC28J60_EIR_DMAIF                   = const(0x20)
_ENC28J60_EIR_LINKIF                  = const(0x10)
_ENC28J60_EIR_TXIF                    = const(0x08)
_ENC28J60_EIR_WOLIF                   = const(0x04)
_ENC28J60_EIR_TXERIF                  = const(0x02)
_ENC28J60_EIR_RXERIF                  = const(0x01)

# Ethernet Status register
_ENC28J60_ESTAT_INT                   = const(0x80)
_ENC28J60_ESTAT_R6                    = const(0x40)
_ENC28J60_ESTAT_R5                    = const(0x20)
_ENC28J60_ESTAT_LATECOL               = const(0x10)
_ENC28J60_ESTAT_RXBUSY                = const(0x04)
_ENC28J60_ESTAT_TXABRT                = const(0x02)
_ENC28J60_ESTAT_CLKRDY                = const(0x01)

# Ethernet Control 2 register
_ENC28J60_ECON2_AUTOINC               = const(0x80)
_ENC28J60_ECON2_PKTDEC                = const(0x40)
_ENC28J60_ECON2_PWRSV                 = const(0x20)
_ENC28J60_ECON2_VRPS                  = const(0x08)

# Ethernet Control 1 register
_ENC28J60_ECON1_TXRST                 = const(0x80)
_ENC28J60_ECON1_RXRST                 = const(0x40)
_ENC28J60_ECON1_DMAST                 = const(0x20)
_ENC28J60_ECON1_CSUMEN                = const(0x10)
_ENC28J60_ECON1_TXRTS                 = const(0x08)
_ENC28J60_ECON1_RXEN                  = const(0x04)
_ENC28J60_ECON1_BSEL1                 = const(0x02)
_ENC28J60_ECON1_BSEL0                 = const(0x01)

# Ethernet Wake-Up On LAN Interrupt Enable register
_ENC28J60_EWOLIE_UCWOLIE              = const(0x80)
_ENC28J60_EWOLIE_AWOLIE               = const(0x40)
_ENC28J60_EWOLIE_PMWOLIE              = const(0x10)
_ENC28J60_EWOLIE_MPWOLIE              = const(0x08)
_ENC28J60_EWOLIE_HTWOLIE              = const(0x04)
_ENC28J60_EWOLIE_MCWOLIE              = const(0x02)
_ENC28J60_EWOLIE_BCWOLIE              = const(0x01)

# Ethernet Wake-Up On LAN Interrupt Request register
_ENC28J60_EWOLIR_UCWOLIF              = const(0x80)
_ENC28J60_EWOLIR_AWOLIF               = const(0x40)
_ENC28J60_EWOLIR_PMWOLIF              = const(0x10)
_ENC28J60_EWOLIR_MPWOLIF              = const(0x08)
_ENC28J60_EWOLIR_HTWOLIF              = const(0x04)
_ENC28J60_EWOLIR_MCWOLIF              = const(0x02)
_ENC28J60_EWOLIR_BCWOLIF              = const(0x01)

# Receive Filter Control register
_ENC28J60_ERXFCON_UCEN                = const(0x80)
_ENC28J60_ERXFCON_ANDOR               = const(0x40)
_ENC28J60_ERXFCON_CRCEN               = const(0x20)
_ENC28J60_ERXFCON_PMEN                = const(0x10)
_ENC28J60_ERXFCON_MPEN                = const(0x08)
_ENC28J60_ERXFCON_HTEN                = const(0x04)
_ENC28J60_ERXFCON_MCEN                = const(0x02)
_ENC28J60_ERXFCON_BCEN                = const(0x01)

# MAC Control 1 register
_ENC28J60_MACON1_LOOPBK               = const(0x10)
_ENC28J60_MACON1_TXPAUS               = const(0x08)
_ENC28J60_MACON1_RXPAUS               = const(0x04)
_ENC28J60_MACON1_PASSALL              = const(0x02)
_ENC28J60_MACON1_MARXEN               = const(0x01)

# MAC Control 2 register
_ENC28J60_MACON2_MARST                = const(0x80)
_ENC28J60_MACON2_RNDRST               = const(0x40)
_ENC28J60_MACON2_MARXRST              = const(0x08)
_ENC28J60_MACON2_RFUNRST              = const(0x04)
_ENC28J60_MACON2_MATXRST              = const(0x02)
_ENC28J60_MACON2_TFUNRST              = const(0x01)

# MAC Control 3 register
_ENC28J60_MACON3_PADCFG               = const(0xE0)
_ENC28J60_MACON3_PADCFG_NO            = const(0x00)
_ENC28J60_MACON3_PADCFG_60_BYTES      = const(0x20)
_ENC28J60_MACON3_PADCFG_64_BYTES      = const(0x60)
_ENC28J60_MACON3_PADCFG_AUTO          = const(0xA0)
_ENC28J60_MACON3_TXCRCEN              = const(0x10)
_ENC28J60_MACON3_PHDRLEN              = const(0x08)
_ENC28J60_MACON3_HFRMEN               = const(0x04)
_ENC28J60_MACON3_FRMLNEN              = const(0x02)
_ENC28J60_MACON3_FULDPX               = const(0x01)

# MAC Control 4 register
_ENC28J60_MACON4_DEFER                = const(0x40)
_ENC28J60_MACON4_BPEN                 = const(0x20)
_ENC28J60_MACON4_NOBKOFF              = const(0x10)
_ENC28J60_MACON4_LONGPRE              = const(0x02)
_ENC28J60_MACON4_PUREPRE              = const(0x01)

# Back-to-Back Inter-Packet Gap register
_ENC28J60_MABBIPG_DEFAULT_HD          = const(0x12)
_ENC28J60_MABBIPG_DEFAULT_FD          = const(0x15)

# Non-Back-to-Back Inter-Packet Gap Low Byte register
_ENC28J60_MAIPGL_DEFAULT              = const(0x12)

# Non-Back-to-Back Inter-Packet Gap High Byte register
_ENC28J60_MAIPGH_DEFAULT              = const(0x0C)

# Retransmission Maximum register
_ENC28J60_MACLCON1_RETMAX             = const(0x0F)

# Collision Window register
_ENC28J60_MACLCON2_COLWIN             = const(0x3F)
_ENC28J60_MACLCON2_COLWIN_DEFAULT     = const(0x37)

# MAC-PHY Support register
_ENC28J60_MAPHSUP_RSTINTFC            = const(0x80)
_ENC28J60_MAPHSUP_R4                  = const(0x10)
_ENC28J60_MAPHSUP_RSTRMII             = const(0x08)
_ENC28J60_MAPHSUP_R0                  = const(0x01)

# MII Control register
_ENC28J60_MICON_RSTMII                = const(0x80)

# MII Command register
_ENC28J60_MICMD_MIISCAN               = const(0x02)
_ENC28J60_MICMD_MIIRD                 = const(0x01)

# MII Register Address register
_ENC28J60_MIREGADR_VAL                = const(0x1F)

# Self-Test Control register
_ENC28J60_EBSTCON_PSV                 = const(0xE0)
_ENC28J60_EBSTCON_PSEL                = const(0x10)
_ENC28J60_EBSTCON_TMSEL               = const(0x0C)
_ENC28J60_EBSTCON_TMSEL_RANDOM        = const(0x00)
_ENC28J60_EBSTCON_TMSEL_ADDR          = const(0x04)
_ENC28J60_EBSTCON_TMSEL_PATTERN_SHIFT = const(0x08)
_ENC28J60_EBSTCON_TMSEL_RACE_MODE     = const(0x0C)
_ENC28J60_EBSTCON_TME                 = const(0x02)
_ENC28J60_EBSTCON_BISTST              = const(0x01)

# MII Status register
_ENC28J60_MISTAT_R3                   = const(0x08)
_ENC28J60_MISTAT_NVALID               = const(0x04)
_ENC28J60_MISTAT_SCAN                 = const(0x02)
_ENC28J60_MISTAT_BUSY                 = const(0x01)

# Ethernet Revision ID register
_ENC28J60_EREVID_REV                  = const(0x1F)
_ENC28J60_EREVID_REV_B1               = const(0x02)
_ENC28J60_EREVID_REV_B4               = const(0x04)
_ENC28J60_EREVID_REV_B5               = const(0x05)
_ENC28J60_EREVID_REV_B7               = const(0x06)

# Clock Output Control register
_ENC28J60_ECOCON_COCON                = const(0x07)
_ENC28J60_ECOCON_COCON_DISABLED       = const(0x00)
_ENC28J60_ECOCON_COCON_DIV1           = const(0x01)
_ENC28J60_ECOCON_COCON_DIV2           = const(0x02)
_ENC28J60_ECOCON_COCON_DIV3           = const(0x03)
_ENC28J60_ECOCON_COCON_DIV4           = const(0x04)
_ENC28J60_ECOCON_COCON_DIV8           = const(0x05)

# Ethernet Flow Control register
_ENC28J60_EFLOCON_FULDPXS             = const(0x04)
_ENC28J60_EFLOCON_FCEN                = const(0x03)
_ENC28J60_EFLOCON_FCEN_OFF            = const(0x00)
_ENC28J60_EFLOCON_FCEN_ON_HD          = const(0x01)
_ENC28J60_EFLOCON_FCEN_ON_FD          = const(0x02)
_ENC28J60_EFLOCON_FCEN_SEND_PAUSE     = const(0x03)

# PHY Control 1 register
_ENC28J60_PHCON1_PRST                 = const(0x8000)
_ENC28J60_PHCON1_PLOOPBK              = const(0x4000)
_ENC28J60_PHCON1_PPWRSV               = const(0x0800)
_ENC28J60_PHCON1_PDPXMD               = const(0x0100)

# Physical Layer Status 1 register
_ENC28J60_PHSTAT1_PFDPX               = const(0x1000)
_ENC28J60_PHSTAT1_PHDPX               = const(0x0800)
_ENC28J60_PHSTAT1_LLSTAT              = const(0x0004)
_ENC28J60_PHSTAT1_JBRSTAT             = const(0x0002)

# PHY Identifier 1 register
_ENC28J60_PHID1_PIDH                  = const(0xFFFF)
_ENC28J60_PHID1_PIDH_DEFAULT          = const(0x0083)

# PHY Identifier 2 register
_ENC28J60_PHID2_PIDL                  = const(0xFC00)
_ENC28J60_PHID2_PIDL_DEFAULT          = const(0x1400)
_ENC28J60_PHID2_PPN                   = const(0x03F0)
_ENC28J60_PHID2_PPN_DEFAULT           = const(0x0000)
_ENC28J60_PHID2_PREV                  = const(0x000F)

# PHY Control 2 register
_ENC28J60_PHCON2_FRCLNK               = const(0x4000)
_ENC28J60_PHCON2_TXDIS                = const(0x2000)
_ENC28J60_PHCON2_JABBER               = const(0x0400)
_ENC28J60_PHCON2_HDLDIS               = const(0x0100)

# Physical Layer Status 2 register
_ENC28J60_PHSTAT2_TXSTAT              = const(0x2000)
_ENC28J60_PHSTAT2_RXSTAT              = const(0x1000)
_ENC28J60_PHSTAT2_COLSTAT             = const(0x0800)
_ENC28J60_PHSTAT2_LSTAT               = const(0x0400)
_ENC28J60_PHSTAT2_DPXSTAT             = const(0x0200)
_ENC28J60_PHSTAT2_PLRITY              = const(0x0010)

# PHY Interrupt Enable register
_ENC28J60_PHIE_PLNKIE                 = const(0x0010)
_ENC28J60_PHIE_PGEIE                  = const(0x0002)

# PHY Interrupt Request register
_ENC28J60_PHIR_PLNKIF                 = const(0x0010)
_ENC28J60_PHIR_PGIF                   = const(0x0004)

# PHY Module LED Control register
_ENC28J60_PHLCON_LACFG                = const(0x0F00)
_ENC28J60_PHLCON_LACFG_TX             = const(0x0100)
_ENC28J60_PHLCON_LACFG_RX             = const(0x0200)
_ENC28J60_PHLCON_LACFG_COL            = const(0x0300)
_ENC28J60_PHLCON_LACFG_LINK           = const(0x0400)
_ENC28J60_PHLCON_LACFG_DUPLEX         = const(0x0500)
_ENC28J60_PHLCON_LACFG_TX_RX          = const(0x0700)
_ENC28J60_PHLCON_LACFG_ON             = const(0x0800)
_ENC28J60_PHLCON_LACFG_OFF            = const(0x0900)
_ENC28J60_PHLCON_LACFG_BLINK_FAST     = const(0x0A00)
_ENC28J60_PHLCON_LACFG_BLINK_SLOW     = const(0x0B00)
_ENC28J60_PHLCON_LACFG_LINK_RX        = const(0x0C00)
_ENC28J60_PHLCON_LACFG_LINK_TX_RX     = const(0x0D00)
_ENC28J60_PHLCON_LACFG_DUPLEX_COL     = const(0x0E00)
_ENC28J60_PHLCON_LBCFG                = const(0x00F0)
_ENC28J60_PHLCON_LBCFG_TX             = const(0x0010)
_ENC28J60_PHLCON_LBCFG_RX             = const(0x0020)
_ENC28J60_PHLCON_LBCFG_COL            = const(0x0030)
_ENC28J60_PHLCON_LBCFG_LINK           = const(0x0040)
_ENC28J60_PHLCON_LBCFG_DUPLEX         = const(0x0050)
_ENC28J60_PHLCON_LBCFG_TX_RX          = const(0x0070)
_ENC28J60_PHLCON_LBCFG_ON             = const(0x0080)
_ENC28J60_PHLCON_LBCFG_OFF            = const(0x0090)
_ENC28J60_PHLCON_LBCFG_BLINK_FAST     = const(0x00A0)
_ENC28J60_PHLCON_LBCFG_BLINK_SLOW     = const(0x00B0)
_ENC28J60_PHLCON_LBCFG_LINK_RX        = const(0x00C0)
_ENC28J60_PHLCON_LBCFG_LINK_TX_RX     = const(0x00D0)
_ENC28J60_PHLCON_LBCFG_DUPLEX_COL     = const(0x00E0)
_ENC28J60_PHLCON_LFRQ                 = const(0x000C)
_ENC28J60_PHLCON_LFRQ_40_MS           = const(0x0000)
_ENC28J60_PHLCON_LFRQ_73_MS           = const(0x0004)
_ENC28J60_PHLCON_LFRQ_139_MS          = const(0x0008)
_ENC28J60_PHLCON_STRCH                = const(0x0002)

# Per-packet control byte
_ENC28J60_TX_CTRL_PHUGEEN             = const(0x08)
_ENC28J60_TX_CTRL_PPADEN              = const(0x04)
_ENC28J60_TX_CTRL_PCRCEN              = const(0x02)
_ENC28J60_TX_CTRL_POVERRIDE           = const(0x01)

# Receive status vector
_ENC28J60_RSV_VLAN_TYPE               = const(0x4000)
_ENC28J60_RSV_UNKNOWN_OPCODE          = const(0x2000)
_ENC28J60_RSV_PAUSE_CONTROL_FRAME     = const(0x1000)
_ENC28J60_RSV_CONTROL_FRAME           = const(0x0800)
_ENC28J60_RSV_DRIBBLE_NIBBLE          = const(0x0400)
_ENC28J60_RSV_BROADCAST_PACKET        = const(0x0200)
_ENC28J60_RSV_MULTICAST_PACKET        = const(0x0100)
_ENC28J60_RSV_RECEIVED_OK             = const(0x0080)
_ENC28J60_RSV_LENGTH_OUT_OF_RANGE     = const(0x0040)
_ENC28J60_RSV_LENGTH_CHECK_ERROR      = const(0x0020)
_ENC28J60_RSV_CRC_ERROR               = const(0x0010)
_ENC28J60_RSV_CARRIER_EVENT           = const(0x0004)
_ENC28J60_RSV_DROP_EVENT              = const(0x0001)

def LSB(val):
    return (val & 0xFF)

def MSB(val):
    return ((val >> 8) & 0xFF)


class ENC28J60:
    '''
    This class provides control over ENC28J60 Ethernet chips.
    '''

    def __init__(self, spi, cs, macAddr = None, fullDuplex = True, enableMulticastRx = False):
        self.fullDuplex = fullDuplex
        self.enableMulticastRx = enableMulticastRx
        self.revId = None
        self.tmpBytearray1B = bytearray(1)
        self.tmpBytearray2B = bytearray(2)
        self.tmpBytearray3B = bytearray(3)
        self.tmpBytearray6B = bytearray(6)

        # SPI
        self.spi = spi

        # MAC Address
        if macAddr:
            self.macAddr = bytearray(macAddr)
        else:
            self.macAddr = bytearray(b'\x0e\x5f\x5f'+cpu.uid[-3:])

        # PIN CS
        self.cs = digitalio.DigitalInOut(cs)
        self.cs.direction = digitalio.Direction.OUTPUT
        self.cs.value = True

        #self.init()

    def getMacAddr(self):
        return self.macAddr

    def init(self):
        # Issue a system reset
        self.SoftReset()

        # After issuing the reset command, wait at least 1ms in firmware for the device to be ready
        time.sleep(0.01)

        # Initialize driver specific variables
        self.currentBank = 0xFFFF
        self.nextPacket = _ENC28J60_RX_BUFFER_START

        # Read silicon revision ID
        self.revId = self.ReadReg(_ENC28J60_EREVID) & _ENC28J60_EREVID_REV

        # Disable CLKOUT output
        self.WriteReg(_ENC28J60_ECOCON, _ENC28J60_ECOCON_COCON_DISABLED)

        # Set the MAC address of the station
        self.WriteReg(_ENC28J60_MAADR5, self.macAddr[0])
        self.WriteReg(_ENC28J60_MAADR4, self.macAddr[1])
        self.WriteReg(_ENC28J60_MAADR3, self.macAddr[2])
        self.WriteReg(_ENC28J60_MAADR2, self.macAddr[3])
        self.WriteReg(_ENC28J60_MAADR1, self.macAddr[4])
        self.WriteReg(_ENC28J60_MAADR0, self.macAddr[5])

        # Set receive buffer location
        self.WriteReg(_ENC28J60_ERXSTL, LSB(_ENC28J60_RX_BUFFER_START))
        self.WriteReg(_ENC28J60_ERXSTH, MSB(_ENC28J60_RX_BUFFER_START))
        self.WriteReg(_ENC28J60_ERXNDL, LSB(_ENC28J60_RX_BUFFER_STOP))
        self.WriteReg(_ENC28J60_ERXNDH, MSB(_ENC28J60_RX_BUFFER_STOP))

        # The ERXRDPT register defines a location within the FIFO where the receive hardware is forbidden to write to
        self.WriteReg(_ENC28J60_ERXRDPTL, LSB(_ENC28J60_RX_BUFFER_STOP))
        self.WriteReg(_ENC28J60_ERXRDPTH, MSB(_ENC28J60_RX_BUFFER_STOP))

        # Configure the receive filters
        if self.enableMulticastRx:
            self.WriteReg(_ENC28J60_ERXFCON, _ENC28J60_ERXFCON_UCEN | _ENC28J60_ERXFCON_CRCEN | _ENC28J60_ERXFCON_HTEN | _ENC28J60_ERXFCON_BCEN | _ENC28J60_ERXFCON_MCEN)
        else:
            self.WriteReg(_ENC28J60_ERXFCON, _ENC28J60_ERXFCON_UCEN | _ENC28J60_ERXFCON_CRCEN | _ENC28J60_ERXFCON_HTEN | _ENC28J60_ERXFCON_BCEN)

        # Initialize the hash table
        self.WriteReg(_ENC28J60_EHT0, 0x00)
        self.WriteReg(_ENC28J60_EHT1, 0x00)
        self.WriteReg(_ENC28J60_EHT2, 0x00)
        self.WriteReg(_ENC28J60_EHT3, 0x00)
        self.WriteReg(_ENC28J60_EHT4, 0x00)
        self.WriteReg(_ENC28J60_EHT5, 0x00)
        self.WriteReg(_ENC28J60_EHT6, 0x00)
        self.WriteReg(_ENC28J60_EHT7, 0x00)

        # Pull the MAC out of reset
        self.WriteReg(_ENC28J60_MACON2, 0x00)

        # Enable the MAC to receive frames
        self.WriteReg(_ENC28J60_MACON1, _ENC28J60_MACON1_TXPAUS | _ENC28J60_MACON1_RXPAUS | _ENC28J60_MACON1_MARXEN)

        # Enable automatic padding, always append a valid CRC and check frame length. MAC can operate in half-duplex or full-duplex mode
        if self.fullDuplex:
            self.WriteReg(_ENC28J60_MACON3, _ENC28J60_MACON3_PADCFG_AUTO | _ENC28J60_MACON3_TXCRCEN | _ENC28J60_MACON3_FRMLNEN | _ENC28J60_MACON3_FULDPX)
        else:
            self.WriteReg(_ENC28J60_MACON3, _ENC28J60_MACON3_PADCFG_AUTO | _ENC28J60_MACON3_TXCRCEN | _ENC28J60_MACON3_FRMLNEN)

        # When the medium is occupied, the MAC will wait indefinitely for it to become free when attempting to transmit
        self.WriteReg(_ENC28J60_MACON4, _ENC28J60_MACON4_DEFER)

        # Maximum frame length that can be received or transmitted
        self.WriteReg(_ENC28J60_MAMXFLL, LSB(ENC28J60_ETH_RX_BUFFER_SIZE))
        self.WriteReg(_ENC28J60_MAMXFLH, MSB(ENC28J60_ETH_RX_BUFFER_SIZE))

        # Configure the back-to-back inter-packet gap register
        if self.fullDuplex:
            self.WriteReg(_ENC28J60_MABBIPG, _ENC28J60_MABBIPG_DEFAULT_FD)
        else:
            self.WriteReg(_ENC28J60_MABBIPG, _ENC28J60_MABBIPG_DEFAULT_HD)

        # Configure the non-back-to-back inter-packet gap register
        self.WriteReg(_ENC28J60_MAIPGL, _ENC28J60_MAIPGL_DEFAULT)
        self.WriteReg(_ENC28J60_MAIPGH, _ENC28J60_MAIPGH_DEFAULT)

        # Collision window register
        self.WriteReg(_ENC28J60_MACLCON2, _ENC28J60_MACLCON2_COLWIN_DEFAULT)

        # Set the PHY to the proper duplex mode
        if self.fullDuplex:
            self.WritePhyReg(_ENC28J60_PHCON1, _ENC28J60_PHCON1_PDPXMD)
        else:
            self.WritePhyReg(_ENC28J60_PHCON1, 0x0000)

        # Disable half-duplex loopback in PHY
        self.WritePhyReg(_ENC28J60_PHCON2, _ENC28J60_PHCON2_HDLDIS)

        # LEDA displays link status and LEDB displays TX/RX activity
        #self.WritePhyReg(ENC28J60_PHLCON, ENC28J60_PHLCON_LACFG_LINK | ENC28J60_PHLCON_LBCFG_TX_RX | ENC28J60_PHLCON_LFRQ_40_MS | ENC28J60_PHLCON_STRCH)

        # Clear interrupt flags
        self.WriteReg(_ENC28J60_EIR, 0x00)

        # Configure interrupts as desired
        self.WriteReg(_ENC28J60_EIE, _ENC28J60_EIE_INTIE | _ENC28J60_EIE_PKTIE | _ENC28J60_EIE_LINKIE)
        # | ENC28J60_EIE_TXIE | ENC28J60_EIE_TXERIE)

        # Configure PHY interrupts as desired
        self.WritePhyReg(_ENC28J60_PHIE, _ENC28J60_PHIE_PLNKIE | _ENC28J60_PHIE_PGEIE)

        # Set RXEN to enable reception
        self.WriteReg(_ENC28J60_ECON1, _ENC28J60_ECON1_RXEN)

    def writeSpi(self, data):
        while not self.spi.try_lock():
            pass
        self.cs.value = False
        self.spi.write(data)
        self.cs.value = True
        self.spi.unlock()

    def SoftReset(self):
        self.tmpBytearray1B[0] = _ENC28J60_CMD_SRC
        self.writeSpi(self.tmpBytearray1B)

    def ClearBit(self, address, mask):
        self.tmpBytearray2B[0] = (_ENC28J60_CMD_BFC | (address & _REG_ADDR_MASK))
        self.tmpBytearray2B[1] = mask
        self.writeSpi(self.tmpBytearray2B)

    def SetBit(self, address, mask):
        self.tmpBytearray2B[0] = (_ENC28J60_CMD_BFS | (address & _REG_ADDR_MASK))
        self.tmpBytearray2B[1] = mask
        self.writeSpi(self.tmpBytearray2B)

    def SelectBank(self, address):
        # uint16_t address
        bank = address & _REG_BANK_MASK

        # Rewrite the bank number only if a change is detected
        if (bank == self.currentBank):
            return

        # Select the relevant bank
        if bank == _BANK_0:
            self.ClearBit(_ENC28J60_ECON1, _ENC28J60_ECON1_BSEL1 | _ENC28J60_ECON1_BSEL0)
        elif bank == _BANK_1:
            self.SetBit(_ENC28J60_ECON1, _ENC28J60_ECON1_BSEL0)
            self.ClearBit(_ENC28J60_ECON1, _ENC28J60_ECON1_BSEL1)
        elif bank == _BANK_2:
            self.ClearBit(_ENC28J60_ECON1, _ENC28J60_ECON1_BSEL0)
            self.SetBit(_ENC28J60_ECON1, _ENC28J60_ECON1_BSEL1)
        else:
            self.SetBit(_ENC28J60_ECON1, _ENC28J60_ECON1_BSEL1 | _ENC28J60_ECON1_BSEL0)

        # Save bank number
        self.currentBank = bank
        return

    def WriteReg(self, address, data):
        # Make sure the corresponding bank is selected
        self.SelectBank(address)

        # Write opcode and register address, Write register value
        self.tmpBytearray2B[0] = (_ENC28J60_CMD_WCR | (address & _REG_ADDR_MASK))
        self.tmpBytearray2B[1] = data
        self.writeSpi(self.tmpBytearray2B)
        return

    def ReadReg(self, address):
        # Make sure the corresponding bank is selected
        self.SelectBank(address)

        # Pull the CS pin low
        while not self.spi.try_lock():
            pass
        self.cs.value = False

        data = 0
        if (address & _REG_TYPE_MASK) != _ETH_REG_TYPE:
            # Write opcode and register address
            self.tmpBytearray3B[0] = (_ENC28J60_CMD_RCR | (address & _REG_ADDR_MASK))
            # When reading MAC or MII registers, a dummy byte is first shifted out
            self.tmpBytearray3B[1] = 0
            # Read register contents
            self.tmpBytearray3B[2] = 0
            self.spi.write_readinto(self.tmpBytearray3B, self.tmpBytearray3B)
            data = self.tmpBytearray3B[2]
        else:
            # Write opcode and register address
            self.tmpBytearray2B[0] = (_ENC28J60_CMD_RCR | (address & _REG_ADDR_MASK))
            # Read register contents
            self.tmpBytearray2B[1] = 0
            self.spi.write_readinto(self.tmpBytearray2B, self.tmpBytearray2B)
            data = self.tmpBytearray2B[1]

        # Terminate the operation by raising the CS pin
        self.cs.value = True
        self.spi.unlock()

        # Return register contents
        return data

    def WritePhyReg(self, address, data):
        # Write register address
        self.WriteReg(_ENC28J60_MIREGADR, address & _REG_ADDR_MASK)

        # Write the lower 8 bits
        self.WriteReg(_ENC28J60_MIWRL, LSB(data))
        # Write the upper 8 bits
        self.WriteReg(_ENC28J60_MIWRH, MSB(data))

        # Wait until the PHY register has been written
        while 0 != (self.ReadReg(_ENC28J60_MISTAT) & _ENC28J60_MISTAT_BUSY):
            pass
        return

    def ReadPhyReg(self, address):
        # Write register address
        self.WriteReg(_ENC28J60_MIREGADR, address & _REG_ADDR_MASK)

        # Start read operation
        self.WriteReg(_ENC28J60_MICMD, _ENC28J60_MICMD_MIIRD)

        # Wait for the read operation to complete
        while 0 != (self.ReadReg(_ENC28J60_MISTAT) & _ENC28J60_MISTAT_BUSY):
            pass

        # Clear command register
        self.WriteReg(_ENC28J60_MICMD, 0)

        # Read the lower 8 bits
        data = self.ReadReg(_ENC28J60_MIRDL)
        # Read the upper 8 bits
        data |= self.ReadReg(_ENC28J60_MIRDH) << 8

        # Return register contents
        return data

    def WriteBuffer(self, chunks):
        while not self.spi.try_lock():
            pass
        # Pull the CS pin low
        self.cs.value = False

        # Write opcode, Write per-packet control byte
        self.tmpBytearray2B[0] = _ENC28J60_CMD_WBM
        self.tmpBytearray2B[1] = 0x00
        self.spi.write(self.tmpBytearray2B)

        # Loop through data chunks
        for data in chunks:
            self.spi.write(data)

        # Terminate the operation by raising the CS pin
        self.cs.value = True
        self.spi.unlock()

    def ReadBuffer(self, data):
        while not self.spi.try_lock():
            pass
        # Pull the CS pin low
        self.cs.value = False

        # Write opcode
        self.tmpBytearray1B[0] = _ENC28J60_CMD_RBM
        self.spi.write(self.tmpBytearray1B)

        # Copy data from SRAM buffer
        self.spi.readinto(data)

        # Terminate the operation by raising the CS pin
        self.cs.value = True
        self.spi.unlock()

    def GetRevId(self):
        if self.revId is None:
            self.revId = self.ReadReg(_ENC28J60_EREVID) & _ENC28J60_EREVID_REV
        return self.revId

    def IsLinkUp(self):
        return 0 != (self.ReadPhyReg(_ENC28J60_PHSTAT2) & _ENC28J60_PHSTAT2_LSTAT)

    def IsLinkStateChanged(self):
        # Read interrupt status register
        status = self.ReadReg(_ENC28J60_EIR)

        # Check whether the link state has changed
        if 0 == (status & _ENC28J60_EIR_LINKIF):
            return False

        # Clear PHY interrupts flags
        self.ReadPhyReg(_ENC28J60_PHIR)

        # Clear interrupt flag
        self.ClearBit(_ENC28J60_EIR, _ENC28J60_EIR_LINKIF)
        return True

    def GetRxPacketCnt(self):
        return self.ReadReg(_ENC28J60_EPKTCNT)

    def SendPacket(self, chunks):
        # Retrieve the length of the packet
        length = 0
        for data in chunks:
            length += len(data)

        # Check the frame length
        if length > _ENC28J60_ETH_TX_BUFFER_SIZE:
            return _ENC28J60_ETH_TX_ERR_MSGSIZE

        # Make sure the link is up before transmitting the frame
        if False == self.IsLinkUp():
            return _ENC28J60_ETH_TX_ERR_LINKDOWN

        # It is recommended to reset the transmit logic before attempting to transmit a packet
        self.SetBit(_ENC28J60_ECON1, _ENC28J60_ECON1_TXRST)
        self.ClearBit(_ENC28J60_ECON1, _ENC28J60_ECON1_TXRST)

        # Interrupt flags should be cleared after the reset is completed
        self.ClearBit(_ENC28J60_EIR, _ENC28J60_EIR_TXIF | _ENC28J60_EIR_TXERIF)

        # Set transmit buffer location
        self.WriteReg(_ENC28J60_ETXSTL, LSB(_ENC28J60_TX_BUFFER_START))
        self.WriteReg(_ENC28J60_ETXSTH, MSB(_ENC28J60_TX_BUFFER_START))

        # Point to start of transmit buffer
        self.WriteReg(_ENC28J60_EWRPTL, LSB(_ENC28J60_TX_BUFFER_START))
        self.WriteReg(_ENC28J60_EWRPTH, MSB(_ENC28J60_TX_BUFFER_START))

        # Copy the data to the transmit buffer
        self.WriteBuffer(chunks)

        # ETXND should point to the last byte in the data payload
        self.WriteReg(_ENC28J60_ETXNDL, LSB(_ENC28J60_TX_BUFFER_START + length))
        self.WriteReg(_ENC28J60_ETXNDH, MSB(_ENC28J60_TX_BUFFER_START + length))

        # Start transmission
        self.SetBit(_ENC28J60_ECON1, _ENC28J60_ECON1_TXRTS)
        return length

    def ReceivePacket(self, rxBuffer):
        if 0 == self.GetRxPacketCnt():
            return 0

        # Point to the start of the received packet
        self.WriteReg(_ENC28J60_ERDPTL, LSB(self.nextPacket))
        self.WriteReg(_ENC28J60_ERDPTH, MSB(self.nextPacket))

        # The packet is preceded by a 6-byte header
        self.ReadBuffer(self.tmpBytearray6B)

        # Unpack header, little-endian
        headerStruct = struct.unpack("<HHH", self.tmpBytearray6B)

        # The first two bytes are the address of the next packet
        self.nextPacket = headerStruct[0]

        # Get the length of the received packet
        length = headerStruct[1]

        # Get the receive status vector (RSV)
        status = headerStruct[2]

        # Make sure no error occurred
        if 0 != (status & _ENC28J60_RSV_RECEIVED_OK):
            # Limit the number of data to read
            length = min(length, ENC28J60_ETH_RX_BUFFER_SIZE)
            length = min(length, len(rxBuffer))

            # Read the Ethernet frame
            self.ReadBuffer(memoryview(rxBuffer)[0:length])
        else:
            # The received packet contains an error
            length = _ENC28J60_ETH_RX_ERR_UNSPECIFIED

        # Advance the ERXRDPT pointer, taking care to wrap back at the end of the received memory buffer
        if _ENC28J60_RX_BUFFER_START == self.nextPacket:
            self.WriteReg(_ENC28J60_ERXRDPTL, LSB(_ENC28J60_RX_BUFFER_STOP))
            self.WriteReg(_ENC28J60_ERXRDPTH, MSB(_ENC28J60_RX_BUFFER_STOP))
        else:
            self.WriteReg(_ENC28J60_ERXRDPTL, LSB(self.nextPacket - 1))
            self.WriteReg(_ENC28J60_ERXRDPTH, MSB(self.nextPacket - 1))

        # Decrement the packet counter
        self.SetBit(_ENC28J60_ECON2, _ENC28J60_ECON2_PKTDEC)
        return length
