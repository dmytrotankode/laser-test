/PROG  DISTI_CADC_V8
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "WeldPRO Auto-Gen";
PROG_SIZE	= 7125;
CREATE		= DATE 26-07-31  TIME 14:01:48;
MODIFIED	= DATE 26-07-31  TIME 15:02:18;
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
	X =  1018.040  mm,	Y =   777.038  mm,	Z =  -243.059  mm,
	W =  -106.497 deg,	P =   -14.995 deg,	R =    94.216 deg
};
P[3]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1017.891  mm,	Y =   779.774  mm,	Z =  -243.081  mm,
	W =  -106.501 deg,	P =   -14.998 deg,	R =    94.232 deg
};
P[4]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1017.828  mm,	Y =   788.177  mm,	Z =  -243.120  mm,
	W =  -106.497 deg,	P =   -15.098 deg,	R =    90.375 deg
};
P[5]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1018.457  mm,	Y =   798.142  mm,	Z =  -243.115  mm,
	W =  -106.481 deg,	P =   -15.217 deg,	R =    85.597 deg
};
P[6]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1019.794  mm,	Y =   807.777  mm,	Z =  -243.054  mm,
	W =  -106.456 deg,	P =   -15.334 deg,	R =    80.807 deg
};
P[7]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1021.999  mm,	Y =   817.759  mm,	Z =  -242.927  mm,
	W =  -106.423 deg,	P =   -15.449 deg,	R =    76.083 deg
};
P[8]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1025.014  mm,	Y =   827.396  mm,	Z =  -242.736  mm,
	W =  -106.378 deg,	P =   -15.565 deg,	R =    71.217 deg
};
P[9]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1028.845  mm,	Y =   836.678  mm,	Z =  -242.481  mm,
	W =  -106.322 deg,	P =   -15.679 deg,	R =    66.207 deg
};
P[10]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1033.496  mm,	Y =   845.605  mm,	Z =  -242.161  mm,
	W =  -106.254 deg,	P =   -15.791 deg,	R =    61.015 deg
};
P[11]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1038.937  mm,	Y =   854.120  mm,	Z =  -241.777  mm,
	W =  -106.179 deg,	P =   -15.896 deg,	R =    55.983 deg
};
P[12]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1045.487  mm,	Y =   862.622  mm,	Z =  -241.303  mm,
	W =  -106.096 deg,	P =   -15.986 deg,	R =    51.162 deg
};
P[13]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1053.505  mm,	Y =   871.285  mm,	Z =  -240.711  mm,
	W =  -106.012 deg,	P =   -16.066 deg,	R =    46.632 deg
};
P[14]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1058.232  mm,	Y =   875.706  mm,	Z =  -240.373  mm,
	W =  -105.919 deg,	P =   -16.142 deg,	R =    41.952 deg
};
P[15]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1067.568  mm,	Y =   883.475  mm,	Z =  -239.658  mm,
	W =  -105.870 deg,	P =   -16.177 deg,	R =    39.609 deg
};
P[16]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1073.060  mm,	Y =   887.486  mm,	Z =  -239.255  mm,
	W =  -105.777 deg,	P =   -16.235 deg,	R =    35.365 deg
};
P[17]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1083.266  mm,	Y =   894.032  mm,	Z =  -238.480  mm,
	W =  -105.677 deg,	P =   -16.289 deg,	R =    30.964 deg
};
P[18]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1093.992  mm,	Y =   899.687  mm,	Z =  -237.657  mm,
	W =  -105.579 deg,	P =   -16.333 deg,	R =    26.830 deg
};
P[19]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1099.525  mm,	Y =   902.174  mm,	Z =  -237.227  mm,
	W =  -105.535 deg,	P =   -16.344 deg,	R =    25.007 deg
};
P[20]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1110.017  mm,	Y =   905.648  mm,	Z =  -237.358  mm,
	W =  -116.027 deg,	P =   -16.063 deg,	R =    30.267 deg
};
P[21]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1118.996  mm,	Y =   908.793  mm,	Z =  -234.416  mm,
	W =  -126.877 deg,	P =   -15.356 deg,	R =    25.893 deg
};
P[22]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1122.518  mm,	Y =   911.354  mm,	Z =  -230.430  mm,
	W =  -121.184 deg,	P =   -15.973 deg,	R =    18.444 deg
};
P[23]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1128.395  mm,	Y =   915.285  mm,	Z =  -222.328  mm,
	W =  -115.329 deg,	P =   -16.208 deg,	R =    11.788 deg
};
P[24]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1135.828  mm,	Y =   918.438  mm,	Z =  -211.777  mm,
	W =  -112.639 deg,	P =   -16.315 deg,	R =     9.714 deg
};
P[25]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1142.076  mm,	Y =   920.284  mm,	Z =  -204.427  mm,
	W =  -110.015 deg,	P =   -16.386 deg,	R =     9.649 deg
};
P[26]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1146.700  mm,	Y =   921.290  mm,	Z =  -200.853  mm,
	W =  -108.552 deg,	P =   -16.418 deg,	R =     8.950 deg
};
P[27]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1160.295  mm,	Y =   923.330  mm,	Z =  -195.206  mm,
	W =  -105.409 deg,	P =   -16.443 deg,	R =     6.805 deg
};
P[28]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1171.769  mm,	Y =   924.323  mm,	Z =  -194.260  mm,
	W =  -104.866 deg,	P =   -16.444 deg,	R =     5.597 deg
};
P[29]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1177.981  mm,	Y =   924.616  mm,	Z =  -193.988  mm,
	W =  -104.887 deg,	P =   -16.444 deg,	R =     3.523 deg
};
P[30]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1187.399  mm,	Y =   924.642  mm,	Z =  -193.582  mm,
	W =  -104.930 deg,	P =   -16.439 deg,	R =     -.729 deg
};
P[31]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1199.484  mm,	Y =   923.714  mm,	Z =  -193.054  mm,
	W =  -104.979 deg,	P =   -16.424 deg,	R =    -5.541 deg
};
P[32]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1205.491  mm,	Y =   922.778  mm,	Z =  -192.811  mm,
	W =  -105.028 deg,	P =   -16.400 deg,	R =   -10.259 deg
};
P[33]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1216.524  mm,	Y =   920.324  mm,	Z =  -192.319  mm,
	W =  -105.070 deg,	P =   -16.371 deg,	R =   -14.490 deg
};
P[34]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1226.959  mm,	Y =   917.094  mm,	Z =  -191.850  mm,
	W =  -105.112 deg,	P =   -16.334 deg,	R =   -18.515 deg
};
P[35]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1234.531  mm,	Y =   914.133  mm,	Z =  -191.522  mm,
	W =  -105.158 deg,	P =   -16.285 deg,	R =   -23.051 deg
};
P[36]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1242.690  mm,	Y =   910.198  mm,	Z =  -191.177  mm,
	W =  -105.219 deg,	P =   -16.204 deg,	R =   -29.417 deg
};
P[37]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1250.278  mm,	Y =   905.539  mm,	Z =  -190.883  mm,
	W =  -105.311 deg,	P =   -16.047 deg,	R =   -39.415 deg
};
P[38]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1258.348  mm,	Y =   899.389  mm,	Z =  -190.472  mm,
	W =  -105.307 deg,	P =   -16.055 deg,	R =   -38.974 deg
};
P[39]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1266.428  mm,	Y =   891.934  mm,	Z =  -190.056  mm,
	W =  -105.302 deg,	P =   -16.063 deg,	R =   -38.625 deg
};
P[40]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1272.487  mm,	Y =   886.194  mm,	Z =  -189.875  mm,
	W =  -105.469 deg,	P =   -15.944 deg,	R =   -44.976 deg
};
P[41]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1278.072  mm,	Y =   880.879  mm,	Z =  -189.824  mm,
	W =  -105.661 deg,	P =   -15.890 deg,	R =   -47.714 deg
};
P[42]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1284.247  mm,	Y =   874.197  mm,	Z =  -190.009  mm,
	W =  -106.210 deg,	P =   -15.792 deg,	R =   -52.259 deg
};
P[43]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1290.135  mm,	Y =   866.573  mm,	Z =  -190.503  mm,
	W =  -106.927 deg,	P =   -15.688 deg,	R =   -56.663 deg
};
P[44]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1295.266  mm,	Y =   858.702  mm,	Z =  -191.299  mm,
	W =  -107.603 deg,	P =   -15.597 deg,	R =   -60.244 deg
};
P[45]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1299.879  mm,	Y =   850.481  mm,	Z =  -192.430  mm,
	W =  -108.271 deg,	P =   -15.504 deg,	R =   -63.686 deg
};
P[46]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1305.291  mm,	Y =   838.979  mm,	Z =  -194.519  mm,
	W =  -109.143 deg,	P =   -15.377 deg,	R =   -68.203 deg
};
P[47]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1307.920  mm,	Y =   832.187  mm,	Z =  -195.836  mm,
	W =  -109.899 deg,	P =   -15.253 deg,	R =   -72.505 deg
};
P[48]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1311.308  mm,	Y =   821.937  mm,	Z =  -197.525  mm,
	W =  -110.273 deg,	P =   -15.181 deg,	R =   -74.982 deg
};
P[49]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1312.815  mm,	Y =   816.097  mm,	Z =  -198.320  mm,
	W =  -110.635 deg,	P =   -14.305 deg,	R =   -78.232 deg
};
P[50]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1315.073  mm,	Y =   804.438  mm,	Z =  -199.508  mm,
	W =  -111.054 deg,	P =   -14.769 deg,	R =   -83.164 deg
};
P[51]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.161  mm,	Y =   794.461  mm,	Z =  -200.126  mm,
	W =  -111.189 deg,	P =   -15.305 deg,	R =   -88.309 deg
};
P[52]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.563  mm,	Y =   785.485  mm,	Z =  -200.379  mm,
	W =  -111.129 deg,	P =   -15.645 deg,	R =   -91.614 deg
};
P[53]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.503  mm,	Y =   780.057  mm,	Z =  -200.390  mm,
	W =  -110.924 deg,	P =   -15.048 deg,	R =   -94.524 deg
};
P[54]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1315.529  mm,	Y =   767.583  mm,	Z =  -200.005  mm,
	W =  -110.276 deg,	P =   -14.535 deg,	R =  -100.837 deg
};
P[55]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1313.943  mm,	Y =   757.668  mm,	Z =  -199.297  mm,
	W =  -109.635 deg,	P =   -14.447 deg,	R =  -105.265 deg
};
P[56]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1311.692  mm,	Y =   748.074  mm,	Z =  -198.284  mm,
	W =  -109.082 deg,	P =   -14.382 deg,	R =  -108.626 deg
};
P[57]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1308.749  mm,	Y =   738.689  mm,	Z =  -196.962  mm,
	W =  -108.349 deg,	P =   -14.302 deg,	R =  -112.873 deg
};
P[58]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1304.735  mm,	Y =   728.503  mm,	Z =  -195.164  mm,
	W =  -107.748 deg,	P =   -14.239 deg,	R =  -116.265 deg
};
P[59]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1301.718  mm,	Y =   722.146  mm,	Z =  -193.853  mm,
	W =  -106.924 deg,	P =   -14.148 deg,	R =  -121.191 deg
};
P[60]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1295.747  mm,	Y =   711.246  mm,	Z =  -191.764  mm,
	W =  -106.269 deg,	P =   -14.066 deg,	R =  -125.698 deg
};
P[61]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1292.200  mm,	Y =   705.693  mm,	Z =  -190.933  mm,
	W =  -105.781 deg,	P =   -13.988 deg,	R =  -130.143 deg
};
P[62]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1285.236  mm,	Y =   696.057  mm,	Z =  -189.869  mm,
	W =  -105.526 deg,	P =   -13.913 deg,	R =  -134.520 deg
};
P[63]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1279.424  mm,	Y =   689.370  mm,	Z =  -189.435  mm,
	W =  -105.437 deg,	P =   -13.849 deg,	R =  -138.629 deg
};
P[64]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1271.239  mm,	Y =   681.481  mm,	Z =  -189.254  mm,
	W =  -105.429 deg,	P =   -13.831 deg,	R =  -139.837 deg
};
P[65]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1261.536  mm,	Y =   673.175  mm,	Z =  -189.491  mm,
	W =  -105.443 deg,	P =   -13.863 deg,	R =  -137.727 deg
};
P[66]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1255.220  mm,	Y =   667.961  mm,	Z =  -189.703  mm,
	W =  -105.373 deg,	P =   -13.729 deg,	R =  -147.436 deg
};
P[67]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1246.913  mm,	Y =   661.856  mm,	Z =  -189.999  mm,
	W =  -105.298 deg,	P =   -13.637 deg,	R =  -156.529 deg
};
P[68]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1239.300  mm,	Y =   657.219  mm,	Z =  -190.314  mm,
	W =  -105.277 deg,	P =   -13.618 deg,	R =  -158.977 deg
};
P[69]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1230.289  mm,	Y =   653.125  mm,	Z =  -190.687  mm,
	W =  -105.241 deg,	P =   -13.592 deg,	R =  -162.969 deg
};
P[70]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1218.316  mm,	Y =   649.083  mm,	Z =  -191.200  mm,
	W =  -105.201 deg,	P =   -13.569 deg,	R =  -167.030 deg
};
P[71]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1209.645  mm,	Y =   646.952  mm,	Z =  -191.560  mm,
	W =  -105.159 deg,	P =   -13.560 deg,	R =  -171.569 deg
};
P[72]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1200.632  mm,	Y =   645.351  mm,	Z =  -191.937  mm,
	W =  -105.113 deg,	P =   -13.556 deg,	R =  -176.312 deg
};
P[73]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1188.036  mm,	Y =   644.168  mm,	Z =  -192.487  mm,
	W =  -105.068 deg,	P =   -13.561 deg,	R =   179.213 deg
};
P[74]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1176.319  mm,	Y =   644.213  mm,	Z =  -193.012  mm,
	W =  -105.038 deg,	P =   -13.569 deg,	R =   176.231 deg
};
P[75]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1164.926  mm,	Y =   645.118  mm,	Z =  -193.574  mm,
	W =  -105.207 deg,	P =   -13.572 deg,	R =   175.290 deg
};
P[76]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1158.587  mm,	Y =   645.963  mm,	Z =  -194.162  mm,
	W =  -107.012 deg,	P =   -13.569 deg,	R =   174.537 deg
};
P[77]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1148.794  mm,	Y =   647.552  mm,	Z =  -196.304  mm,
	W =  -109.414 deg,	P =   -13.538 deg,	R =   174.483 deg
};
P[78]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1140.468  mm,	Y =   649.329  mm,	Z =  -200.611  mm,
	W =  -112.196 deg,	P =   -13.466 deg,	R =   175.322 deg
};
P[79]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1133.230  mm,	Y =   651.346  mm,	Z =  -206.798  mm,
	W =  -114.872 deg,	P =   -13.369 deg,	R =   175.422 deg
};
P[80]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1125.798  mm,	Y =   654.267  mm,	Z =  -216.502  mm,
	W =  -120.114 deg,	P =   -13.109 deg,	R =   172.292 deg
};
P[81]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1119.128  mm,	Y =   658.426  mm,	Z =  -226.021  mm,
	W =  -126.809 deg,	P =   -12.620 deg,	R =   167.791 deg
};
P[82]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1111.797  mm,	Y =   662.733  mm,	Z =  -232.800  mm,
	W =  -119.561 deg,	P =   -13.285 deg,	R =   157.805 deg
};
P[83]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1103.866  mm,	Y =   665.996  mm,	Z =  -235.418  mm,
	W =  -107.325 deg,	P =   -13.741 deg,	R =   154.436 deg
};
P[84]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1092.882  mm,	Y =   670.775  mm,	Z =  -236.713  mm,
	W =  -105.746 deg,	P =   -13.749 deg,	R =   154.142 deg
};
P[85]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1086.736  mm,	Y =   673.962  mm,	Z =  -237.224  mm,
	W =  -105.804 deg,	P =   -13.784 deg,	R =   151.506 deg
};
P[86]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1075.535  mm,	Y =   680.817  mm,	Z =  -238.158  mm,
	W =  -105.885 deg,	P =   -13.838 deg,	R =   147.739 deg
};
P[87]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1069.940  mm,	Y =   684.858  mm,	Z =  -238.601  mm,
	W =  -105.988 deg,	P =   -13.918 deg,	R =   142.681 deg
};
P[88]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1060.221  mm,	Y =   692.801  mm,	Z =  -239.391  mm,
	W =  -106.083 deg,	P =   -14.001 deg,	R =   137.677 deg
};
P[89]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1051.788  mm,	Y =   700.778  mm,	Z =  -240.052  mm,
	W =  -106.129 deg,	P =   -14.056 deg,	R =   135.014 deg
};
P[90]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1044.325  mm,	Y =   709.141  mm,	Z =  -240.694  mm,
	W =  -106.186 deg,	P =   -14.117 deg,	R =   131.622 deg
};
P[91]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1040.638  mm,	Y =   713.932  mm,	Z =  -241.000  mm,
	W =  -106.269 deg,	P =   -14.234 deg,	R =   126.207 deg
};
P[92]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1034.356  mm,	Y =   723.361  mm,	Z =  -241.534  mm,
	W =  -106.343 deg,	P =   -14.367 deg,	R =   120.225 deg
};
P[93]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1029.538  mm,	Y =   732.229  mm,	Z =  -241.931  mm,
	W =  -106.383 deg,	P =   -14.448 deg,	R =   116.672 deg
};
P[94]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1025.030  mm,	Y =   742.838  mm,	Z =  -242.318  mm,
	W =  -106.433 deg,	P =   -14.556 deg,	R =   111.957 deg
};
P[95]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1021.867  mm,	Y =   752.959  mm,	Z =  -242.631  mm,
	W =  -106.465 deg,	P =   -14.714 deg,	R =   105.666 deg
};
P[96]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1019.399  mm,	Y =   764.554  mm,	Z =  -242.915  mm,
	W =  -106.480 deg,	P =   -14.798 deg,	R =   102.261 deg
};
P[97]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1018.355  mm,	Y =   772.866  mm,	Z =  -243.024  mm,
	W =  -106.494 deg,	P =   -14.935 deg,	R =    96.827 deg
};
P[98]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1017.891  mm,	Y =   779.773  mm,	Z =  -243.081  mm,
	W =  -106.501 deg,	P =   -15.000 deg,	R =    94.235 deg
};
P[99]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =   651.995  mm,	Y =   781.694  mm,	Z =  -345.952  mm,
	W =  -106.495 deg,	P =   -15.000 deg,	R =    94.234 deg
};
/END
