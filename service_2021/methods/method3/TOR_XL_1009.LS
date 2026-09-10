/PROG  TOR_XL_2907
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "WeldPRO Auto-Gen";
PROG_SIZE	= 5005;
CREATE		= DATE 26-09-10  TIME 17:43:26;
MODIFIED	= DATE 26-09-10  TIME 17:43:26;
FILE_NAME	= ;
VERSION		= 0;
LINE_COUNT	= 77;
MEMORY_SIZE	= 5333;
PROTECT		= READ_WRITE;
TCD:  STACK_SIZE	= 0,
      TASK_PRIORITY	= 50,
      TIME_SLICE	= 0,
      BUSY_LAMP_OFF	= 0,
      ABORT_REQUEST	= 0,
      PAUSE_REQUEST	= 0;
DEFAULT_GROUP	= 1,*,*,*,*;
CONTROL_CODE	= 00000000 00000000;
/MN
   1:  !WeldPRO Auto-Generated TPP ;
   2:  !TOR_XL_2026, TOR_xl_2907 ;
   3:   ;
   4:  UFRAME_NUM=2 ;
   5:  UTOOL_NUM=2 ;
   6:  !Feature Approach ;
   7:J P[1] 100% FINE    ;
   8:   ;
   9:  !Segment1 ;
  10:L P[2] 2000mm/sec FINE
    :  Weld Start[1,1]    ;
  11:L P[3] R[23:moving]mm/sec CNT100    ;
  12:L P[4] R[23:moving]mm/sec CNT100    ;
  13:L P[5] R[23:moving]mm/sec CNT100    ;
  14:L P[6] R[23:moving]mm/sec CNT100    ;
  15:L P[7] R[23:moving]mm/sec CNT100    ;
  16:L P[8] R[23:moving]mm/sec CNT100    ;
  17:L P[9] R[23:moving]mm/sec CNT100    ;
  18:L P[10] R[23:moving]mm/sec CNT100    ;
  19:L P[11] R[23:moving]mm/sec CNT100    ;
  20:L P[12] R[23:moving]mm/sec CNT100    ;
  21:L P[13] R[23:moving]mm/sec CNT100    ;
  22:L P[14] R[23:moving]mm/sec CNT100    ;
  23:L P[15] R[23:moving]mm/sec CNT100    ;
  24:L P[16] R[23:moving]mm/sec CNT100    ;
  25:L P[17] R[23:moving]mm/sec CNT100    ;
  26:L P[18] R[23:moving]mm/sec CNT100    ;
  27:L P[19] R[23:moving]mm/sec CNT100    ;
  28:L P[20] R[23:moving]mm/sec CNT100    ;
  29:L P[21] R[23:moving]mm/sec CNT100    ;
  30:L P[22] R[23:moving]mm/sec CNT100    ;
  31:L P[23] R[23:moving]mm/sec CNT100    ;
  32:L P[24] R[23:moving]mm/sec CNT100    ;
  33:L P[25] R[23:moving]mm/sec CNT100    ;
  34:L P[26] R[23:moving]mm/sec CNT100    ;
  35:L P[27] R[23:moving]mm/sec CNT100    ;
  36:L P[28] R[23:moving]mm/sec CNT100    ;
  37:L P[29] R[23:moving]mm/sec CNT100    ;
  38:L P[30] R[23:moving]mm/sec CNT100    ;
  39:L P[31] R[23:moving]mm/sec CNT100    ;
  40:L P[32] R[23:moving]mm/sec CNT100    ;
  41:L P[33] R[23:moving]mm/sec CNT100    ;
  42:L P[34] R[23:moving]mm/sec CNT100    ;
  43:L P[35] R[23:moving]mm/sec CNT100    ;
  44:L P[36] R[23:moving]mm/sec CNT100    ;
  45:L P[37] R[23:moving]mm/sec CNT100    ;
  46:L P[38] R[23:moving]mm/sec CNT100    ;
  47:L P[39] R[23:moving]mm/sec CNT100    ;
  48:L P[40] R[23:moving]mm/sec CNT100    ;
  49:L P[41] R[23:moving]mm/sec CNT100    ;
  50:L P[42] R[23:moving]mm/sec CNT100    ;
  51:L P[43] R[23:moving]mm/sec CNT100    ;
  52:L P[44] R[23:moving]mm/sec CNT100    ;
  53:L P[45] R[23:moving]mm/sec CNT100    ;
  54:L P[46] R[23:moving]mm/sec CNT100    ;
  55:L P[47] R[23:moving]mm/sec CNT100    ;
  56:L P[48] R[23:moving]mm/sec CNT100    ;
  57:L P[49] R[23:moving]mm/sec CNT100    ;
  58:L P[50] R[23:moving]mm/sec CNT100    ;
  59:L P[51] R[23:moving]mm/sec CNT100    ;
  60:L P[52] R[23:moving]mm/sec CNT100    ;
  61:L P[53] R[23:moving]mm/sec CNT100    ;
  62:L P[54] R[23:moving]mm/sec CNT100    ;
  63:L P[55] R[23:moving]mm/sec CNT100    ;
  64:L P[56] R[23:moving]mm/sec CNT100    ;
  65:L P[57] R[23:moving]mm/sec CNT100    ;
  66:L P[58] R[23:moving]mm/sec CNT100    ;
  67:L P[59] R[23:moving]mm/sec CNT100    ;
  68:L P[60] R[23:moving]mm/sec CNT100    ;
  69:L P[61] R[23:moving]mm/sec CNT100    ;
  70:L P[62] R[23:moving]mm/sec CNT100    ;
  71:L P[63] R[23:moving]mm/sec CNT100    ;
  72:L P[64] R[23:moving]mm/sec CNT100    ;
  73:L P[65] R[23:moving]mm/sec CNT100    ;
  74:L P[66] R[23:moving]mm/sec FINE
    :  Weld End[1,1]    ;
  75:  !Feature Retreat ;
  76:L P[67] 2000mm/sec FINE    ;
  77:  CALL ROZVOROT    ;
/POS
P[1]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =   924.335  mm,	Y =   780.986  mm,	Z =  -268.284  mm,
	W =  -106.495 deg,	P =   -15.000 deg,	R =    94.234 deg
};
P[2]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1020.500  mm,	Y =   780.736  mm,	Z =  -240.858  mm,
	W =  -106.495 deg,	P =   -15.000 deg,	R =    94.234 deg
};
P[3]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1020.362  mm,	Y =   783.751  mm,	Z =  -240.856  mm,
	W =  -106.495 deg,	P =   -15.038 deg,	R =    92.734 deg
};
P[4]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1020.567  mm,	Y =   798.741  mm,	Z =  -240.824  mm,
	W =  -106.479 deg,	P =   -15.217 deg,	R =    85.601 deg
};
P[5]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1022.515  mm,	Y =   813.604  mm,	Z =  -240.749  mm,
	W =  -106.440 deg,	P =   -15.393 deg,	R =    78.462 deg
};
P[6]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1026.263  mm,	Y =   828.117  mm,	Z =  -240.628  mm,
	W =  -106.378 deg,	P =   -15.565 deg,	R =    71.217 deg
};
P[7]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1031.858  mm,	Y =   842.022  mm,	Z =  -240.463  mm,
	W =  -106.289 deg,	P =   -15.736 deg,	R =    63.600 deg
};
P[8]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1039.220  mm,	Y =   855.077  mm,	Z =  -240.255  mm,
	W =  -106.177 deg,	P =   -15.894 deg,	R =    55.979 deg
};
P[9]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1048.149  mm,	Y =   867.115  mm,	Z =  -240.008  mm,
	W =  -106.091 deg,	P =   -15.990 deg,	R =    50.931 deg
};
P[10]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1058.456  mm,	Y =   877.999  mm,	Z =  -239.730  mm,
	W =  -105.919 deg,	P =   -16.142 deg,	R =    41.952 deg
};
P[11]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1069.894  mm,	Y =   887.688  mm,	Z =  -239.425  mm,
	W =  -105.825 deg,	P =   -16.206 deg,	R =    37.555 deg
};
P[12]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1082.287  mm,	Y =   896.117  mm,	Z =  -239.098  mm,
	W =  -105.677 deg,	P =   -16.289 deg,	R =    30.964 deg
};
P[13]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1095.457  mm,	Y =   903.276  mm,	Z =  -238.754  mm,
	W =  -105.559 deg,	P =   -16.340 deg,	R =    26.016 deg
};
P[14]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1108.847  mm,	Y =   909.925  mm,	Z =  -238.734  mm,
	W =  -116.027 deg,	P =   -16.063 deg,	R =    30.267 deg
};
P[15]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1120.045  mm,	Y =   917.212  mm,	Z =  -232.613  mm,
	W =  -122.457 deg,	P =   -15.760 deg,	R =    19.657 deg
};
P[16]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1128.917  mm,	Y =   921.682  mm,	Z =  -221.400  mm,
	W =  -115.329 deg,	P =   -16.208 deg,	R =    11.788 deg
};
P[17]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1138.370  mm,	Y =   924.681  mm,	Z =  -210.173  mm,
	W =  -111.465 deg,	P =   -16.350 deg,	R =     9.989 deg
};
P[18]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1150.809  mm,	Y =   927.069  mm,	Z =  -202.297  mm,
	W =  -107.406 deg,	P =   -16.429 deg,	R =     8.407 deg
};
P[19]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1165.344  mm,	Y =   928.902  mm,	Z =  -199.547  mm,
	W =  -104.856 deg,	P =   -16.443 deg,	R =     6.613 deg
};
P[20]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1180.280  mm,	Y =   930.262  mm,	Z =  -199.691  mm,
	W =  -104.886 deg,	P =   -16.444 deg,	R =     3.601 deg
};
P[21]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1195.269  mm,	Y =   930.374  mm,	Z =  -199.837  mm,
	W =  -104.972 deg,	P =   -16.427 deg,	R =    -4.780 deg
};
P[22]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1210.138  mm,	Y =   928.483  mm,	Z =  -199.984  mm,
	W =  -105.027 deg,	P =   -16.400 deg,	R =   -10.199 deg
};
P[23]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1224.706  mm,	Y =   924.936  mm,	Z =  -200.131  mm,
	W =  -105.112 deg,	P =   -16.334 deg,	R =   -18.515 deg
};
P[24]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1238.840  mm,	Y =   919.941  mm,	Z =  -200.275  mm,
	W =  -105.157 deg,	P =   -16.286 deg,	R =   -23.031 deg
};
P[25]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1252.011  mm,	Y =   912.815  mm,	Z =  -200.413  mm,
	W =  -105.286 deg,	P =   -16.093 deg,	R =   -36.670 deg
};
P[26]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1263.687  mm,	Y =   903.418  mm,	Z =  -200.539  mm,
	W =  -105.307 deg,	P =   -16.055 deg,	R =   -38.974 deg
};
P[27]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1275.415  mm,	Y =   894.071  mm,	Z =  -200.666  mm,
	W =  -105.321 deg,	P =   -16.025 deg,	R =   -40.665 deg
};
P[28]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1286.111  mm,	Y =   883.603  mm,	Z =  -201.429  mm,
	W =  -105.661 deg,	P =   -15.890 deg,	R =   -47.714 deg
};
P[29]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1295.429  mm,	Y =   871.996  mm,	Z =  -203.204  mm,
	W =  -106.549 deg,	P =   -15.741 deg,	R =   -54.452 deg
};
P[30]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1303.339  mm,	Y =   859.489  mm,	Z =  -205.599  mm,
	W =  -107.603 deg,	P =   -15.597 deg,	R =   -60.244 deg
};
P[31]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1309.836  mm,	Y =   846.238  mm,	Z =  -208.240  mm,
	W =  -108.718 deg,	P =   -15.441 deg,	R =   -65.967 deg
};
P[32]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1314.932  mm,	Y =   832.367  mm,	Z =  -210.771  mm,
	W =  -109.899 deg,	P =   -15.253 deg,	R =   -72.505 deg
};
P[33]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1318.626  mm,	Y =   817.987  mm,	Z =  -212.860  mm,
	W =  -110.484 deg,	P =   -15.135 deg,	R =   -76.538 deg
};
P[34]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1320.906  mm,	Y =   803.234  mm,	Z =  -214.217  mm,
	W =  -111.054 deg,	P =   -14.769 deg,	R =   -83.165 deg
};
P[35]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1321.585  mm,	Y =   788.267  mm,	Z =  -214.558  mm,
	W =  -111.194 deg,	P =   -15.444 deg,	R =   -89.637 deg
};
P[36]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1320.553  mm,	Y =   773.335  mm,	Z =  -213.750  mm,
	W =  -110.760 deg,	P =   -14.624 deg,	R =   -96.574 deg
};
P[37]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1317.970  mm,	Y =   758.667  mm,	Z =  -212.037  mm,
	W =  -110.105 deg,	P =   -14.511 deg,	R =  -102.038 deg
};
P[38]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1314.011  mm,	Y =   744.390  mm,	Z =  -209.740  mm,
	W =  -109.083 deg,	P =   -14.382 deg,	R =  -108.626 deg
};
P[39]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1308.656  mm,	Y =   730.627  mm,	Z =  -207.159  mm,
	W =  -108.107 deg,	P =   -14.276 deg,	R =  -114.246 deg
};
P[40]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1301.866  mm,	Y =   717.502  mm,	Z =  -204.623  mm,
	W =  -106.927 deg,	P =   -14.148 deg,	R =  -121.193 deg
};
P[41]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1293.609  mm,	Y =   705.169  mm,	Z =  -202.517  mm,
	W =  -106.127 deg,	P =   -14.043 deg,	R =  -126.998 deg
};
P[42]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1283.943  mm,	Y =   693.791  mm,	Z =  -201.213  mm,
	W =  -105.502 deg,	P =   -13.914 deg,	R =  -134.519 deg
};
P[43]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1272.894  mm,	Y =   683.673  mm,	Z =  -200.913  mm,
	W =  -105.423 deg,	P =   -13.820 deg,	R =  -140.614 deg
};
P[44]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1261.584  mm,	Y =   673.827  mm,	Z =  -200.815  mm,
	W =  -105.443 deg,	P =   -13.863 deg,	R =  -137.727 deg
};
P[45]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1249.475  mm,	Y =   665.033  mm,	Z =  -200.708  mm,
	W =  -105.350 deg,	P =   -13.696 deg,	R =  -150.395 deg
};
P[46]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1235.942  mm,	Y =   658.603  mm,	Z =  -200.585  mm,
	W =  -105.277 deg,	P =   -13.618 deg,	R =  -158.976 deg
};
P[47]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1221.691  mm,	Y =   653.942  mm,	Z =  -200.452  mm,
	W =  -105.222 deg,	P =   -13.582 deg,	R =  -164.940 deg
};
P[48]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1207.054  mm,	Y =   650.706  mm,	Z =  -200.313  mm,
	W =  -105.159 deg,	P =   -13.560 deg,	R =  -171.569 deg
};
P[49]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1192.130  mm,	Y =   649.366  mm,	Z =  -200.169  mm,
	W =  -105.090 deg,	P =   -13.557 deg,	R =  -178.630 deg
};
P[50]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1177.141  mm,	Y =   649.765  mm,	Z =  -200.022  mm,
	W =  -105.038 deg,	P =   -13.569 deg,	R =   176.231 deg
};
P[51]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1162.226  mm,	Y =   650.942  mm,	Z =  -200.549  mm,
	W =  -106.031 deg,	P =   -13.573 deg,	R =   174.828 deg
};
P[52]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1148.400  mm,	Y =   652.675  mm,	Z =  -205.856  mm,
	W =  -109.414 deg,	P =   -13.538 deg,	R =   174.483 deg
};
P[53]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1137.474  mm,	Y =   655.022  mm,	Z =  -215.726  mm,
	W =  -113.043 deg,	P =   -13.435 deg,	R =   176.365 deg
};
P[54]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1128.327  mm,	Y =   658.322  mm,	Z =  -227.140  mm,
	W =  -120.114 deg,	P =   -13.109 deg,	R =   172.293 deg
};
P[55]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1118.819  mm,	Y =   664.060  mm,	Z =  -236.945  mm,
	W =  -125.780 deg,	P =   -12.784 deg,	R =   161.278 deg
};
P[56]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1105.881  mm,	Y =   670.917  mm,	Z =  -239.102  mm,
	W =  -106.615 deg,	P =   -13.747 deg,	R =   154.159 deg
};
P[57]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1092.263  mm,	Y =   677.186  mm,	Z =  -239.237  mm,
	W =  -105.766 deg,	P =   -13.761 deg,	R =   153.218 deg
};
P[58]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1079.196  mm,	Y =   684.533  mm,	Z =  -239.553  mm,
	W =  -105.885 deg,	P =   -13.838 deg,	R =   147.734 deg
};
P[59]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1067.019  mm,	Y =   693.274  mm,	Z =  -239.843  mm,
	W =  -106.000 deg,	P =   -13.929 deg,	R =   142.054 deg
};
P[60]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1055.813  mm,	Y =   703.230  mm,	Z =  -240.108  mm,
	W =  -106.129 deg,	P =   -14.056 deg,	R =   135.011 deg
};
P[61]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1045.777  mm,	Y =   714.364  mm,	Z =  -240.340  mm,
	W =  -106.235 deg,	P =   -14.189 deg,	R =   128.349 deg
};
P[62]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1037.180  mm,	Y =   726.639  mm,	Z =  -240.535  mm,
	W =  -106.343 deg,	P =   -14.369 deg,	R =   120.121 deg
};
P[63]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1030.286  mm,	Y =   739.947  mm,	Z =  -240.684  mm,
	W =  -106.410 deg,	P =   -14.523 deg,	R =   113.528 deg
};
P[64]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1025.194  mm,	Y =   754.044  mm,	Z =  -240.787  mm,
	W =  -106.465 deg,	P =   -14.714 deg,	R =   105.661 deg
};
P[65]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1021.894  mm,	Y =   768.666  mm,	Z =  -240.844  mm,
	W =  -106.490 deg,	P =   -14.880 deg,	R =    99.010 deg
};
P[66]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1020.500  mm,	Y =   780.736  mm,	Z =  -240.858  mm,
	W =  -106.495 deg,	P =   -15.000 deg,	R =    94.234 deg
};
P[67]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =   924.335  mm,	Y =   780.986  mm,	Z =  -268.284  mm,
	W =  -106.495 deg,	P =   -15.000 deg,	R =    94.234 deg
};
/END
