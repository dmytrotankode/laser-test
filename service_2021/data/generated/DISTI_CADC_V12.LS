/PROG  DISTI_CADC_V12
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "WeldPRO Auto-Gen";
PROG_SIZE	= 7125;
CREATE		= DATE 26-07-30  TIME 14:36:46;
MODIFIED	= DATE 26-07-30  TIME 15:08:14;
FILE_NAME	= DISTI_CA;
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
	X =  1018.187  mm,	Y =   777.296  mm,	Z =  -244.516  mm,
	W =  -106.497 deg,	P =   -14.995 deg,	R =    94.216 deg
};
P[3]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1018.031  mm,	Y =   780.031  mm,	Z =  -244.575  mm,
	W =  -106.499 deg,	P =   -14.997 deg,	R =    94.226 deg
};
P[4]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1017.949  mm,	Y =   788.432  mm,	Z =  -244.717  mm,
	W =  -106.492 deg,	P =   -15.098 deg,	R =    90.372 deg
};
P[5]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1018.555  mm,	Y =   798.397  mm,	Z =  -244.831  mm,
	W =  -106.479 deg,	P =   -15.217 deg,	R =    85.601 deg
};
P[6]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1019.868  mm,	Y =   808.035  mm,	Z =  -244.881  mm,
	W =  -106.456 deg,	P =   -15.335 deg,	R =    80.815 deg
};
P[7]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1022.050  mm,	Y =   818.023  mm,	Z =  -244.865  mm,
	W =  -106.423 deg,	P =   -15.450 deg,	R =    76.090 deg
};
P[8]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1025.042  mm,	Y =   827.669  mm,	Z =  -244.775  mm,
	W =  -106.378 deg,	P =   -15.565 deg,	R =    71.217 deg
};
P[9]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1028.849  mm,	Y =   836.963  mm,	Z =  -244.612  mm,
	W =  -106.322 deg,	P =   -15.679 deg,	R =    66.207 deg
};
P[10]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1033.478  mm,	Y =   845.904  mm,	Z =  -244.376  mm,
	W =  -106.254 deg,	P =   -15.791 deg,	R =    61.015 deg
};
P[11]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1038.897  mm,	Y =   854.437  mm,	Z =  -244.066  mm,
	W =  -106.177 deg,	P =   -15.894 deg,	R =    55.979 deg
};
P[12]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1045.424  mm,	Y =   862.959  mm,	Z =  -243.662  mm,
	W =  -106.096 deg,	P =   -15.986 deg,	R =    51.162 deg
};
P[13]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1053.418  mm,	Y =   871.648  mm,	Z =  -243.133  mm,
	W =  -106.012 deg,	P =   -16.066 deg,	R =    46.632 deg
};
P[14]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1058.133  mm,	Y =   876.084  mm,	Z =  -242.823  mm,
	W =  -105.919 deg,	P =   -16.142 deg,	R =    41.952 deg
};
P[15]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1067.446  mm,	Y =   883.885  mm,	Z =  -242.155  mm,
	W =  -105.870 deg,	P =   -16.177 deg,	R =    39.609 deg
};
P[16]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1072.926  mm,	Y =   887.914  mm,	Z =  -241.772  mm,
	W =  -105.777 deg,	P =   -16.235 deg,	R =    35.365 deg
};
P[17]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1083.111  mm,	Y =   894.494  mm,	Z =  -241.021  mm,
	W =  -105.677 deg,	P =   -16.289 deg,	R =    30.964 deg
};
P[18]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1093.819  mm,	Y =   900.186  mm,	Z =  -240.210  mm,
	W =  -105.579 deg,	P =   -16.333 deg,	R =    26.830 deg
};
P[19]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1099.342  mm,	Y =   902.691  mm,	Z =  -239.781  mm,
	W =  -105.537 deg,	P =   -16.344 deg,	R =    25.018 deg
};
P[20]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1110.768  mm,	Y =   906.594  mm,	Z =  -239.550  mm,
	W =  -116.027 deg,	P =   -16.063 deg,	R =    30.267 deg
};
P[21]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1119.543  mm,	Y =   909.944  mm,	Z =  -236.198  mm,
	W =  -126.877 deg,	P =   -15.356 deg,	R =    25.893 deg
};
P[22]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1125.737  mm,	Y =   914.559  mm,	Z =  -228.151  mm,
	W =  -119.393 deg,	P =   -15.981 deg,	R =    16.221 deg
};
P[23]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1129.956  mm,	Y =   917.099  mm,	Z =  -222.263  mm,
	W =  -115.329 deg,	P =   -16.208 deg,	R =    11.788 deg
};
P[24]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1135.447  mm,	Y =   919.394  mm,	Z =  -214.348  mm,
	W =  -112.639 deg,	P =   -16.315 deg,	R =     9.714 deg
};
P[25]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1142.744  mm,	Y =   921.604  mm,	Z =  -206.080  mm,
	W =  -110.015 deg,	P =   -16.386 deg,	R =     9.649 deg
};
P[26]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1151.501  mm,	Y =   923.374  mm,	Z =  -200.477  mm,
	W =  -107.391 deg,	P =   -16.429 deg,	R =     8.399 deg
};
P[27]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1159.810  mm,	Y =   924.554  mm,	Z =  -197.694  mm,
	W =  -105.409 deg,	P =   -16.443 deg,	R =     6.805 deg
};
P[28]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1171.276  mm,	Y =   925.588  mm,	Z =  -196.694  mm,
	W =  -104.866 deg,	P =   -16.444 deg,	R =     5.597 deg
};
P[29]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1177.486  mm,	Y =   925.899  mm,	Z =  -196.391  mm,
	W =  -104.887 deg,	P =   -16.444 deg,	R =     3.523 deg
};
P[30]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1186.901  mm,	Y =   925.954  mm,	Z =  -195.935  mm,
	W =  -104.930 deg,	P =   -16.439 deg,	R =     -.729 deg
};
P[31]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1198.984  mm,	Y =   925.062  mm,	Z =  -195.328  mm,
	W =  -104.979 deg,	P =   -16.424 deg,	R =    -5.541 deg
};
P[32]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1210.165  mm,	Y =   923.155  mm,	Z =  -194.752  mm,
	W =  -105.028 deg,	P =   -16.400 deg,	R =   -10.259 deg
};
P[33]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1216.027  mm,	Y =   921.723  mm,	Z =  -194.461  mm,
	W =  -105.070 deg,	P =   -16.371 deg,	R =   -14.490 deg
};
P[34]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1226.466  mm,	Y =   918.525  mm,	Z =  -193.895  mm,
	W =  -105.112 deg,	P =   -16.334 deg,	R =   -18.515 deg
};
P[35]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1234.043  mm,	Y =   915.586  mm,	Z =  -193.491  mm,
	W =  -105.158 deg,	P =   -16.285 deg,	R =   -23.051 deg
};
P[36]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1242.209  mm,	Y =   911.675  mm,	Z =  -193.058  mm,
	W =  -105.219 deg,	P =   -16.204 deg,	R =   -29.417 deg
};
P[37]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1249.803  mm,	Y =   907.037  mm,	Z =  -192.678  mm,
	W =  -105.311 deg,	P =   -16.047 deg,	R =   -39.415 deg
};
P[38]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1257.886  mm,	Y =   900.915  mm,	Z =  -192.137  mm,
	W =  -105.307 deg,	P =   -16.055 deg,	R =   -38.974 deg
};
P[39]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1265.983  mm,	Y =   893.486  mm,	Z =  -191.574  mm,
	W =  -105.302 deg,	P =   -16.063 deg,	R =   -38.625 deg
};
P[40]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1272.053  mm,	Y =   887.764  mm,	Z =  -191.295  mm,
	W =  -105.469 deg,	P =   -15.944 deg,	R =   -44.976 deg
};
P[41]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1277.650  mm,	Y =   882.464  mm,	Z =  -191.147  mm,
	W =  -105.661 deg,	P =   -15.890 deg,	R =   -47.714 deg
};
P[42]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1283.840  mm,	Y =   875.797  mm,	Z =  -191.217  mm,
	W =  -106.210 deg,	P =   -15.792 deg,	R =   -52.259 deg
};
P[43]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1289.748  mm,	Y =   868.182  mm,	Z =  -191.587  mm,
	W =  -106.927 deg,	P =   -15.688 deg,	R =   -56.663 deg
};
P[44]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1294.901  mm,	Y =   860.316  mm,	Z =  -192.256  mm,
	W =  -107.603 deg,	P =   -15.597 deg,	R =   -60.243 deg
};
P[45]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1299.540  mm,	Y =   852.093  mm,	Z =  -193.260  mm,
	W =  -108.271 deg,	P =   -15.504 deg,	R =   -63.685 deg
};
P[46]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1304.990  mm,	Y =   840.580  mm,	Z =  -195.175  mm,
	W =  -109.144 deg,	P =   -15.377 deg,	R =   -68.202 deg
};
P[47]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1307.642  mm,	Y =   833.779  mm,	Z =  -196.396  mm,
	W =  -109.899 deg,	P =   -15.253 deg,	R =   -72.505 deg
};
P[48]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1311.064  mm,	Y =   823.517  mm,	Z =  -197.935  mm,
	W =  -110.273 deg,	P =   -15.181 deg,	R =   -74.981 deg
};
P[49]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1313.858  mm,	Y =   812.194  mm,	Z =  -199.198  mm,
	W =  -110.635 deg,	P =   -14.305 deg,	R =   -78.232 deg
};
P[50]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1314.881  mm,	Y =   806.004  mm,	Z =  -199.681  mm,
	W =  -111.054 deg,	P =   -14.769 deg,	R =   -83.164 deg
};
P[51]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1315.996  mm,	Y =   796.023  mm,	Z =  -200.172  mm,
	W =  -111.190 deg,	P =   -15.305 deg,	R =   -88.308 deg
};
P[52]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.420  mm,	Y =   787.046  mm,	Z =  -200.310  mm,
	W =  -111.129 deg,	P =   -15.645 deg,	R =   -91.614 deg
};
P[53]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.124  mm,	Y =   776.323  mm,	Z =  -200.107  mm,
	W =  -110.761 deg,	P =   -14.624 deg,	R =   -96.574 deg
};
P[54]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1315.427  mm,	Y =   769.147  mm,	Z =  -199.721  mm,
	W =  -110.276 deg,	P =   -14.535 deg,	R =  -100.836 deg
};
P[55]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1313.860  mm,	Y =   759.237  mm,	Z =  -198.899  mm,
	W =  -109.635 deg,	P =   -14.447 deg,	R =  -105.265 deg
};
P[56]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1311.627  mm,	Y =   749.651  mm,	Z =  -197.777  mm,
	W =  -109.083 deg,	P =   -14.382 deg,	R =  -108.625 deg
};
P[57]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1308.699  mm,	Y =   740.275  mm,	Z =  -196.355  mm,
	W =  -108.349 deg,	P =   -14.302 deg,	R =  -112.873 deg
};
P[58]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1304.699  mm,	Y =   730.103  mm,	Z =  -194.451  mm,
	W =  -107.751 deg,	P =   -14.239 deg,	R =  -116.264 deg
};
P[59]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1301.689  mm,	Y =   723.754  mm,	Z =  -193.081  mm,
	W =  -106.927 deg,	P =   -14.148 deg,	R =  -121.193 deg
};
P[60]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1295.734  mm,	Y =   712.868  mm,	Z =  -190.887  mm,
	W =  -106.269 deg,	P =   -14.066 deg,	R =  -125.698 deg
};
P[61]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1288.904  mm,	Y =   702.436  mm,	Z =  -189.359  mm,
	W =  -105.781 deg,	P =   -13.988 deg,	R =  -130.143 deg
};
P[62]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1285.247  mm,	Y =   697.679  mm,	Z =  -188.862  mm,
	W =  -105.529 deg,	P =   -13.914 deg,	R =  -134.519 deg
};
P[63]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1276.775  mm,	Y =   688.197  mm,	Z =  -188.244  mm,
	W =  -105.437 deg,	P =   -13.849 deg,	R =  -138.629 deg
};
P[64]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1271.283  mm,	Y =   683.078  mm,	Z =  -188.139  mm,
	W =  -105.429 deg,	P =   -13.831 deg,	R =  -139.837 deg
};
P[65]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1261.603  mm,	Y =   674.743  mm,	Z =  -188.322  mm,
	W =  -105.443 deg,	P =   -13.863 deg,	R =  -137.727 deg
};
P[66]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1255.299  mm,	Y =   669.513  mm,	Z =  -188.506  mm,
	W =  -105.373 deg,	P =   -13.729 deg,	R =  -147.436 deg
};
P[67]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1247.008  mm,	Y =   663.387  mm,	Z =  -188.771  mm,
	W =  -105.298 deg,	P =   -13.637 deg,	R =  -156.529 deg
};
P[68]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1239.408  mm,	Y =   658.728  mm,	Z =  -189.068  mm,
	W =  -105.277 deg,	P =   -13.618 deg,	R =  -158.976 deg
};
P[69]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1226.721  mm,	Y =   653.167  mm,	Z =  -189.611  mm,
	W =  -105.241 deg,	P =   -13.592 deg,	R =  -162.969 deg
};
P[70]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1218.451  mm,	Y =   650.529  mm,	Z =  -189.968  mm,
	W =  -105.203 deg,	P =   -13.573 deg,	R =  -167.022 deg
};
P[71]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1209.786  mm,	Y =   648.373  mm,	Z =  -190.347  mm,
	W =  -105.159 deg,	P =   -13.560 deg,	R =  -171.569 deg
};
P[72]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1196.562  mm,	Y =   646.156  mm,	Z =  -190.968  mm,
	W =  -105.113 deg,	P =   -13.556 deg,	R =  -176.312 deg
};
P[73]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1188.190  mm,	Y =   645.524  mm,	Z =  -191.356  mm,
	W =  -105.068 deg,	P =   -13.561 deg,	R =   179.213 deg
};
P[74]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1176.476  mm,	Y =   645.533  mm,	Z =  -191.948  mm,
	W =  -105.038 deg,	P =   -13.569 deg,	R =   176.231 deg
};
P[75]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1165.085  mm,	Y =   646.402  mm,	Z =  -192.588  mm,
	W =  -105.207 deg,	P =   -13.572 deg,	R =   175.290 deg
};
P[76]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1157.359  mm,	Y =   647.405  mm,	Z =  -193.325  mm,
	W =  -107.012 deg,	P =   -13.569 deg,	R =   174.537 deg
};
P[77]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1147.595  mm,	Y =   648.994  mm,	Z =  -195.918  mm,
	W =  -109.414 deg,	P =   -13.538 deg,	R =   174.483 deg
};
P[78]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1139.350  mm,	Y =   650.751  mm,	Z =  -200.678  mm,
	W =  -112.196 deg,	P =   -13.466 deg,	R =   175.323 deg
};
P[79]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1132.627  mm,	Y =   652.625  mm,	Z =  -206.954  mm,
	W =  -114.872 deg,	P =   -13.369 deg,	R =   175.422 deg
};
P[80]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1125.021  mm,	Y =   655.603  mm,	Z =  -217.353  mm,
	W =  -120.114 deg,	P =   -13.109 deg,	R =   172.293 deg
};
P[81]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1119.434  mm,	Y =   659.206  mm,	Z =  -225.445  mm,
	W =  -126.811 deg,	P =   -12.622 deg,	R =   167.800 deg
};
P[82]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1111.321  mm,	Y =   663.918  mm,	Z =  -233.065  mm,
	W =  -119.561 deg,	P =   -13.285 deg,	R =   157.806 deg
};
P[83]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1103.183  mm,	Y =   667.015  mm,	Z =  -235.351  mm,
	W =  -107.219 deg,	P =   -13.741 deg,	R =   154.408 deg
};
P[84]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1093.238  mm,	Y =   671.306  mm,	Z =  -236.456  mm,
	W =  -105.746 deg,	P =   -13.749 deg,	R =   154.142 deg
};
P[85]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1087.087  mm,	Y =   674.472  mm,	Z =  -237.040  mm,
	W =  -105.804 deg,	P =   -13.784 deg,	R =   151.506 deg
};
P[86]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1075.876  mm,	Y =   681.285  mm,	Z =  -238.123  mm,
	W =  -105.885 deg,	P =   -13.838 deg,	R =   147.739 deg
};
P[87]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1070.274  mm,	Y =   685.308  mm,	Z =  -238.641  mm,
	W =  -105.988 deg,	P =   -13.918 deg,	R =   142.681 deg
};
P[88]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1060.543  mm,	Y =   693.215  mm,	Z =  -239.583  mm,
	W =  -106.082 deg,	P =   -14.006 deg,	R =   137.688 deg
};
P[89]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1052.094  mm,	Y =   701.162  mm,	Z =  -240.394  mm,
	W =  -106.129 deg,	P =   -14.056 deg,	R =   135.015 deg
};
P[90]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1044.614  mm,	Y =   709.498  mm,	Z =  -241.183  mm,
	W =  -106.186 deg,	P =   -14.117 deg,	R =   131.622 deg
};
P[91]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1037.972  mm,	Y =   718.382  mm,	Z =  -241.900  mm,
	W =  -106.269 deg,	P =   -14.239 deg,	R =   125.999 deg
};
P[92]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1034.619  mm,	Y =   723.682  mm,	Z =  -242.244  mm,
	W =  -106.343 deg,	P =   -14.367 deg,	R =   120.225 deg
};
P[93]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1029.755  mm,	Y =   732.598  mm,	Z =  -242.778  mm,
	W =  -106.384 deg,	P =   -14.458 deg,	R =   116.261 deg
};
P[94]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1025.252  mm,	Y =   743.125  mm,	Z =  -243.321  mm,
	W =  -106.433 deg,	P =   -14.556 deg,	R =   111.957 deg
};
P[95]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1022.067  mm,	Y =   753.233  mm,	Z =  -243.773  mm,
	W =  -106.465 deg,	P =   -14.714 deg,	R =   105.666 deg
};
P[96]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1019.573  mm,	Y =   764.818  mm,	Z =  -244.217  mm,
	W =  -106.480 deg,	P =   -14.798 deg,	R =   102.262 deg
};
P[97]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1018.511  mm,	Y =   773.125  mm,	Z =  -244.430  mm,
	W =  -106.494 deg,	P =   -14.935 deg,	R =    96.828 deg
};
P[98]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1018.031  mm,	Y =   780.030  mm,	Z =  -244.574  mm,
	W =  -106.495 deg,	P =   -15.000 deg,	R =    94.234 deg
};
P[99]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =   651.995  mm,	Y =   781.694  mm,	Z =  -345.952  mm,
	W =  -106.495 deg,	P =   -15.000 deg,	R =    94.234 deg
};
/END
