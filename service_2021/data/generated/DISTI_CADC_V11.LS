/PROG  DISTI_CADC_V11
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "WeldPRO Auto-Gen";
PROG_SIZE	= 7109;
CREATE		= DATE 26-07-22  TIME 10:34:12;
MODIFIED	= DATE 26-07-22  TIME 10:52:32;
FILE_NAME	= DISTI_CA;
VERSION		= 0;
LINE_COUNT	= 113;
MEMORY_SIZE	= 7429;
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
   2:  !Tor XL_176 _2, Feature1 ;
   3:   ;
   4:  UFRAME_NUM=2 ;
   5:  UTOOL_NUM=2 ;
   6:L P[1] 100mm/sec FINE    ;
   7:   ;
   8:  !Segment1 ;
   9:L P[2] 100mm/sec FINE    ;
  10:  CALL LASER_OFF    ;
  11:   ;
  12:L P[99] R[23:moving]mm/sec CNT100    ;
  13:   ;
  14:L P[3] R[23:moving]mm/sec CNT100    ;
  15:L P[4] R[23:moving]mm/sec CNT100    ;
  16:L P[5] R[23:moving]mm/sec CNT100    ;
  17:L P[6] R[23:moving]mm/sec CNT100    ;
  18:L P[7] R[23:moving]mm/sec CNT100    ;
  19:L P[8] R[23:moving]mm/sec CNT100    ;
  20:L P[9] R[23:moving]mm/sec CNT100    ;
  21:L P[10] R[23:moving]mm/sec CNT100    ;
  22:L P[11] R[23:moving]mm/sec CNT100    ;
  23:L P[12] R[23:moving]mm/sec CNT100    ;
  24:L P[13] R[23:moving]mm/sec CNT100    ;
  25:L P[14] R[23:moving]mm/sec CNT100    ;
  26:L P[15] R[23:moving]mm/sec CNT100    ;
  27:L P[16] R[23:moving]mm/sec CNT100    ;
  28:L P[17] R[23:moving]mm/sec CNT100    ;
  29:L P[18] R[23:moving]mm/sec CNT100    ;
  30:L P[19] R[23:moving]mm/sec CNT100    ;
  31:L P[20] R[23:moving]mm/sec CNT100    ;
  32:L P[21] R[23:moving]mm/sec CNT100    ;
  33:L P[22] R[23:moving]mm/sec CNT100    ;
  34:L P[23] R[23:moving]mm/sec CNT100    ;
  35:L P[24] R[23:moving]mm/sec CNT100    ;
  36:L P[25] R[23:moving]mm/sec CNT100    ;
  37:L P[26] R[23:moving]mm/sec CNT100    ;
  38:L P[27] R[23:moving]mm/sec CNT100    ;
  39:L P[28] R[23:moving]mm/sec CNT100    ;
  40:L P[29] R[23:moving]mm/sec CNT100    ;
  41:L P[30] R[23:moving]mm/sec CNT100    ;
  42:L P[31] R[23:moving]mm/sec CNT100    ;
  43:L P[32] R[23:moving]mm/sec CNT100    ;
  44:L P[33] R[23:moving]mm/sec CNT100    ;
  45:L P[34] R[23:moving]mm/sec CNT100    ;
  46:L P[35] R[23:moving]mm/sec CNT100    ;
  47:L P[36] R[23:moving]mm/sec CNT100    ;
  48:L P[37] R[23:moving]mm/sec CNT100    ;
  49:L P[38] R[23:moving]mm/sec CNT100    ;
  50:L P[39] R[23:moving]mm/sec CNT100    ;
  51:L P[40] R[23:moving]mm/sec CNT100    ;
  52:L P[41] R[23:moving]mm/sec CNT100    ;
  53:L P[42] R[23:moving]mm/sec CNT100    ;
  54:L P[43] R[23:moving]mm/sec CNT100    ;
  55:L P[44] R[23:moving]mm/sec CNT100    ;
  56:L P[45] R[23:moving]mm/sec CNT100    ;
  57:L P[46] R[23:moving]mm/sec CNT100    ;
  58:L P[47] R[23:moving]mm/sec CNT100    ;
  59:L P[48] R[23:moving]mm/sec CNT100    ;
  60:L P[49] R[23:moving]mm/sec CNT100    ;
  61:L P[50] R[23:moving]mm/sec CNT100    ;
  62:L P[51] R[23:moving]mm/sec CNT100    ;
  63:L P[52] R[23:moving]mm/sec CNT100    ;
  64:L P[53] R[23:moving]mm/sec CNT100    ;
  65:L P[54] R[23:moving]mm/sec CNT100    ;
  66:L P[55] R[23:moving]mm/sec CNT100    ;
  67:L P[56] R[23:moving]mm/sec CNT100    ;
  68:L P[57] R[23:moving]mm/sec CNT100    ;
  69:L P[58] R[23:moving]mm/sec CNT100    ;
  70:L P[59] R[23:moving]mm/sec CNT100    ;
  71:L P[60] R[23:moving]mm/sec CNT100    ;
  72:L P[61] R[23:moving]mm/sec CNT100    ;
  73:L P[62] R[23:moving]mm/sec CNT100    ;
  74:L P[63] R[23:moving]mm/sec CNT100    ;
  75:L P[64] R[23:moving]mm/sec CNT100    ;
  76:L P[65] R[23:moving]mm/sec CNT100    ;
  77:L P[66] R[23:moving]mm/sec CNT100    ;
  78:L P[67] R[23:moving]mm/sec CNT100    ;
  79:L P[68] R[23:moving]mm/sec CNT100    ;
  80:L P[69] R[23:moving]mm/sec CNT100    ;
  81:L P[70] R[23:moving]mm/sec CNT100    ;
  82:L P[71] R[23:moving]mm/sec CNT100    ;
  83:L P[72] R[23:moving]mm/sec CNT100    ;
  84:L P[73] R[23:moving]mm/sec CNT100    ;
  85:L P[74] R[23:moving]mm/sec CNT100    ;
  86:L P[75] R[23:moving]mm/sec CNT100    ;
  87:L P[76] R[23:moving]mm/sec CNT100    ;
  88:L P[77] R[23:moving]mm/sec CNT100    ;
  89:L P[78] R[23:moving]mm/sec CNT100    ;
  90:L P[79] R[23:moving]mm/sec CNT100    ;
  91:L P[80] R[23:moving]mm/sec CNT100    ;
  92:L P[81] R[23:moving]mm/sec CNT100    ;
  93:L P[82] R[23:moving]mm/sec CNT100    ;
  94:L P[83] R[23:moving]mm/sec CNT100    ;
  95:L P[84] R[23:moving]mm/sec CNT100    ;
  96:L P[85] R[23:moving]mm/sec CNT100    ;
  97:L P[86] R[23:moving]mm/sec CNT100    ;
  98:L P[87] R[23:moving]mm/sec CNT100    ;
  99:L P[88] R[23:moving]mm/sec CNT100    ;
 100:L P[89] R[23:moving]mm/sec CNT100    ;
 101:L P[90] R[23:moving]mm/sec CNT100    ;
 102:L P[91] R[23:moving]mm/sec CNT100    ;
 103:L P[92] R[23:moving]mm/sec CNT100    ;
 104:L P[93] R[23:moving]mm/sec CNT100    ;
 105:L P[94] R[23:moving]mm/sec CNT100    ;
 106:L P[95] R[23:moving]mm/sec CNT100    ;
 107:L P[96] R[23:moving]mm/sec CNT100    ;
 108:L P[97] R[23:moving]mm/sec FINE    ;
 109:  CALL LASER_OFF    ;
 110:   ;
 111:  !Feature Retreat ;
 112:L P[98] 100mm/sec FINE    ;
 113:  CALL ROTATE    ;
/POS
P[1]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =   927.346  mm,	Y =   856.354  mm,	Z =  -244.034  mm,
	W =  -106.482 deg,	P =   -15.198 deg,	R =    86.345 deg
};
P[2]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1017.558  mm,	Y =   791.000  mm,	Z =  -243.062  mm,
	W =  -106.491 deg,	P =   -15.193 deg,	R =    86.327 deg
};
P[3]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1017.817  mm,	Y =   795.990  mm,	Z =  -243.232  mm,
	W =  -106.495 deg,	P =   -15.194 deg,	R =    86.332 deg
};
P[4]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1021.919  mm,	Y =   819.823  mm,	Z =  -243.777  mm,
	W =  -106.425 deg,	P =   -15.445 deg,	R =    76.281 deg
};
P[5]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1025.018  mm,	Y =   829.426  mm,	Z =  -243.892  mm,
	W =  -106.381 deg,	P =   -15.559 deg,	R =    71.464 deg
};
P[6]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1029.026  mm,	Y =   838.853  mm,	Z =  -243.934  mm,
	W =  -106.310 deg,	P =   -15.698 deg,	R =    65.272 deg
};
P[7]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1033.705  mm,	Y =   847.632  mm,	Z =  -243.910  mm,
	W =  -106.251 deg,	P =   -15.795 deg,	R =    60.811 deg
};
P[8]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1039.226  mm,	Y =   856.101  mm,	Z =  -243.814  mm,
	W =  -106.174 deg,	P =   -15.897 deg,	R =    55.794 deg
};
P[9]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1045.860  mm,	Y =   864.550  mm,	Z =  -243.637  mm,
	W =  -106.090 deg,	P =   -15.988 deg,	R =    50.970 deg
};
P[10]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1053.858  mm,	Y =   873.049  mm,	Z =  -243.365  mm,
	W =  -106.027 deg,	P =   -16.056 deg,	R =    47.314 deg
};
P[11]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1058.579  mm,	Y =   877.412  mm,	Z =  -243.184  mm,
	W =  -105.939 deg,	P =   -16.126 deg,	R =    42.935 deg
};
P[12]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1068.108  mm,	Y =   885.197  mm,	Z =  -242.773  mm,
	W =  -105.872 deg,	P =   -16.175 deg,	R =    39.733 deg
};
P[13]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1073.639  mm,	Y =   889.171  mm,	Z =  -242.523  mm,
	W =  -105.783 deg,	P =   -16.243 deg,	R =    35.484 deg
};
P[14]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1083.912  mm,	Y =   895.642  mm,	Z =  -242.016  mm,
	W =  -105.683 deg,	P =   -16.290 deg,	R =    31.072 deg
};
P[15]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1094.699  mm,	Y =   901.220  mm,	Z =  -241.438  mm,
	W =  -105.584 deg,	P =   -16.329 deg,	R =    26.914 deg
};
P[16]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1100.258  mm,	Y =   903.665  mm,	Z =  -241.124  mm,
	W =  -105.545 deg,	P =   -16.341 deg,	R =    25.103 deg
};
P[17]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1111.769  mm,	Y =   907.498  mm,	Z =  -241.043  mm,
	W =  -115.468 deg,	P =   -16.090 deg,	R =    30.046 deg
};
P[18]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1119.764  mm,	Y =   910.284  mm,	Z =  -238.672  mm,
	W =  -126.721 deg,	P =   -15.366 deg,	R =    26.538 deg
};
P[19]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1123.647  mm,	Y =   913.105  mm,	Z =  -234.531  mm,
	W =  -119.393 deg,	P =   -15.981 deg,	R =    16.221 deg
};
P[20]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1129.393  mm,	Y =   917.038  mm,	Z =  -226.839  mm,
	W =  -115.329 deg,	P =   -16.208 deg,	R =    11.788 deg
};
P[21]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1136.937  mm,	Y =   920.439  mm,	Z =  -216.449  mm,
	W =  -112.690 deg,	P =   -16.313 deg,	R =     9.687 deg
};
P[22]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1143.244  mm,	Y =   922.441  mm,	Z =  -209.206  mm,
	W =  -110.089 deg,	P =   -16.384 deg,	R =     9.676 deg
};
P[23]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1151.480  mm,	Y =   924.191  mm,	Z =  -203.614  mm,
	W =  -107.448 deg,	P =   -16.428 deg,	R =     8.430 deg
};
P[24]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1162.955  mm,	Y =   925.718  mm,	Z =  -199.992  mm,
	W =  -105.451 deg,	P =   -16.442 deg,	R =     6.850 deg
};
P[25]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1173.029  mm,	Y =   926.485  mm,	Z =  -199.362  mm,
	W =  -104.865 deg,	P =   -16.444 deg,	R =     5.674 deg
};
P[26]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1184.219  mm,	Y =   926.785  mm,	Z =  -198.942  mm,
	W =  -104.885 deg,	P =   -16.444 deg,	R =     3.732 deg
};
P[27]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1192.686  mm,	Y =   926.477  mm,	Z =  -198.630  mm,
	W =  -104.928 deg,	P =   -16.440 deg,	R =     -.482 deg
};
P[28]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1200.719  mm,	Y =   925.659  mm,	Z =  -198.324  mm,
	W =  -104.977 deg,	P =   -16.425 deg,	R =    -5.295 deg
};
P[29]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1211.889  mm,	Y =   923.631  mm,	Z =  -197.850  mm,
	W =  -105.026 deg,	P =   -16.401 deg,	R =   -10.039 deg
};
P[30]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1222.914  mm,	Y =   920.620  mm,	Z =  -197.341  mm,
	W =  -105.069 deg,	P =   -16.371 deg,	R =   -14.284 deg
};
P[31]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1231.660  mm,	Y =   917.515  mm,	Z =  -196.921  mm,
	W =  -105.112 deg,	P =   -16.334 deg,	R =   -18.515 deg
};
P[32]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1238.708  mm,	Y =   914.458  mm,	Z =  -196.574  mm,
	W =  -105.156 deg,	P =   -16.287 deg,	R =   -22.931 deg
};
P[33]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1247.875  mm,	Y =   909.549  mm,	Z =  -196.097  mm,
	W =  -105.219 deg,	P =   -16.204 deg,	R =   -29.417 deg
};
P[34]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1253.165  mm,	Y =   905.967  mm,	Z =  -195.825  mm,
	W =  -105.326 deg,	P =   -16.106 deg,	R =   -35.234 deg
};
P[35]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1259.422  mm,	Y =   900.875  mm,	Z =  -195.420  mm,
	W =  -105.307 deg,	P =   -16.055 deg,	R =   -38.974 deg
};
P[36]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1267.430  mm,	Y =   893.354  mm,	Z =  -194.821  mm,
	W =  -105.304 deg,	P =   -16.061 deg,	R =   -38.624 deg
};
P[37]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1276.157  mm,	Y =   885.042  mm,	Z =  -194.392  mm,
	W =  -105.460 deg,	P =   -15.949 deg,	R =   -44.737 deg
};
P[38]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1284.641  mm,	Y =   876.137  mm,	Z =  -194.282  mm,
	W =  -105.652 deg,	P =   -15.892 deg,	R =   -47.603 deg
};
P[39]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1290.529  mm,	Y =   868.471  mm,	Z =  -194.563  mm,
	W =  -106.194 deg,	P =   -15.794 deg,	R =   -52.149 deg
};
P[40]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1295.696  mm,	Y =   860.432  mm,	Z =  -195.163  mm,
	W =  -106.906 deg,	P =   -15.690 deg,	R =   -56.548 deg
};
P[41]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1300.268  mm,	Y =   852.148  mm,	Z =  -196.076  mm,
	W =  -107.559 deg,	P =   -15.603 deg,	R =   -60.015 deg
};
P[42]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1303.112  mm,	Y =   846.222  mm,	Z =  -196.919  mm,
	W =  -108.250 deg,	P =   -15.507 deg,	R =   -63.574 deg
};
P[43]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1308.190  mm,	Y =   833.827  mm,	Z =  -198.981  mm,
	W =  -109.123 deg,	P =   -15.380 deg,	R =   -68.091 deg
};
P[44]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1309.977  mm,	Y =   828.351  mm,	Z =  -199.789  mm,
	W =  -109.894 deg,	P =   -15.253 deg,	R =   -72.476 deg
};
P[45]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1313.017  mm,	Y =   817.391  mm,	Z =  -201.059  mm,
	W =  -110.258 deg,	P =   -15.184 deg,	R =   -74.873 deg
};
P[46]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1314.259  mm,	Y =   811.375  mm,	Z =  -201.578  mm,
	W =  -110.625 deg,	P =   -15.098 deg,	R =   -77.924 deg
};
P[47]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1315.808  mm,	Y =   800.545  mm,	Z =  -202.185  mm,
	W =  -111.046 deg,	P =   -14.958 deg,	R =   -82.908 deg
};
P[48]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.455  mm,	Y =   790.954  mm,	Z =  -202.365  mm,
	W =  -111.160 deg,	P =   -14.266 deg,	R =   -88.178 deg
};
P[49]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.465  mm,	Y =   781.240  mm,	Z =  -202.186  mm,
	W =  -111.104 deg,	P =   -14.627 deg,	R =   -91.603 deg
};
P[50]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1315.815  mm,	Y =   772.198  mm,	Z =  -201.701  mm,
	W =  -110.785 deg,	P =   -15.101 deg,	R =   -96.403 deg
};
P[51]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1314.657  mm,	Y =   763.676  mm,	Z =  -200.971  mm,
	W =  -110.276 deg,	P =   -14.535 deg,	R =  -100.836 deg
};
P[52]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1312.644  mm,	Y =   753.882  mm,	Z =  -199.795  mm,
	W =  -109.635 deg,	P =   -14.447 deg,	R =  -105.265 deg
};
P[53]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1310.009  mm,	Y =   744.535  mm,	Z =  -198.337  mm,
	W =  -109.103 deg,	P =   -14.384 deg,	R =  -108.504 deg
};
P[54]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1306.827  mm,	Y =   735.678  mm,	Z =  -196.648  mm,
	W =  -108.392 deg,	P =   -14.307 deg,	R =  -112.625 deg
};
P[55]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1304.198  mm,	Y =   729.502  mm,	Z =  -195.294  mm,
	W =  -107.773 deg,	P =   -14.241 deg,	R =  -116.139 deg
};
P[56]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1298.407  mm,	Y =   718.062  mm,	Z =  -192.519  mm,
	W =  -106.932 deg,	P =   -14.149 deg,	R =  -121.162 deg
};
P[57]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1291.941  mm,	Y =   707.479  mm,	Z =  -190.382  mm,
	W =  -106.269 deg,	P =   -14.066 deg,	R =  -125.698 deg
};
P[58]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1288.131  mm,	Y =   702.103  mm,	Z =  -189.518  mm,
	W =  -105.781 deg,	P =   -13.988 deg,	R =  -130.143 deg
};
P[59]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1281.702  mm,	Y =   694.110  mm,	Z =  -188.516  mm,
	W =  -105.502 deg,	P =   -13.914 deg,	R =  -134.519 deg
};
P[60]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1275.868  mm,	Y =   688.044  mm,	Z =  -188.007  mm,
	W =  -105.438 deg,	P =   -13.851 deg,	R =  -138.498 deg
};
P[61]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1268.107  mm,	Y =   681.132  mm,	Z =  -187.677  mm,
	W =  -105.428 deg,	P =   -13.829 deg,	R =  -139.977 deg
};
P[62]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1260.508  mm,	Y =   674.776  mm,	Z =  -187.628  mm,
	W =  -105.443 deg,	P =   -13.863 deg,	R =  -137.727 deg
};
P[63]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1250.594  mm,	Y =   666.735  mm,	Z =  -187.705  mm,
	W =  -105.373 deg,	P =   -13.729 deg,	R =  -147.436 deg
};
P[64]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1243.198  mm,	Y =   661.831  mm,	Z =  -187.772  mm,
	W =  -105.298 deg,	P =   -13.637 deg,	R =  -156.529 deg
};
P[65]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1233.768  mm,	Y =   656.879  mm,	Z =  -187.950  mm,
	W =  -105.278 deg,	P =   -13.619 deg,	R =  -158.873 deg
};
P[66]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1225.380  mm,	Y =   653.586  mm,	Z =  -188.138  mm,
	W =  -105.242 deg,	P =   -13.593 deg,	R =  -162.872 deg
};
P[67]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1217.076  mm,	Y =   651.039  mm,	Z =  -188.348  mm,
	W =  -105.204 deg,	P =   -13.573 deg,	R =  -166.917 deg
};
P[68]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1208.384  mm,	Y =   648.977  mm,	Z =  -188.585  mm,
	W =  -105.160 deg,	P =   -13.560 deg,	R =  -171.451 deg
};
P[69]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1199.353  mm,	Y =   647.447  mm,	Z =  -188.853  mm,
	W =  -105.114 deg,	P =   -13.556 deg,	R =  -176.195 deg
};
P[70]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1186.738  mm,	Y =   646.366  mm,	Z =  -189.280  mm,
	W =  -105.069 deg,	P =   -13.561 deg,	R =   179.311 deg
};
P[71]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1179.546  mm,	Y =   646.347  mm,	Z =  -189.538  mm,
	W =  -105.038 deg,	P =   -13.569 deg,	R =   176.231 deg
};
P[72]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1169.644  mm,	Y =   646.899  mm,	Z =  -189.967  mm,
	W =  -105.170 deg,	P =   -13.572 deg,	R =   175.317 deg
};
P[73]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1157.285  mm,	Y =   648.405  mm,	Z =  -190.796  mm,
	W =  -106.961 deg,	P =   -13.569 deg,	R =   174.549 deg
};
P[74]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1147.491  mm,	Y =   650.036  mm,	Z =  -192.912  mm,
	W =  -109.346 deg,	P =   -13.539 deg,	R =   174.478 deg
};
P[75]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1139.146  mm,	Y =   651.774  mm,	Z =  -197.213  mm,
	W =  -112.145 deg,	P =   -13.468 deg,	R =   175.272 deg
};
P[76]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1130.139  mm,	Y =   654.165  mm,	Z =  -205.336  mm,
	W =  -114.824 deg,	P =   -13.371 deg,	R =   175.449 deg
};
P[77]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1123.363  mm,	Y =   656.793  mm,	Z =  -214.640  mm,
	W =  -120.114 deg,	P =   -13.109 deg,	R =   172.293 deg
};
P[78]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1117.748  mm,	Y =   660.277  mm,	Z =  -222.675  mm,
	W =  -126.491 deg,	P =   -12.649 deg,	R =   168.032 deg
};
P[79]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1111.879  mm,	Y =   663.452  mm,	Z =  -228.051  mm,
	W =  -119.899 deg,	P =   -13.263 deg,	R =   157.916 deg
};
P[80]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1104.457  mm,	Y =   666.726  mm,	Z =  -231.386  mm,
	W =  -106.920 deg,	P =   -13.744 deg,	R =   154.284 deg
};
P[81]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1097.622  mm,	Y =   669.621  mm,	Z =  -233.095  mm,
	W =  -105.725 deg,	P =   -13.738 deg,	R =   155.031 deg
};
P[82]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1085.382  mm,	Y =   675.694  mm,	Z =  -234.222  mm,
	W =  -105.804 deg,	P =   -13.784 deg,	R =   151.515 deg
};
P[83]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1079.415  mm,	Y =   679.245  mm,	Z =  -234.773  mm,
	W =  -105.884 deg,	P =   -13.836 deg,	R =   147.827 deg
};
P[84]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1068.669  mm,	Y =   686.706  mm,	Z =  -235.810  mm,
	W =  -105.989 deg,	P =   -13.919 deg,	R =   142.627 deg
};
P[85]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1063.529  mm,	Y =   690.849  mm,	Z =  -236.313  mm,
	W =  -106.066 deg,	P =   -13.990 deg,	R =   138.574 deg
};
P[86]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1054.637  mm,	Y =   698.777  mm,	Z =  -237.204  mm,
	W =  -106.118 deg,	P =   -14.044 deg,	R =   135.639 deg
};
P[87]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1046.615  mm,	Y =   707.199  mm,	Z =  -238.052  mm,
	W =  -106.192 deg,	P =   -14.130 deg,	R =   131.212 deg
};
P[88]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1039.658  mm,	Y =   715.915  mm,	Z =  -238.883  mm,
	W =  -106.261 deg,	P =   -14.227 deg,	R =   126.545 deg
};
P[89]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1036.365  mm,	Y =   720.741  mm,	Z =  -239.270  mm,
	W =  -106.325 deg,	P =   -14.335 deg,	R =   121.649 deg
};
P[90]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1030.640  mm,	Y =   730.542  mm,	Z =  -239.995  mm,
	W =  -106.396 deg,	P =   -14.486 deg,	R =   115.073 deg
};
P[91]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1025.352  mm,	Y =   742.173  mm,	Z =  -240.758  mm,
	W =  -106.437 deg,	P =   -14.604 deg,	R =   110.157 deg
};
P[92]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1022.094  mm,	Y =   751.891  mm,	Z =  -241.342  mm,
	W =  -106.467 deg,	P =   -14.723 deg,	R =   105.309 deg
};
P[93]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1020.185  mm,	Y =   759.633  mm,	Z =  -241.771  mm,
	W =  -106.486 deg,	P =   -14.842 deg,	R =   100.517 deg
};
P[94]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1018.250  mm,	Y =   771.487  mm,	Z =  -242.348  mm,
	W =  -106.495 deg,	P =   -14.962 deg,	R =    95.763 deg
};
P[95]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1017.863  mm,	Y =   775.454  mm,	Z =  -242.513  mm,
	W =  -106.506 deg,	P =   -15.000 deg,	R =    94.230 deg
};
P[96]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1017.555  mm,	Y =   790.987  mm,	Z =  -243.060  mm,
	W =  -106.482 deg,	P =   -15.197 deg,	R =    86.402 deg
};
P[97]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1017.816  mm,	Y =   795.988  mm,	Z =  -243.230  mm,
	W =  -106.482 deg,	P =   -15.198 deg,	R =    86.344 deg
};
P[98]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =   725.689  mm,	Y =   853.506  mm,	Z =  -242.034  mm,
	W =  -106.487 deg,	P =   -15.200 deg,	R =    86.348 deg
};
P[99]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1017.817  mm,	Y =   795.990  mm,	Z =  -243.233  mm,
	W =  -106.501 deg,	P =   -15.194 deg,	R =    86.334 deg
};
/END
