/PROG  TOR_XL_LEARN_V9
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "WeldPRO Auto-Gen";
PROG_SIZE	= 7125;
CREATE		= DATE 26-07-31  TIME 14:01:48;
MODIFIED	= DATE 26-07-31  TIME 15:02:18;
FILE_NAME	= TOR_XL_L;
VERSION		= 0;
LINE_COUNT	= 113;
MEMORY_SIZE	= 7445;
PROTECT		= READ_WRITE;
TCD:  STACK_SIZE	= 0,
      TASK_PRIORITY	= 50,
      TIME_SLICE	= 0,
      BUSY_LAMP_OFF	= 0,
      ABORT_REQUEST	= 0,
      PAUSE_REQUEST	= 0;
DEFAULT_GROUP	= 1,*,*,*,*;
CONTROL_CODE	= 00000000 00000000;
/APPL
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
  10:L P[2] 2000mm/sec FINE    ;
  11:   ;
  12:  CALL LASER_OFF    ;
  13:L P[3] R[23:moving]mm/sec CNT100    ;
  14:L P[4] R[23:moving]mm/sec CNT100    ;
  15:L P[5] R[23:moving]mm/sec CNT100    ;
  16:L P[6] R[23:moving]mm/sec CNT100    ;
  17:L P[7] R[23:moving]mm/sec CNT100    ;
  18:L P[8] R[23:moving]mm/sec CNT100    ;
  19:L P[9] R[23:moving]mm/sec CNT100    ;
  20:L P[10] R[23:moving]mm/sec CNT100    ;
  21:L P[11] R[23:moving]mm/sec CNT100    ;
  22:L P[12] R[23:moving]mm/sec CNT100    ;
  23:L P[13] R[23:moving]mm/sec CNT100    ;
  24:L P[14] R[23:moving]mm/sec CNT100    ;
  25:L P[15] R[23:moving]mm/sec CNT100    ;
  26:L P[16] R[23:moving]mm/sec CNT100    ;
  27:L P[17] R[23:moving]mm/sec CNT100    ;
  28:L P[18] R[23:moving]mm/sec CNT100    ;
  29:L P[19] R[23:moving]mm/sec CNT100    ;
  30:L P[20] R[23:moving]mm/sec CNT100    ;
  31:L P[21] R[23:moving]mm/sec CNT100    ;
  32:L P[22] R[23:moving]mm/sec CNT100    ;
  33:L P[23] R[23:moving]mm/sec CNT100    ;
  34:L P[24] R[23:moving]mm/sec CNT100    ;
  35:L P[25] R[23:moving]mm/sec CNT100    ;
  36:L P[26] R[23:moving]mm/sec CNT100    ;
  37:L P[27] R[23:moving]mm/sec CNT100    ;
  38:L P[28] R[23:moving]mm/sec CNT100    ;
  39:L P[29] R[23:moving]mm/sec CNT100    ;
  40:L P[30] R[23:moving]mm/sec CNT100    ;
  41:L P[31] R[23:moving]mm/sec CNT100    ;
  42:L P[32] R[23:moving]mm/sec CNT100    ;
  43:L P[33] R[23:moving]mm/sec CNT100    ;
  44:L P[34] R[23:moving]mm/sec CNT100    ;
  45:L P[35] R[23:moving]mm/sec CNT100    ;
  46:L P[36] R[23:moving]mm/sec CNT100    ;
  47:L P[37] R[23:moving]mm/sec CNT100    ;
  48:L P[38] R[23:moving]mm/sec CNT100    ;
  49:L P[39] R[23:moving]mm/sec CNT100    ;
  50:L P[40] R[23:moving]mm/sec CNT100    ;
  51:L P[41] R[23:moving]mm/sec CNT100    ;
  52:L P[42] R[23:moving]mm/sec CNT100    ;
  53:L P[43] R[23:moving]mm/sec CNT100    ;
  54:L P[44] R[23:moving]mm/sec CNT100    ;
  55:L P[45] R[23:moving]mm/sec CNT100    ;
  56:L P[46] R[23:moving]mm/sec CNT100    ;
  57:L P[47] R[23:moving]mm/sec CNT100    ;
  58:L P[48] R[23:moving]mm/sec CNT100    ;
  59:L P[49] R[23:moving]mm/sec CNT100    ;
  60:L P[50] R[23:moving]mm/sec CNT100    ;
  61:L P[51] R[23:moving]mm/sec CNT100    ;
  62:L P[52] R[23:moving]mm/sec CNT100    ;
  63:L P[53] R[23:moving]mm/sec CNT100    ;
  64:L P[54] R[23:moving]mm/sec CNT100    ;
  65:L P[55] R[23:moving]mm/sec CNT100    ;
  66:L P[56] R[23:moving]mm/sec CNT100    ;
  67:L P[57] R[23:moving]mm/sec CNT100    ;
  68:L P[58] R[23:moving]mm/sec CNT100    ;
  69:L P[59] R[23:moving]mm/sec CNT100    ;
  70:L P[60] R[23:moving]mm/sec CNT100    ;
  71:L P[61] R[23:moving]mm/sec CNT100    ;
  72:L P[62] R[23:moving]mm/sec CNT100    ;
  73:L P[63] R[23:moving]mm/sec CNT100    ;
  74:L P[64] R[23:moving]mm/sec CNT100    ;
  75:L P[65] R[23:moving]mm/sec CNT100    ;
  76:L P[66] R[23:moving]mm/sec CNT100    ;
  77:L P[67] R[23:moving]mm/sec CNT100    ;
  78:L P[68] R[23:moving]mm/sec CNT100    ;
  79:L P[69] R[23:moving]mm/sec CNT100    ;
  80:L P[70] R[23:moving]mm/sec CNT100    ;
  81:L P[71] R[23:moving]mm/sec CNT100    ;
  82:L P[72] R[23:moving]mm/sec CNT100    ;
  83:L P[73] R[23:moving]mm/sec CNT100    ;
  84:L P[74] R[23:moving]mm/sec CNT100    ;
  85:L P[75] R[23:moving]mm/sec CNT100    ;
  86:L P[76] R[23:moving]mm/sec CNT100    ;
  87:L P[77] R[23:moving]mm/sec CNT100    ;
  88:L P[78] R[23:moving]mm/sec CNT100    ;
  89:L P[79] R[23:moving]mm/sec CNT100    ;
  90:L P[80] R[23:moving]mm/sec CNT100    ;
  91:L P[81] R[23:moving]mm/sec CNT100    ;
  92:L P[82] R[23:moving]mm/sec CNT100    ;
  93:L P[83] R[23:moving]mm/sec CNT100    ;
  94:L P[84] R[23:moving]mm/sec CNT100    ;
  95:L P[85] R[23:moving]mm/sec CNT100    ;
  96:L P[86] R[23:moving]mm/sec CNT100    ;
  97:L P[87] R[23:moving]mm/sec CNT100    ;
  98:L P[88] R[23:moving]mm/sec CNT100    ;
  99:L P[89] R[23:moving]mm/sec CNT100    ;
 100:L P[90] R[23:moving]mm/sec CNT100    ;
 101:L P[91] R[23:moving]mm/sec CNT100    ;
 102:L P[92] R[23:moving]mm/sec CNT100    ;
 103:L P[93] R[23:moving]mm/sec CNT100    ;
 104:L P[94] R[23:moving]mm/sec CNT100    ;
 105:L P[95] R[23:moving]mm/sec CNT100    ;
 106:L P[96] R[23:moving]mm/sec CNT100    ;
 107:L P[97] R[23:moving]mm/sec CNT100    ;
 108:L P[98] R[23:moving]mm/sec FINE    ;
 109:  CALL LASER_OFF    ;
 110:   ;
 111:  !Feature Retreat ;
 112:L P[99] 2000mm/sec FINE    ;
 113:  CALL ROTATE    ;
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
	X =  1014.789  mm,	Y =   776.665  mm,	Z =  -227.278  mm,
	W =  -106.497 deg,	P =   -14.995 deg,	R =    94.216 deg
};
P[3]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1024.505  mm,	Y =   780.927  mm,	Z =  -240.314  mm,
	W =  -106.501 deg,	P =   -14.998 deg,	R =    94.232 deg
};
P[4]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1024.636  mm,	Y =   788.709  mm,	Z =  -240.491  mm,
	W =  -106.497 deg,	P =   -15.098 deg,	R =    90.375 deg
};
P[5]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1024.604  mm,	Y =   798.213  mm,	Z =  -240.068  mm,
	W =  -106.481 deg,	P =   -15.217 deg,	R =    85.597 deg
};
P[6]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1027.034  mm,	Y =   807.809  mm,	Z =  -240.871  mm,
	W =  -106.456 deg,	P =   -15.334 deg,	R =    80.807 deg
};
P[7]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1028.382  mm,	Y =   817.256  mm,	Z =  -240.661  mm,
	W =  -106.423 deg,	P =   -15.449 deg,	R =    76.083 deg
};
P[8]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1031.489  mm,	Y =   826.400  mm,	Z =  -240.827  mm,
	W =  -106.378 deg,	P =   -15.565 deg,	R =    71.217 deg
};
P[9]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1035.290  mm,	Y =   834.967  mm,	Z =  -240.265  mm,
	W =  -106.322 deg,	P =   -15.679 deg,	R =    66.207 deg
};
P[10]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1039.659  mm,	Y =   843.234  mm,	Z =  -239.849  mm,
	W =  -106.254 deg,	P =   -15.791 deg,	R =    61.015 deg
};
P[11]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1044.485  mm,	Y =   851.302  mm,	Z =  -239.675  mm,
	W =  -106.179 deg,	P =   -15.896 deg,	R =    55.983 deg
};
P[12]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1050.327  mm,	Y =   858.701  mm,	Z =  -239.422  mm,
	W =  -106.096 deg,	P =   -15.986 deg,	R =    51.162 deg
};
P[13]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1056.705  mm,	Y =   865.645  mm,	Z =  -239.256  mm,
	W =  -106.012 deg,	P =   -16.066 deg,	R =    46.632 deg
};
P[14]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1063.039  mm,	Y =   872.723  mm,	Z =  -239.319  mm,
	W =  -105.919 deg,	P =   -16.142 deg,	R =    41.952 deg
};
P[15]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1070.464  mm,	Y =   878.827  mm,	Z =  -238.789  mm,
	W =  -105.870 deg,	P =   -16.177 deg,	R =    39.609 deg
};
P[16]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1078.232  mm,	Y =   883.977  mm,	Z =  -238.126  mm,
	W =  -105.777 deg,	P =   -16.235 deg,	R =    35.365 deg
};
P[17]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1086.213  mm,	Y =   888.779  mm,	Z =  -237.701  mm,
	W =  -105.677 deg,	P =   -16.289 deg,	R =    30.964 deg
};
P[18]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1094.455  mm,	Y =   893.020  mm,	Z =  -237.084  mm,
	W =  -105.579 deg,	P =   -16.333 deg,	R =    26.830 deg
};
P[19]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1103.001  mm,	Y =   897.245  mm,	Z =  -236.610  mm,
	W =  -105.535 deg,	P =   -16.344 deg,	R =    25.007 deg
};
P[20]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1112.364  mm,	Y =   902.470  mm,	Z =  -236.227  mm,
	W =  -116.027 deg,	P =   -16.063 deg,	R =    30.267 deg
};
P[21]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1120.181  mm,	Y =   905.563  mm,	Z =  -231.619  mm,
	W =  -126.877 deg,	P =   -15.356 deg,	R =    25.893 deg
};
P[22]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1124.072  mm,	Y =   908.316  mm,	Z =  -228.277  mm,
	W =  -121.184 deg,	P =   -15.973 deg,	R =    18.444 deg
};
P[23]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1130.757  mm,	Y =   911.350  mm,	Z =  -220.329  mm,
	W =  -115.329 deg,	P =   -16.208 deg,	R =    11.788 deg
};
P[24]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1136.522  mm,	Y =   913.279  mm,	Z =  -212.859  mm,
	W =  -112.639 deg,	P =   -16.315 deg,	R =     9.714 deg
};
P[25]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1143.135  mm,	Y =   915.415  mm,	Z =  -204.496  mm,
	W =  -110.015 deg,	P =   -16.386 deg,	R =     9.649 deg
};
P[26]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1147.497  mm,	Y =   916.260  mm,	Z =  -200.751  mm,
	W =  -108.552 deg,	P =   -16.418 deg,	R =     8.950 deg
};
P[27]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1160.493  mm,	Y =   918.504  mm,	Z =  -196.243  mm,
	W =  -105.409 deg,	P =   -16.443 deg,	R =     6.805 deg
};
P[28]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1170.094  mm,	Y =   919.201  mm,	Z =  -195.467  mm,
	W =  -104.866 deg,	P =   -16.444 deg,	R =     5.597 deg
};
P[29]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1179.454  mm,	Y =   919.775  mm,	Z =  -194.717  mm,
	W =  -104.887 deg,	P =   -16.444 deg,	R =     3.523 deg
};
P[30]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1188.473  mm,	Y =   919.713  mm,	Z =  -194.157  mm,
	W =  -104.930 deg,	P =   -16.439 deg,	R =     -.729 deg
};
P[31]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1197.603  mm,	Y =   919.541  mm,	Z =  -194.363  mm,
	W =  -104.979 deg,	P =   -16.424 deg,	R =    -5.541 deg
};
P[32]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1206.476  mm,	Y =   918.164  mm,	Z =  -193.987  mm,
	W =  -105.028 deg,	P =   -16.400 deg,	R =   -10.259 deg
};
P[33]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1215.232  mm,	Y =   916.023  mm,	Z =  -193.619  mm,
	W =  -105.070 deg,	P =   -16.371 deg,	R =   -14.490 deg
};
P[34]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1224.128  mm,	Y =   913.590  mm,	Z =  -193.558  mm,
	W =  -105.112 deg,	P =   -16.334 deg,	R =   -18.515 deg
};
P[35]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1232.497  mm,	Y =   910.498  mm,	Z =  -192.956  mm,
	W =  -105.158 deg,	P =   -16.285 deg,	R =   -23.051 deg
};
P[36]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1240.390  mm,	Y =   906.785  mm,	Z =  -192.910  mm,
	W =  -105.219 deg,	P =   -16.204 deg,	R =   -29.417 deg
};
P[37]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1247.174  mm,	Y =   902.726  mm,	Z =  -192.387  mm,
	W =  -105.311 deg,	P =   -16.047 deg,	R =   -39.415 deg
};
P[38]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1254.787  mm,	Y =   896.227  mm,	Z =  -192.217  mm,
	W =  -105.307 deg,	P =   -16.055 deg,	R =   -38.974 deg
};
P[39]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1262.559  mm,	Y =   890.166  mm,	Z =  -191.678  mm,
	W =  -105.302 deg,	P =   -16.063 deg,	R =   -38.625 deg
};
P[40]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1269.811  mm,	Y =   885.013  mm,	Z =  -191.864  mm,
	W =  -105.469 deg,	P =   -15.944 deg,	R =   -44.976 deg
};
P[41]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1276.392  mm,	Y =   878.562  mm,	Z =  -191.566  mm,
	W =  -105.661 deg,	P =   -15.890 deg,	R =   -47.714 deg
};
P[42]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1282.291  mm,	Y =   871.796  mm,	Z =  -192.163  mm,
	W =  -106.210 deg,	P =   -15.792 deg,	R =   -52.259 deg
};
P[43]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1288.390  mm,	Y =   865.189  mm,	Z =  -192.838  mm,
	W =  -106.927 deg,	P =   -15.688 deg,	R =   -56.663 deg
};
P[44]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1293.507  mm,	Y =   857.570  mm,	Z =  -194.095  mm,
	W =  -107.603 deg,	P =   -15.597 deg,	R =   -60.244 deg
};
P[45]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1298.666  mm,	Y =   849.748  mm,	Z =  -195.902  mm,
	W =  -108.271 deg,	P =   -15.504 deg,	R =   -63.686 deg
};
P[46]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1302.170  mm,	Y =   841.599  mm,	Z =  -196.533  mm,
	W =  -109.143 deg,	P =   -15.377 deg,	R =   -68.203 deg
};
P[47]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1306.219  mm,	Y =   833.139  mm,	Z =  -198.469  mm,
	W =  -109.899 deg,	P =   -15.253 deg,	R =   -72.505 deg
};
P[48]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1308.943  mm,	Y =   823.926  mm,	Z =  -200.119  mm,
	W =  -110.273 deg,	P =   -15.181 deg,	R =   -74.982 deg
};
P[49]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1312.162  mm,	Y =   814.620  mm,	Z =  -201.692  mm,
	W =  -110.635 deg,	P =   -14.305 deg,	R =   -78.232 deg
};
P[50]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1313.750  mm,	Y =   805.447  mm,	Z =  -202.661  mm,
	W =  -111.054 deg,	P =   -14.769 deg,	R =   -83.164 deg
};
P[51]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1314.408  mm,	Y =   796.276  mm,	Z =  -202.819  mm,
	W =  -111.189 deg,	P =   -15.305 deg,	R =   -88.309 deg
};
P[52]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1317.538  mm,	Y =   786.313  mm,	Z =  -203.950  mm,
	W =  -111.129 deg,	P =   -15.645 deg,	R =   -91.614 deg
};
P[53]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1314.838  mm,	Y =   780.920  mm,	Z =  -202.854  mm,
	W =  -110.924 deg,	P =   -15.048 deg,	R =   -94.524 deg
};
P[54]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1313.573  mm,	Y =   767.404  mm,	Z =  -201.903  mm,
	W =  -110.276 deg,	P =   -14.535 deg,	R =  -100.837 deg
};
P[55]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1311.802  mm,	Y =   758.078  mm,	Z =  -200.638  mm,
	W =  -109.635 deg,	P =   -14.447 deg,	R =  -105.265 deg
};
P[56]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1309.500  mm,	Y =   748.738  mm,	Z =  -199.298  mm,
	W =  -109.082 deg,	P =   -14.382 deg,	R =  -108.626 deg
};
P[57]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1306.573  mm,	Y =   739.605  mm,	Z =  -198.078  mm,
	W =  -108.349 deg,	P =   -14.302 deg,	R =  -112.873 deg
};
P[58]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1302.902  mm,	Y =   730.640  mm,	Z =  -196.760  mm,
	W =  -107.748 deg,	P =   -14.239 deg,	R =  -116.265 deg
};
P[59]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1298.610  mm,	Y =   722.338  mm,	Z =  -194.838  mm,
	W =  -106.924 deg,	P =   -14.148 deg,	R =  -121.191 deg
};
P[60]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1293.830  mm,	Y =   714.085  mm,	Z =  -193.540  mm,
	W =  -106.269 deg,	P =   -14.066 deg,	R =  -125.698 deg
};
P[61]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1287.939  mm,	Y =   706.673  mm,	Z =  -192.109  mm,
	W =  -105.781 deg,	P =   -13.988 deg,	R =  -130.143 deg
};
P[62]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1282.411  mm,	Y =   698.596  mm,	Z =  -191.529  mm,
	W =  -105.526 deg,	P =   -13.913 deg,	R =  -134.520 deg
};
P[63]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1276.108  mm,	Y =   691.203  mm,	Z =  -191.252  mm,
	W =  -105.437 deg,	P =   -13.849 deg,	R =  -138.629 deg
};
P[64]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1268.507  mm,	Y =   684.941  mm,	Z =  -190.871  mm,
	W =  -105.429 deg,	P =   -13.831 deg,	R =  -139.837 deg
};
P[65]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1260.550  mm,	Y =   678.551  mm,	Z =  -191.051  mm,
	W =  -105.443 deg,	P =   -13.863 deg,	R =  -137.727 deg
};
P[66]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1253.614  mm,	Y =   672.078  mm,	Z =  -191.403  mm,
	W =  -105.373 deg,	P =   -13.729 deg,	R =  -147.436 deg
};
P[67]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1246.068  mm,	Y =   665.962  mm,	Z =  -191.505  mm,
	W =  -105.298 deg,	P =   -13.637 deg,	R =  -156.529 deg
};
P[68]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1237.009  mm,	Y =   661.763  mm,	Z =  -191.808  mm,
	W =  -105.277 deg,	P =   -13.618 deg,	R =  -158.977 deg
};
P[69]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1228.021  mm,	Y =   657.171  mm,	Z =  -192.239  mm,
	W =  -105.241 deg,	P =   -13.592 deg,	R =  -162.969 deg
};
P[70]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1218.317  mm,	Y =   654.976  mm,	Z =  -192.207  mm,
	W =  -105.201 deg,	P =   -13.569 deg,	R =  -167.030 deg
};
P[71]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1208.751  mm,	Y =   652.412  mm,	Z =  -192.321  mm,
	W =  -105.159 deg,	P =   -13.560 deg,	R =  -171.569 deg
};
P[72]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1198.810  mm,	Y =   651.586  mm,	Z =  -192.714  mm,
	W =  -105.113 deg,	P =   -13.556 deg,	R =  -176.312 deg
};
P[73]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1188.737  mm,	Y =   651.055  mm,	Z =  -193.571  mm,
	W =  -105.068 deg,	P =   -13.561 deg,	R =   179.213 deg
};
P[74]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1178.780  mm,	Y =   651.189  mm,	Z =  -193.647  mm,
	W =  -105.038 deg,	P =   -13.569 deg,	R =   176.231 deg
};
P[75]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1168.891  mm,	Y =   652.700  mm,	Z =  -193.645  mm,
	W =  -105.207 deg,	P =   -13.572 deg,	R =   175.290 deg
};
P[76]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1159.436  mm,	Y =   653.732  mm,	Z =  -194.223  mm,
	W =  -107.012 deg,	P =   -13.569 deg,	R =   174.537 deg
};
P[77]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1150.674  mm,	Y =   654.474  mm,	Z =  -197.193  mm,
	W =  -109.414 deg,	P =   -13.538 deg,	R =   174.483 deg
};
P[78]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1143.329  mm,	Y =   655.175  mm,	Z =  -201.298  mm,
	W =  -112.196 deg,	P =   -13.466 deg,	R =   175.322 deg
};
P[79]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1137.149  mm,	Y =   655.911  mm,	Z =  -208.042  mm,
	W =  -114.872 deg,	P =   -13.369 deg,	R =   175.422 deg
};
P[80]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1130.956  mm,	Y =   657.769  mm,	Z =  -215.635  mm,
	W =  -120.114 deg,	P =   -13.109 deg,	R =   172.292 deg
};
P[81]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1124.038  mm,	Y =   662.119  mm,	Z =  -227.430  mm,
	W =  -126.809 deg,	P =   -12.620 deg,	R =   167.791 deg
};
P[82]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1115.879  mm,	Y =   665.747  mm,	Z =  -233.001  mm,
	W =  -119.561 deg,	P =   -13.285 deg,	R =   157.805 deg
};
P[83]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1106.655  mm,	Y =   670.304  mm,	Z =  -235.517  mm,
	W =  -107.325 deg,	P =   -13.741 deg,	R =   154.436 deg
};
P[84]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1097.258  mm,	Y =   674.542  mm,	Z =  -236.520  mm,
	W =  -105.746 deg,	P =   -13.749 deg,	R =   154.142 deg
};
P[85]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1088.643  mm,	Y =   679.567  mm,	Z =  -236.618  mm,
	W =  -105.804 deg,	P =   -13.784 deg,	R =   151.506 deg
};
P[86]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1080.042  mm,	Y =   684.917  mm,	Z =  -237.525  mm,
	W =  -105.885 deg,	P =   -13.838 deg,	R =   147.739 deg
};
P[87]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1071.999  mm,	Y =   690.827  mm,	Z =  -237.991  mm,
	W =  -105.988 deg,	P =   -13.918 deg,	R =   142.681 deg
};
P[88]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1064.613  mm,	Y =   697.541  mm,	Z =  -238.429  mm,
	W =  -106.083 deg,	P =   -14.001 deg,	R =   137.677 deg
};
P[89]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1057.495  mm,	Y =   704.420  mm,	Z =  -238.754  mm,
	W =  -106.129 deg,	P =   -14.056 deg,	R =   135.014 deg
};
P[90]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1050.660  mm,	Y =   711.710  mm,	Z =  -239.259  mm,
	W =  -106.186 deg,	P =   -14.117 deg,	R =   131.622 deg
};
P[91]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1044.767  mm,	Y =   719.009  mm,	Z =  -239.316  mm,
	W =  -106.269 deg,	P =   -14.234 deg,	R =   126.207 deg
};
P[92]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1039.812  mm,	Y =   727.678  mm,	Z =  -239.554  mm,
	W =  -106.343 deg,	P =   -14.367 deg,	R =   120.225 deg
};
P[93]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1035.250  mm,	Y =   735.475  mm,	Z =  -239.992  mm,
	W =  -106.383 deg,	P =   -14.448 deg,	R =   116.672 deg
};
P[94]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1032.207  mm,	Y =   743.708  mm,	Z =  -240.206  mm,
	W =  -106.433 deg,	P =   -14.556 deg,	R =   111.957 deg
};
P[95]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1028.503  mm,	Y =   754.881  mm,	Z =  -240.490  mm,
	W =  -106.465 deg,	P =   -14.714 deg,	R =   105.666 deg
};
P[96]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1026.002  mm,	Y =   764.393  mm,	Z =  -240.685  mm,
	W =  -106.480 deg,	P =   -14.798 deg,	R =   102.261 deg
};
P[97]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1025.029  mm,	Y =   773.991  mm,	Z =  -240.592  mm,
	W =  -106.494 deg,	P =   -14.935 deg,	R =    96.827 deg
};
P[98]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1024.455  mm,	Y =   781.010  mm,	Z =  -240.717  mm,
	W =  -106.501 deg,	P =   -15.000 deg,	R =    94.235 deg
};
P[99]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =   651.995  mm,	Y =   781.694  mm,	Z =  -345.952  mm,
	W =  -106.495 deg,	P =   -15.000 deg,	R =    94.234 deg
};
/END
