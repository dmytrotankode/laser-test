/PROG  DISTI_LINE_V24
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "WeldPRO Auto-Gen";
PROG_SIZE	= 7125;
CREATE		= DATE 26-07-31  TIME 14:01:48;
MODIFIED	= DATE 26-07-31  TIME 15:02:18;
FILE_NAME	= DISTI_LI;
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
	X =  1010.370  mm,	Y =   780.780  mm,	Z =  -223.355  mm,
	W =  -106.497 deg,	P =   -14.995 deg,	R =    94.216 deg
};
P[3]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1019.821  mm,	Y =   785.134  mm,	Z =  -236.554  mm,
	W =  -106.501 deg,	P =   -14.998 deg,	R =    94.232 deg
};
P[4]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1020.222  mm,	Y =   793.318  mm,	Z =  -236.497  mm,
	W =  -106.497 deg,	P =   -15.098 deg,	R =    90.375 deg
};
P[5]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1020.578  mm,	Y =   803.303  mm,	Z =  -235.780  mm,
	W =  -106.481 deg,	P =   -15.217 deg,	R =    85.597 deg
};
P[6]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1023.401  mm,	Y =   813.332  mm,	Z =  -236.362  mm,
	W =  -106.456 deg,	P =   -15.334 deg,	R =    80.807 deg
};
P[7]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1025.208  mm,	Y =   823.200  mm,	Z =  -235.900  mm,
	W =  -106.423 deg,	P =   -15.449 deg,	R =    76.083 deg
};
P[8]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1028.795  mm,	Y =   832.721  mm,	Z =  -235.877  mm,
	W =  -106.378 deg,	P =   -15.565 deg,	R =    71.217 deg
};
P[9]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1033.125  mm,	Y =   841.614  mm,	Z =  -235.166  mm,
	W =  -106.322 deg,	P =   -15.679 deg,	R =    66.207 deg
};
P[10]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1038.058  mm,	Y =   850.189  mm,	Z =  -234.625  mm,
	W =  -106.254 deg,	P =   -15.791 deg,	R =    61.015 deg
};
P[11]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1043.466  mm,	Y =   858.518  mm,	Z =  -234.345  mm,
	W =  -106.179 deg,	P =   -15.896 deg,	R =    55.983 deg
};
P[12]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1049.889  mm,	Y =   866.097  mm,	Z =  -234.038  mm,
	W =  -106.096 deg,	P =   -15.986 deg,	R =    51.162 deg
};
P[13]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1056.839  mm,	Y =   873.156  mm,	Z =  -233.848  mm,
	W =  -106.012 deg,	P =   -16.066 deg,	R =    46.632 deg
};
P[14]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1063.780  mm,	Y =   880.341  mm,	Z =  -233.879  mm,
	W =  -105.919 deg,	P =   -16.142 deg,	R =    41.952 deg
};
P[15]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1071.620  mm,	Y =   886.322  mm,	Z =  -233.389  mm,
	W =  -105.870 deg,	P =   -16.177 deg,	R =    39.609 deg
};
P[16]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1079.947  mm,	Y =   891.437  mm,	Z =  -232.800  mm,
	W =  -105.777 deg,	P =   -16.235 deg,	R =    35.365 deg
};
P[17]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1088.499  mm,	Y =   896.185  mm,	Z =  -232.465  mm,
	W =  -105.677 deg,	P =   -16.289 deg,	R =    30.964 deg
};
P[18]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1097.290  mm,	Y =   900.314  mm,	Z =  -231.964  mm,
	W =  -105.579 deg,	P =   -16.333 deg,	R =    26.830 deg
};
P[19]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1106.164  mm,	Y =   904.307  mm,	Z =  -231.624  mm,
	W =  -105.535 deg,	P =   -16.344 deg,	R =    25.007 deg
};
P[20]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1115.681  mm,	Y =   908.753  mm,	Z =  -232.402  mm,
	W =  -116.027 deg,	P =   -16.063 deg,	R =    30.267 deg
};
P[21]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1124.652  mm,	Y =   911.125  mm,	Z =  -228.914  mm,
	W =  -126.877 deg,	P =   -15.356 deg,	R =    25.893 deg
};
P[22]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1129.164  mm,	Y =   914.079  mm,	Z =  -225.105  mm,
	W =  -121.184 deg,	P =   -15.973 deg,	R =    18.444 deg
};
P[23]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1136.600  mm,	Y =   916.975  mm,	Z =  -216.735  mm,
	W =  -115.329 deg,	P =   -16.208 deg,	R =    11.788 deg
};
P[24]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1142.765  mm,	Y =   918.590  mm,	Z =  -209.136  mm,
	W =  -112.639 deg,	P =   -16.315 deg,	R =     9.714 deg
};
P[25]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1149.614  mm,	Y =   920.324  mm,	Z =  -200.671  mm,
	W =  -110.015 deg,	P =   -16.386 deg,	R =     9.649 deg
};
P[26]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1154.135  mm,	Y =   920.952  mm,	Z =  -196.898  mm,
	W =  -108.552 deg,	P =   -16.418 deg,	R =     8.950 deg
};
P[27]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1167.446  mm,	Y =   922.717  mm,	Z =  -192.422  mm,
	W =  -105.409 deg,	P =   -16.443 deg,	R =     6.805 deg
};
P[28]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1177.194  mm,	Y =   923.086  mm,	Z =  -191.875  mm,
	W =  -104.866 deg,	P =   -16.444 deg,	R =     5.597 deg
};
P[29]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1186.808  mm,	Y =   923.325  mm,	Z =  -191.405  mm,
	W =  -104.887 deg,	P =   -16.444 deg,	R =     3.523 deg
};
P[30]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1196.284  mm,	Y =   922.927  mm,	Z =  -191.131  mm,
	W =  -104.930 deg,	P =   -16.439 deg,	R =     -.729 deg
};
P[31]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1205.901  mm,	Y =   922.397  mm,	Z =  -191.628  mm,
	W =  -104.979 deg,	P =   -16.424 deg,	R =    -5.541 deg
};
P[32]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1215.220  mm,	Y =   920.613  mm,	Z =  -191.572  mm,
	W =  -105.028 deg,	P =   -16.400 deg,	R =   -10.259 deg
};
P[33]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1224.336  mm,	Y =   918.046  mm,	Z =  -191.546  mm,
	W =  -105.070 deg,	P =   -16.371 deg,	R =   -14.490 deg
};
P[34]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1233.542  mm,	Y =   915.169  mm,	Z =  -191.839  mm,
	W =  -105.112 deg,	P =   -16.334 deg,	R =   -18.515 deg
};
P[35]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1242.253  mm,	Y =   911.583  mm,	Z =  -191.596  mm,
	W =  -105.158 deg,	P =   -16.285 deg,	R =   -23.051 deg
};
P[36]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1250.597  mm,	Y =   907.274  mm,	Z =  -191.908  mm,
	W =  -105.219 deg,	P =   -16.204 deg,	R =   -29.417 deg
};
P[37]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1258.085  mm,	Y =   902.327  mm,	Z =  -191.712  mm,
	W =  -105.311 deg,	P =   -16.047 deg,	R =   -39.415 deg
};
P[38]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1265.436  mm,	Y =   895.605  mm,	Z =  -191.991  mm,
	W =  -105.307 deg,	P =   -16.055 deg,	R =   -38.974 deg
};
P[39]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1272.979  mm,	Y =   889.297  mm,	Z =  -191.892  mm,
	W =  -105.302 deg,	P =   -16.063 deg,	R =   -38.625 deg
};
P[40]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1280.513  mm,	Y =   883.431  mm,	Z =  -192.471  mm,
	W =  -105.469 deg,	P =   -15.944 deg,	R =   -44.976 deg
};
P[41]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1287.060  mm,	Y =   876.529  mm,	Z =  -192.599  mm,
	W =  -105.661 deg,	P =   -15.890 deg,	R =   -47.714 deg
};
P[42]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1292.984  mm,	Y =   869.184  mm,	Z =  -193.640  mm,
	W =  -106.210 deg,	P =   -15.792 deg,	R =   -52.259 deg
};
P[43]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1299.067  mm,	Y =   861.980  mm,	Z =  -194.778  mm,
	W =  -106.927 deg,	P =   -15.688 deg,	R =   -56.663 deg
};
P[44]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1304.043  mm,	Y =   853.879  mm,	Z =  -196.496  mm,
	W =  -107.603 deg,	P =   -15.597 deg,	R =   -60.244 deg
};
P[45]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1309.007  mm,	Y =   845.597  mm,	Z =  -198.771  mm,
	W =  -108.271 deg,	P =   -15.504 deg,	R =   -63.686 deg
};
P[46]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1312.350  mm,	Y =   836.885  mm,	Z =  -199.846  mm,
	W =  -109.143 deg,	P =   -15.377 deg,	R =   -68.203 deg
};
P[47]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.142  mm,	Y =   827.905  mm,	Z =  -202.242  mm,
	W =  -109.899 deg,	P =   -15.253 deg,	R =   -72.505 deg
};
P[48]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1318.536  mm,	Y =   818.401  mm,	Z =  -204.300  mm,
	W =  -110.273 deg,	P =   -15.181 deg,	R =   -74.982 deg
};
P[49]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1321.415  mm,	Y =   808.735  mm,	Z =  -206.305  mm,
	W =  -110.635 deg,	P =   -14.305 deg,	R =   -78.232 deg
};
P[50]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1322.688  mm,	Y =   799.014  mm,	Z =  -207.639  mm,
	W =  -111.054 deg,	P =   -14.769 deg,	R =   -83.164 deg
};
P[51]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1323.017  mm,	Y =   789.283  mm,	Z =  -208.104  mm,
	W =  -111.189 deg,	P =   -15.305 deg,	R =   -88.309 deg
};
P[52]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1325.739  mm,	Y =   778.914  mm,	Z =  -209.632  mm,
	W =  -111.129 deg,	P =   -15.645 deg,	R =   -91.614 deg
};
P[53]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1322.857  mm,	Y =   773.313  mm,	Z =  -208.602  mm,
	W =  -110.924 deg,	P =   -15.048 deg,	R =   -94.524 deg
};
P[54]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1321.048  mm,	Y =   759.222  mm,	Z =  -207.969  mm,
	W =  -110.276 deg,	P =   -14.535 deg,	R =  -100.837 deg
};
P[55]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1318.887  mm,	Y =   749.503  mm,	Z =  -206.873  mm,
	W =  -109.635 deg,	P =   -14.447 deg,	R =  -105.265 deg
};
P[56]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.204  mm,	Y =   739.893  mm,	Z =  -205.696  mm,
	W =  -109.082 deg,	P =   -14.382 deg,	R =  -108.626 deg
};
P[57]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1312.849  mm,	Y =   730.439  mm,	Z =  -204.594  mm,
	W =  -108.349 deg,	P =   -14.302 deg,	R =  -112.873 deg
};
P[58]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1308.771  mm,	Y =   721.261  mm,	Z =  -203.379  mm,
	W =  -107.748 deg,	P =   -14.239 deg,	R =  -116.265 deg
};
P[59]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1304.015  mm,	Y =   712.622  mm,	Z =  -201.497  mm,
	W =  -106.924 deg,	P =   -14.148 deg,	R =  -121.191 deg
};
P[60]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1298.740  mm,	Y =   704.121  mm,	Z =  -200.240  mm,
	W =  -106.269 deg,	P =   -14.066 deg,	R =  -125.698 deg
};
P[61]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1292.356  mm,	Y =   696.518  mm,	Z =  -198.805  mm,
	W =  -105.781 deg,	P =   -13.988 deg,	R =  -130.143 deg
};
P[62]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1286.256  mm,	Y =   688.292  mm,	Z =  -198.278  mm,
	W =  -105.526 deg,	P =   -13.913 deg,	R =  -134.520 deg
};
P[63]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1279.388  mm,	Y =   680.827  mm,	Z =  -198.025  mm,
	W =  -105.437 deg,	P =   -13.849 deg,	R =  -138.629 deg
};
P[64]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1271.490  mm,	Y =   674.737  mm,	Z =  -197.598  mm,
	W =  -105.429 deg,	P =   -13.831 deg,	R =  -139.837 deg
};
P[65]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1263.488  mm,	Y =   668.766  mm,	Z =  -197.726  mm,
	W =  -105.443 deg,	P =   -13.863 deg,	R =  -137.727 deg
};
P[66]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1255.487  mm,	Y =   661.961  mm,	Z =  -198.059  mm,
	W =  -105.373 deg,	P =   -13.729 deg,	R =  -147.436 deg
};
P[67]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1246.871  mm,	Y =   655.696  mm,	Z =  -198.114  mm,
	W =  -105.298 deg,	P =   -13.637 deg,	R =  -156.529 deg
};
P[68]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1237.425  mm,	Y =   651.729  mm,	Z =  -198.261  mm,
	W =  -105.277 deg,	P =   -13.618 deg,	R =  -158.977 deg
};
P[69]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1227.871  mm,	Y =   647.338  mm,	Z =  -198.551  mm,
	W =  -105.241 deg,	P =   -13.592 deg,	R =  -162.969 deg
};
P[70]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1217.684  mm,	Y =   645.377  mm,	Z =  -198.280  mm,
	W =  -105.201 deg,	P =   -13.569 deg,	R =  -167.030 deg
};
P[71]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1207.562  mm,	Y =   643.071  mm,	Z =  -198.173  mm,
	W =  -105.159 deg,	P =   -13.560 deg,	R =  -171.569 deg
};
P[72]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1197.091  mm,	Y =   642.561  mm,	Z =  -198.279  mm,
	W =  -105.113 deg,	P =   -13.556 deg,	R =  -176.312 deg
};
P[73]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1186.511  mm,	Y =   642.405  mm,	Z =  -198.834  mm,
	W =  -105.068 deg,	P =   -13.561 deg,	R =   179.213 deg
};
P[74]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1176.252  mm,	Y =   642.901  mm,	Z =  -198.592  mm,
	W =  -105.038 deg,	P =   -13.569 deg,	R =   176.231 deg
};
P[75]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1166.323  mm,	Y =   644.759  mm,	Z =  -198.246  mm,
	W =  -105.207 deg,	P =   -13.572 deg,	R =   175.290 deg
};
P[76]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1156.780  mm,	Y =   646.192  mm,	Z =  -198.677  mm,
	W =  -107.012 deg,	P =   -13.569 deg,	R =   174.537 deg
};
P[77]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1147.910  mm,	Y =   647.407  mm,	Z =  -201.587  mm,
	W =  -109.414 deg,	P =   -13.538 deg,	R =   174.483 deg
};
P[78]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1140.504  mm,	Y =   648.581  mm,	Z =  -205.710  mm,
	W =  -112.196 deg,	P =   -13.466 deg,	R =   175.322 deg
};
P[79]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1134.112  mm,	Y =   649.857  mm,	Z =  -212.492  mm,
	W =  -114.872 deg,	P =   -13.369 deg,	R =   175.422 deg
};
P[80]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1127.385  mm,	Y =   652.495  mm,	Z =  -220.333  mm,
	W =  -120.114 deg,	P =   -13.109 deg,	R =   172.292 deg
};
P[81]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1119.832  mm,	Y =   657.983  mm,	Z =  -232.379  mm,
	W =  -126.809 deg,	P =   -12.620 deg,	R =   167.791 deg
};
P[82]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1110.769  mm,	Y =   662.009  mm,	Z =  -236.929  mm,
	W =  -119.561 deg,	P =   -13.285 deg,	R =   157.805 deg
};
P[83]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1101.357  mm,	Y =   666.544  mm,	Z =  -237.804  mm,
	W =  -107.325 deg,	P =   -13.741 deg,	R =   154.436 deg
};
P[84]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1092.071  mm,	Y =   671.083  mm,	Z =  -238.211  mm,
	W =  -105.746 deg,	P =   -13.749 deg,	R =   154.142 deg
};
P[85]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1083.394  mm,	Y =   676.537  mm,	Z =  -237.889  mm,
	W =  -105.804 deg,	P =   -13.784 deg,	R =   151.506 deg
};
P[86]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1074.624  mm,	Y =   682.421  mm,	Z =  -238.370  mm,
	W =  -105.885 deg,	P =   -13.838 deg,	R =   147.739 deg
};
P[87]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1066.355  mm,	Y =   688.940  mm,	Z =  -238.417  mm,
	W =  -105.988 deg,	P =   -13.918 deg,	R =   142.681 deg
};
P[88]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1058.805  mm,	Y =   696.272  mm,	Z =  -238.431  mm,
	W =  -106.083 deg,	P =   -14.001 deg,	R =   137.677 deg
};
P[89]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1051.729  mm,	Y =   703.600  mm,	Z =  -238.324  mm,
	W =  -106.129 deg,	P =   -14.056 deg,	R =   135.014 deg
};
P[90]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1044.905  mm,	Y =   711.404  mm,	Z =  -238.396  mm,
	W =  -106.186 deg,	P =   -14.117 deg,	R =   131.622 deg
};
P[91]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1038.932  mm,	Y =   719.363  mm,	Z =  -238.057  mm,
	W =  -106.269 deg,	P =   -14.234 deg,	R =   126.207 deg
};
P[92]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1033.956  mm,	Y =   728.747  mm,	Z =  -237.887  mm,
	W =  -106.343 deg,	P =   -14.367 deg,	R =   120.225 deg
};
P[93]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1029.494  mm,	Y =   737.045  mm,	Z =  -237.946  mm,
	W =  -106.383 deg,	P =   -14.448 deg,	R =   116.672 deg
};
P[94]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1026.552  mm,	Y =   745.846  mm,	Z =  -237.820  mm,
	W =  -106.433 deg,	P =   -14.556 deg,	R =   111.957 deg
};
P[95]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1023.050  mm,	Y =   757.784  mm,	Z =  -237.651  mm,
	W =  -106.465 deg,	P =   -14.714 deg,	R =   105.666 deg
};
P[96]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1020.808  mm,	Y =   767.731  mm,	Z =  -237.476  mm,
	W =  -106.480 deg,	P =   -14.798 deg,	R =   102.261 deg
};
P[97]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1020.107  mm,	Y =   777.922  mm,	Z =  -237.062  mm,
	W =  -106.494 deg,	P =   -14.935 deg,	R =    96.827 deg
};
P[98]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1019.762  mm,	Y =   785.231  mm,	Z =  -236.953  mm,
	W =  -106.501 deg,	P =   -15.000 deg,	R =    94.235 deg
};
P[99]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =   651.995  mm,	Y =   781.694  mm,	Z =  -345.952  mm,
	W =  -106.495 deg,	P =   -15.000 deg,	R =    94.234 deg
};
/END
