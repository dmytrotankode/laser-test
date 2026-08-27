/PROG  DISTI_CADC_V4
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "WeldPRO Auto-Gen";
PROG_SIZE	= 7071;
CREATE		= DATE 26-07-30  TIME 13:37:36;
MODIFIED	= DATE 26-07-30  TIME 14:22:58;
FILE_NAME	= DISTI_CA;
VERSION		= 0;
LINE_COUNT	= 113;
MEMORY_SIZE	= 7391;
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
	X =  1017.370  mm,	Y =   777.976  mm,	Z =  -241.793  mm,
	W =  -106.497 deg,	P =   -14.995 deg,	R =    94.216 deg
};
P[3]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1017.248  mm,	Y =   780.723  mm,	Z =  -241.802  mm,
	W =  -106.499 deg,	P =   -14.997 deg,	R =    94.226 deg
};
P[4]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1017.209  mm,	Y =   786.375  mm,	Z =  -241.808  mm,
	W =  -106.492 deg,	P =   -15.098 deg,	R =    90.372 deg
};
P[5]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1017.723  mm,	Y =   796.345  mm,	Z =  -241.784  mm,
	W =  -106.479 deg,	P =   -15.217 deg,	R =    85.601 deg
};
P[6]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1018.949  mm,	Y =   805.994  mm,	Z =  -241.715  mm,
	W =  -106.456 deg,	P =   -15.335 deg,	R =    80.815 deg
};
P[7]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1021.040  mm,	Y =   816.000  mm,	Z =  -241.590  mm,
	W =  -106.423 deg,	P =   -15.450 deg,	R =    76.090 deg
};
P[8]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1023.946  mm,	Y =   825.671  mm,	Z =  -241.413  mm,
	W =  -106.378 deg,	P =   -15.565 deg,	R =    71.217 deg
};
P[9]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1027.673  mm,	Y =   834.996  mm,	Z =  -241.183  mm,
	W =  -106.322 deg,	P =   -15.679 deg,	R =    66.207 deg
};
P[10]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1032.225  mm,	Y =   843.974  mm,	Z =  -240.902  mm,
	W =  -106.254 deg,	P =   -15.791 deg,	R =    61.015 deg
};
P[11]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1037.572  mm,	Y =   852.551  mm,	Z =  -240.567  mm,
	W =  -106.177 deg,	P =   -15.894 deg,	R =    55.979 deg
};
P[12]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1044.028  mm,	Y =   861.126  mm,	Z =  -240.159  mm,
	W =  -106.096 deg,	P =   -15.986 deg,	R =    51.162 deg
};
P[13]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1051.952  mm,	Y =   869.881  mm,	Z =  -239.653  mm,
	W =  -106.012 deg,	P =   -16.066 deg,	R =    46.632 deg
};
P[14]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1056.633  mm,	Y =   874.353  mm,	Z =  -239.365  mm,
	W =  -105.919 deg,	P =   -16.142 deg,	R =    41.952 deg
};
P[15]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1065.884  mm,	Y =   882.233  mm,	Z =  -238.760  mm,
	W =  -105.870 deg,	P =   -16.177 deg,	R =    39.609 deg
};
P[16]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1076.012  mm,	Y =   889.558  mm,	Z =  -238.107  mm,
	W =  -105.777 deg,	P =   -16.235 deg,	R =    35.365 deg
};
P[17]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1081.472  mm,	Y =   892.968  mm,	Z =  -237.767  mm,
	W =  -105.677 deg,	P =   -16.289 deg,	R =    30.964 deg
};
P[18]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1092.140  mm,	Y =   898.748  mm,	Z =  -237.077  mm,
	W =  -105.579 deg,	P =   -16.333 deg,	R =    26.830 deg
};
P[19]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1097.646  mm,	Y =   901.299  mm,	Z =  -236.718  mm,
	W =  -105.535 deg,	P =   -16.349 deg,	R =    25.033 deg
};
P[20]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1110.440  mm,	Y =   905.854  mm,	Z =  -236.069  mm,
	W =  -116.027 deg,	P =   -16.063 deg,	R =    30.267 deg
};
P[21]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1118.690  mm,	Y =   909.153  mm,	Z =  -232.559  mm,
	W =  -126.877 deg,	P =   -15.356 deg,	R =    25.893 deg
};
P[22]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1124.205  mm,	Y =   913.188  mm,	Z =  -225.397  mm,
	W =  -119.393 deg,	P =   -15.981 deg,	R =    16.221 deg
};
P[23]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1128.512  mm,	Y =   915.682  mm,	Z =  -219.553  mm,
	W =  -115.329 deg,	P =   -16.208 deg,	R =    11.788 deg
};
P[24]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1135.289  mm,	Y =   918.267  mm,	Z =  -210.223  mm,
	W =  -112.639 deg,	P =   -16.315 deg,	R =     9.714 deg
};
P[25]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1142.717  mm,	Y =   920.316  mm,	Z =  -202.730  mm,
	W =  -110.015 deg,	P =   -16.386 deg,	R =     9.649 deg
};
P[26]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1150.423  mm,	Y =   921.844  mm,	Z =  -198.124  mm,
	W =  -107.391 deg,	P =   -16.429 deg,	R =     8.399 deg
};
P[27]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1160.176  mm,	Y =   923.230  mm,	Z =  -195.288  mm,
	W =  -105.409 deg,	P =   -16.443 deg,	R =     6.805 deg
};
P[28]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1170.243  mm,	Y =   924.200  mm,	Z =  -194.711  mm,
	W =  -104.866 deg,	P =   -16.444 deg,	R =     5.597 deg
};
P[29]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1181.449  mm,	Y =   924.729  mm,	Z =  -194.361  mm,
	W =  -104.887 deg,	P =   -16.444 deg,	R =     3.523 deg
};
P[30]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1189.929  mm,	Y =   924.582  mm,	Z =  -194.115  mm,
	W =  -104.930 deg,	P =   -16.439 deg,	R =     -.729 deg
};
P[31]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1197.977  mm,	Y =   923.913  mm,	Z =  -193.887  mm,
	W =  -104.979 deg,	P =   -16.424 deg,	R =    -5.541 deg
};
P[32]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1209.185  mm,	Y =   922.102  mm,	Z =  -193.555  mm,
	W =  -105.028 deg,	P =   -16.400 deg,	R =   -10.259 deg
};
P[33]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1215.064  mm,	Y =   920.718  mm,	Z =  -193.391  mm,
	W =  -105.070 deg,	P =   -16.371 deg,	R =   -14.490 deg
};
P[34]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1225.541  mm,	Y =   917.610  mm,	Z =  -193.076  mm,
	W =  -105.112 deg,	P =   -16.334 deg,	R =   -18.515 deg
};
P[35]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1233.150  mm,	Y =   914.735  mm,	Z =  -192.858  mm,
	W =  -105.158 deg,	P =   -16.285 deg,	R =   -23.051 deg
};
P[36]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1241.356  mm,	Y =   910.890  mm,	Z =  -192.629  mm,
	W =  -105.219 deg,	P =   -16.204 deg,	R =   -29.417 deg
};
P[37]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1251.307  mm,	Y =   904.767  mm,	Z =  -192.360  mm,
	W =  -105.311 deg,	P =   -16.047 deg,	R =   -39.415 deg
};
P[38]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1257.145  mm,	Y =   900.262  mm,	Z =  -192.165  mm,
	W =  -105.307 deg,	P =   -16.055 deg,	R =   -38.974 deg
};
P[39]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1265.324  mm,	Y =   892.908  mm,	Z =  -191.892  mm,
	W =  -105.302 deg,	P =   -16.063 deg,	R =   -38.625 deg
};
P[40]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1271.447  mm,	Y =   887.236  mm,	Z =  -191.804  mm,
	W =  -105.469 deg,	P =   -15.944 deg,	R =   -44.976 deg
};
P[41]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1280.106  mm,	Y =   879.019  mm,	Z =  -191.917  mm,
	W =  -105.661 deg,	P =   -15.890 deg,	R =   -47.714 deg
};
P[42]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1286.195  mm,	Y =   872.038  mm,	Z =  -192.332  mm,
	W =  -106.210 deg,	P =   -15.792 deg,	R =   -52.259 deg
};
P[43]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1291.890  mm,	Y =   864.203  mm,	Z =  -193.084  mm,
	W =  -106.927 deg,	P =   -15.688 deg,	R =   -56.663 deg
};
P[44]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1296.801  mm,	Y =   856.305  mm,	Z =  -194.123  mm,
	W =  -107.603 deg,	P =   -15.597 deg,	R =   -60.243 deg
};
P[45]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1301.959  mm,	Y =   846.606  mm,	Z =  -195.775  mm,
	W =  -108.271 deg,	P =   -15.504 deg,	R =   -63.685 deg
};
P[46]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1304.733  mm,	Y =   840.427  mm,	Z =  -197.034  mm,
	W =  -109.144 deg,	P =   -15.377 deg,	R =   -68.202 deg
};
P[47]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1309.161  mm,	Y =   829.001  mm,	Z =  -199.267  mm,
	W =  -109.899 deg,	P =   -15.253 deg,	R =   -72.505 deg
};
P[48]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1310.907  mm,	Y =   823.467  mm,	Z =  -200.172  mm,
	W =  -110.273 deg,	P =   -15.181 deg,	R =   -74.981 deg
};
P[49]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1313.781  mm,	Y =   812.193  mm,	Z =  -201.666  mm,
	W =  -110.635 deg,	P =   -14.305 deg,	R =   -78.232 deg
};
P[50]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1315.552  mm,	Y =   801.398  mm,	Z =  -202.628  mm,
	W =  -111.054 deg,	P =   -14.769 deg,	R =   -83.164 deg
};
P[51]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.393  mm,	Y =   791.780  mm,	Z =  -203.106  mm,
	W =  -111.190 deg,	P =   -15.305 deg,	R =   -88.308 deg
};
P[52]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.605  mm,	Y =   782.091  mm,	Z =  -203.250  mm,
	W =  -111.129 deg,	P =   -15.645 deg,	R =   -91.614 deg
};
P[53]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.145  mm,	Y =   773.096  mm,	Z =  -203.070  mm,
	W =  -110.761 deg,	P =   -14.624 deg,	R =   -96.574 deg
};
P[54]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1315.169  mm,	Y =   764.533  mm,	Z =  -202.606  mm,
	W =  -110.276 deg,	P =   -14.535 deg,	R =  -100.836 deg
};
P[55]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1313.369  mm,	Y =   754.668  mm,	Z =  -201.740  mm,
	W =  -109.635 deg,	P =   -14.447 deg,	R =  -105.265 deg
};
P[56]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1310.936  mm,	Y =   745.206  mm,	Z =  -200.575  mm,
	W =  -109.083 deg,	P =   -14.382 deg,	R =  -108.625 deg
};
P[57]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1307.943  mm,	Y =   736.217  mm,	Z =  -199.154  mm,
	W =  -108.349 deg,	P =   -14.302 deg,	R =  -112.873 deg
};
P[58]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1305.458  mm,	Y =   729.967  mm,	Z =  -197.987  mm,
	W =  -107.751 deg,	P =   -14.239 deg,	R =  -116.264 deg
};
P[59]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1299.936  mm,	Y =   718.335  mm,	Z =  -195.557  mm,
	W =  -106.927 deg,	P =   -14.148 deg,	R =  -121.193 deg
};
P[60]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1296.720  mm,	Y =   712.599  mm,	Z =  -194.513  mm,
	W =  -106.269 deg,	P =   -14.066 deg,	R =  -125.698 deg
};
P[61]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1290.018  mm,	Y =   702.081  mm,	Z =  -193.013  mm,
	W =  -105.781 deg,	P =   -13.988 deg,	R =  -130.143 deg
};
P[62]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1283.765  mm,	Y =   693.928  mm,	Z =  -192.233  mm,
	W =  -105.502 deg,	P =   -13.914 deg,	R =  -134.519 deg
};
P[63]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1278.045  mm,	Y =   687.716  mm,	Z =  -191.884  mm,
	W =  -105.437 deg,	P =   -13.849 deg,	R =  -138.629 deg
};
P[64]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1270.476  mm,	Y =   680.655  mm,	Z =  -191.738  mm,
	W =  -105.429 deg,	P =   -13.831 deg,	R =  -139.837 deg
};
P[65]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1263.007  mm,	Y =   674.111  mm,	Z =  -191.864  mm,
	W =  -105.443 deg,	P =   -13.863 deg,	R =  -137.727 deg
};
P[66]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1253.254  mm,	Y =   665.886  mm,	Z =  -192.131  mm,
	W =  -105.373 deg,	P =   -13.729 deg,	R =  -147.436 deg
};
P[67]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1245.955  mm,	Y =   660.853  mm,	Z =  -192.305  mm,
	W =  -105.298 deg,	P =   -13.637 deg,	R =  -156.529 deg
};
P[68]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1236.617  mm,	Y =   655.702  mm,	Z =  -192.587  mm,
	W =  -105.277 deg,	P =   -13.618 deg,	R =  -158.976 deg
};
P[69]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1228.299  mm,	Y =   652.245  mm,	Z =  -192.828  mm,
	W =  -105.241 deg,	P =   -13.592 deg,	R =  -162.969 deg
};
P[70]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1216.140  mm,	Y =   648.416  mm,	Z =  -193.194  mm,
	W =  -105.203 deg,	P =   -13.573 deg,	R =  -167.022 deg
};
P[71]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1207.336  mm,	Y =   646.409  mm,	Z =  -193.448  mm,
	W =  -105.159 deg,	P =   -13.560 deg,	R =  -171.569 deg
};
P[72]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1198.185  mm,	Y =   644.974  mm,	Z =  -193.714  mm,
	W =  -105.113 deg,	P =   -13.556 deg,	R =  -176.312 deg
};
P[73]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1186.497  mm,	Y =   644.119  mm,	Z =  -194.063  mm,
	W =  -105.068 deg,	P =   -13.561 deg,	R =   179.213 deg
};
P[74]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1178.090  mm,	Y =   644.177  mm,	Z =  -194.315  mm,
	W =  -105.038 deg,	P =   -13.569 deg,	R =   176.231 deg
};
P[75]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1166.680  mm,	Y =   644.943  mm,	Z =  -194.708  mm,
	W =  -105.207 deg,	P =   -13.572 deg,	R =   175.290 deg
};
P[76]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1156.148  mm,	Y =   646.234  mm,	Z =  -195.573  mm,
	W =  -107.012 deg,	P =   -13.569 deg,	R =   174.537 deg
};
P[77]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1146.398  mm,	Y =   647.869  mm,	Z =  -198.700  mm,
	W =  -109.414 deg,	P =   -13.538 deg,	R =   174.483 deg
};
P[78]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1135.735  mm,	Y =   650.361  mm,	Z =  -206.144  mm,
	W =  -112.196 deg,	P =   -13.466 deg,	R =   175.323 deg
};
P[79]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1127.749  mm,	Y =   653.119  mm,	Z =  -216.251  mm,
	W =  -114.872 deg,	P =   -13.369 deg,	R =   175.422 deg
};
P[80]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1122.074  mm,	Y =   656.210  mm,	Z =  -224.033  mm,
	W =  -120.114 deg,	P =   -13.109 deg,	R =   172.293 deg
};
P[81]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1117.041  mm,	Y =   660.103  mm,	Z =  -230.984  mm,
	W =  -126.811 deg,	P =   -12.622 deg,	R =   167.800 deg
};
P[82]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1111.179  mm,	Y =   663.031  mm,	Z =  -234.487  mm,
	W =  -119.561 deg,	P =   -13.285 deg,	R =   157.806 deg
};
P[83]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1103.719  mm,	Y =   665.639  mm,	Z =  -235.930  mm,
	W =  -107.219 deg,	P =   -13.741 deg,	R =   154.408 deg
};
P[84]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1093.706  mm,	Y =   669.850  mm,	Z =  -236.758  mm,
	W =  -105.746 deg,	P =   -13.749 deg,	R =   154.142 deg
};
P[85]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1087.516  mm,	Y =   672.966  mm,	Z =  -237.175  mm,
	W =  -105.804 deg,	P =   -13.784 deg,	R =   151.506 deg
};
P[86]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1076.222  mm,	Y =   679.688  mm,	Z =  -237.932  mm,
	W =  -105.885 deg,	P =   -13.838 deg,	R =   147.739 deg
};
P[87]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1065.850  mm,	Y =   687.245  mm,	Z =  -238.619  mm,
	W =  -105.988 deg,	P =   -13.918 deg,	R =   142.681 deg
};
P[88]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1060.757  mm,	Y =   691.496  mm,	Z =  -238.926  mm,
	W =  -106.082 deg,	P =   -14.006 deg,	R =   137.688 deg
};
P[89]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1052.219  mm,	Y =   699.373  mm,	Z =  -239.444  mm,
	W =  -106.129 deg,	P =   -14.056 deg,	R =   135.015 deg
};
P[90]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1044.649  mm,	Y =   707.646  mm,	Z =  -239.958  mm,
	W =  -106.185 deg,	P =   -14.122 deg,	R =   131.632 deg
};
P[91]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1037.914  mm,	Y =   716.480  mm,	Z =  -240.417  mm,
	W =  -106.269 deg,	P =   -14.239 deg,	R =   125.999 deg
};
P[92]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1034.511  mm,	Y =   721.756  mm,	Z =  -240.629  mm,
	W =  -106.343 deg,	P =   -14.367 deg,	R =   120.226 deg
};
P[93]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1029.557  mm,	Y =   730.632  mm,	Z =  -240.934  mm,
	W =  -106.384 deg,	P =   -14.458 deg,	R =   116.261 deg
};
P[94]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1024.947  mm,	Y =   741.122  mm,	Z =  -241.229  mm,
	W =  -106.433 deg,	P =   -14.556 deg,	R =   111.957 deg
};
P[95]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1021.665  mm,	Y =   751.207  mm,	Z =  -241.473  mm,
	W =  -106.465 deg,	P =   -14.714 deg,	R =   105.666 deg
};
P[96]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1019.055  mm,	Y =   762.772  mm,	Z =  -241.690  mm,
	W =  -106.480 deg,	P =   -14.798 deg,	R =   102.262 deg
};
P[97]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1017.916  mm,	Y =   771.072  mm,	Z =  -241.762  mm,
	W =  -106.494 deg,	P =   -14.935 deg,	R =    96.828 deg
};
P[98]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1017.370  mm,	Y =   777.973  mm,	Z =  -241.792  mm,
	W =  -106.495 deg,	P =   -15.000 deg,	R =    94.234 deg
};
P[99]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =   651.995  mm,	Y =   781.694  mm,	Z =  -345.952  mm,
	W =  -106.495 deg,	P =   -15.000 deg,	R =    94.234 deg
};
/END
