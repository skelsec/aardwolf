"""
RFB protocol implementattion, client side.
Override RFBClient and RFBFactory in your application.
See vncviewer.py for an example.
Reference:
http://www.realvnc.com/docs/rfbproto.pdf
(C) 2003 cliechti@gmx.net
MIT License
"""

KEY_BackSpace = 0xff08
KEY_Tab = 0xff09
KEY_Return = 0xff0d
KEY_Escape = 0xff1b
KEY_Insert = 0xff63
KEY_Delete = 0xffff
KEY_Home = 0xff50
KEY_End = 0xff57
KEY_PageUp = 0xff55
KEY_PageDown = 0xff56
KEY_Left = 0xff51
KEY_Up = 0xff52
KEY_Right = 0xff53
KEY_Down = 0xff54
KEY_F1 = 0xffbe
KEY_F2 = 0xffbf
KEY_F3 = 0xffc0
KEY_F4 = 0xffc1
KEY_F5 = 0xffc2
KEY_F6 = 0xffc3
KEY_F7 = 0xffc4
KEY_F8 = 0xffc5
KEY_F9 = 0xffc6
KEY_F10 = 0xffc7
KEY_F11 = 0xffc8
KEY_F12 = 0xffc9
KEY_F13 = 0xFFCA
KEY_F14 = 0xFFCB
KEY_F15 = 0xFFCC
KEY_F16 = 0xFFCD
KEY_F17 = 0xFFCE
KEY_F18 = 0xFFCF
KEY_F19 = 0xFFD0
KEY_F20 = 0xFFD1
KEY_ShiftLeft = 0xffe1
KEY_ShiftRight = 0xffe2
KEY_ControlLeft = 0xffe3
KEY_ControlRight = 0xffe4
KEY_MetaLeft = 0xffe7
KEY_MetaRight = 0xffe8
KEY_AltLeft = 0xffe9
KEY_AltRight = 0xffea

KEY_Scroll_Lock = 0xFF14
KEY_Sys_Req = 0xFF15
KEY_Num_Lock = 0xFF7F
KEY_Caps_Lock = 0xFFE5
KEY_Pause = 0xFF13
KEY_Super_L = 0xFFEB
KEY_Super_R = 0xFFEC
KEY_Hyper_L = 0xFFED
KEY_Hyper_R = 0xFFEE
KEY_Menu_R = 0xFF67

KEY_KP_0 = 0xFFB0
KEY_KP_1 = 0xFFB1
KEY_KP_2 = 0xFFB2
KEY_KP_3 = 0xFFB3
KEY_KP_4 = 0xFFB4
KEY_KP_5 = 0xFFB5
KEY_KP_6 = 0xFFB6
KEY_KP_7 = 0xFFB7
KEY_KP_8 = 0xFFB8
KEY_KP_9 = 0xFFB9
KEY_KP_Add = 0xFFAB
KEY_KP_Subtract = 0xFFAD
KEY_KP_Multiply = 0xFFAA
KEY_KP_Decimal = 0xFFAE
KEY_KP_Divide = 0xFFAF
KEY_KP_Enter = 0xFF8D
KEY_Print = 0xFF61, 

