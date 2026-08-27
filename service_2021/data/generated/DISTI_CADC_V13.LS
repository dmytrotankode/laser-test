/PROG  DISTI_CADC_V13
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
	X =  1017.539  mm,	Y =   792.441  mm,	Z =  -238.376  mm,
	W =  -106.491 deg,	P =   -15.193 deg,	R =    86.327 deg
};
P[3]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1017.801  mm,	Y =   796.611  mm,	Z =  -238.445  mm,
	W =  -106.495 deg,	P =   -15.194 deg,	R =    86.332 deg
};
P[4]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1021.059  mm,	Y =   816.367  mm,	Z =  -238.660  mm,
	W =  -106.425 deg,	P =   -15.445 deg,	R =    76.281 deg
};
P[5]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1023.929  mm,	Y =   826.041  mm,	Z =  -238.716  mm,
	W =  -106.381 deg,	P =   -15.559 deg,	R =    71.464 deg
};
P[6]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1029.665  mm,	Y =   839.720  mm,	Z =  -238.731  mm,
	W =  -106.310 deg,	P =   -15.698 deg,	R =    65.272 deg
};
P[7]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1034.510  mm,	Y =   848.439  mm,	Z =  -238.691  mm,
	W =  -106.251 deg,	P =   -15.795 deg,	R =    60.811 deg
};
P[8]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1040.206  mm,	Y =   856.865  mm,	Z =  -238.612  mm,
	W =  -106.174 deg,	P =   -15.897 deg,	R =    55.794 deg
};
P[9]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1047.499  mm,	Y =   865.809  mm,	Z =  -238.479  mm,
	W =  -106.090 deg,	P =   -15.988 deg,	R =    50.970 deg
};
P[10]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1051.745  mm,	Y =   870.321  mm,	Z =  -238.389  mm,
	W =  -106.027 deg,	P =   -16.056 deg,	R =    47.314 deg
};
P[11]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1060.700  mm,	Y =   878.677  mm,	Z =  -238.180  mm,
	W =  -105.939 deg,	P =   -16.126 deg,	R =    42.935 deg
};
P[12]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1065.717  mm,	Y =   882.797  mm,	Z =  -238.052  mm,
	W =  -105.872 deg,	P =   -16.175 deg,	R =    39.733 deg
};
P[13]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1075.833  mm,	Y =   890.167  mm,	Z =  -237.779  mm,
	W =  -105.783 deg,	P =   -16.243 deg,	R =    35.484 deg
};
P[14]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1086.235  mm,	Y =   896.468  mm,	Z =  -237.474  mm,
	W =  -105.683 deg,	P =   -16.290 deg,	R =    31.072 deg
};
P[15]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1091.953  mm,	Y =   899.428  mm,	Z =  -237.300  mm,
	W =  -105.584 deg,	P =   -16.329 deg,	R =    26.914 deg
};
P[16]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1102.819  mm,	Y =   904.261  mm,	Z =  -236.948  mm,
	W =  -105.545 deg,	P =   -16.341 deg,	R =    25.103 deg
};
P[17]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1110.291  mm,	Y =   906.687  mm,	Z =  -236.827  mm,
	W =  -115.468 deg,	P =   -16.090 deg,	R =    30.046 deg
};
P[18]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1116.947  mm,	Y =   908.995  mm,	Z =  -235.166  mm,
	W =  -126.721 deg,	P =   -15.366 deg,	R =    26.538 deg
};
P[19]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1120.885  mm,	Y =   911.838  mm,	Z =  -231.090  mm,
	W =  -119.393 deg,	P =   -15.981 deg,	R =    16.221 deg
};
P[20]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1126.781  mm,	Y =   915.787  mm,	Z =  -223.521  mm,
	W =  -115.329 deg,	P =   -16.208 deg,	R =    11.788 deg
};
P[21]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1134.582  mm,	Y =   919.210  mm,	Z =  -213.333  mm,
	W =  -112.690 deg,	P =   -16.313 deg,	R =     9.687 deg
};
P[22]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1141.074  mm,	Y =   921.264  mm,	Z =  -206.283  mm,
	W =  -110.089 deg,	P =   -16.384 deg,	R =     9.676 deg
};
P[23]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1151.176  mm,	Y =   923.435  mm,	Z =  -200.248  mm,
	W =  -107.448 deg,	P =   -16.428 deg,	R =     8.430 deg
};
P[24]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1162.396  mm,	Y =   925.064  mm,	Z =  -197.575  mm,
	W =  -105.451 deg,	P =   -16.442 deg,	R =     6.850 deg
};
P[25]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1171.048  mm,	Y =   925.914  mm,	Z =  -197.384  mm,
	W =  -104.865 deg,	P =   -16.444 deg,	R =     5.674 deg
};
P[26]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1182.235  mm,	Y =   926.487  mm,	Z =  -197.330  mm,
	W =  -104.885 deg,	P =   -16.444 deg,	R =     3.732 deg
};
P[27]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1190.713  mm,	Y =   926.374  mm,	Z =  -197.287  mm,
	W =  -104.928 deg,	P =   -16.440 deg,	R =     -.482 deg
};
P[28]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1204.013  mm,	Y =   925.058  mm,	Z =  -197.195  mm,
	W =  -104.977 deg,	P =   -16.425 deg,	R =    -5.295 deg
};
P[29]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1209.992  mm,	Y =   923.969  mm,	Z =  -197.154  mm,
	W =  -105.026 deg,	P =   -16.401 deg,	R =   -10.039 deg
};
P[30]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1221.096  mm,	Y =   921.218  mm,	Z =  -197.047  mm,
	W =  -105.069 deg,	P =   -16.371 deg,	R =   -14.284 deg
};
P[31]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1229.921  mm,	Y =   918.315  mm,	Z =  -196.954  mm,
	W =  -105.112 deg,	P =   -16.334 deg,	R =   -18.515 deg
};
P[32]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1237.045  mm,	Y =   915.418  mm,	Z =  -196.873  mm,
	W =  -105.156 deg,	P =   -16.287 deg,	R =   -22.931 deg
};
P[33]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1247.456  mm,	Y =   910.065  mm,	Z =  -196.734  mm,
	W =  -105.219 deg,	P =   -16.204 deg,	R =   -29.417 deg
};
P[34]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1251.702  mm,	Y =   907.245  mm,	Z =  -196.688  mm,
	W =  -105.326 deg,	P =   -16.106 deg,	R =   -35.234 deg
};
P[35]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1266.340  mm,	Y =   894.938  mm,	Z =  -196.372  mm,
	W =  -105.307 deg,	P =   -16.055 deg,	R =   -38.974 deg
};
P[36]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1271.702  mm,	Y =   890.106  mm,	Z =  -196.307  mm,
	W =  -105.304 deg,	P =   -16.061 deg,	R =   -38.624 deg
};
P[37]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1277.788  mm,	Y =   884.496  mm,	Z =  -196.395  mm,
	W =  -105.460 deg,	P =   -15.949 deg,	R =   -44.737 deg
};
P[38]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1283.919  mm,	Y =   878.176  mm,	Z =  -196.668  mm,
	W =  -105.652 deg,	P =   -15.892 deg,	R =   -47.603 deg
};
P[39]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1289.973  mm,	Y =   870.657  mm,	Z =  -197.257  mm,
	W =  -106.194 deg,	P =   -15.794 deg,	R =   -52.149 deg
};
P[40]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1295.304  mm,	Y =   862.754  mm,	Z =  -198.150  mm,
	W =  -106.906 deg,	P =   -15.690 deg,	R =   -56.548 deg
};
P[41]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1300.038  mm,	Y =   854.598  mm,	Z =  -199.345  mm,
	W =  -107.559 deg,	P =   -15.603 deg,	R =   -60.015 deg
};
P[42]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1305.542  mm,	Y =   843.322  mm,	Z =  -201.456  mm,
	W =  -108.250 deg,	P =   -15.507 deg,	R =   -63.574 deg
};
P[43]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1308.289  mm,	Y =   836.522  mm,	Z =  -202.801  mm,
	W =  -109.123 deg,	P =   -15.380 deg,	R =   -68.091 deg
};
P[44]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1311.856  mm,	Y =   825.977  mm,	Z =  -204.542  mm,
	W =  -109.894 deg,	P =   -15.253 deg,	R =   -72.476 deg
};
P[45]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1313.432  mm,	Y =   820.244  mm,	Z =  -205.304  mm,
	W =  -110.258 deg,	P =   -15.184 deg,	R =   -74.873 deg
};
P[46]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1315.832  mm,	Y =   808.947  mm,	Z =  -206.420  mm,
	W =  -110.625 deg,	P =   -15.098 deg,	R =   -77.924 deg
};
P[47]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1317.103  mm,	Y =   799.032  mm,	Z =  -207.002  mm,
	W =  -111.046 deg,	P =   -14.958 deg,	R =   -82.908 deg
};
P[48]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1317.655  mm,	Y =   789.792  mm,	Z =  -207.190  mm,
	W =  -111.160 deg,	P =   -14.266 deg,	R =   -88.178 deg
};
P[49]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1317.559  mm,	Y =   779.216  mm,	Z =  -206.985  mm,
	W =  -111.104 deg,	P =   -14.627 deg,	R =   -91.603 deg
};
P[50]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.988  mm,	Y =   771.901  mm,	Z =  -206.578  mm,
	W =  -110.785 deg,	P =   -15.101 deg,	R =   -96.403 deg
};
P[51]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1315.625  mm,	Y =   761.989  mm,	Z =  -205.701  mm,
	W =  -110.276 deg,	P =   -14.535 deg,	R =  -100.836 deg
};
P[52]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1313.548  mm,	Y =   752.208  mm,	Z =  -204.452  mm,
	W =  -109.635 deg,	P =   -14.447 deg,	R =  -105.265 deg
};
P[53]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1310.891  mm,	Y =   742.939  mm,	Z =  -202.920  mm,
	W =  -109.103 deg,	P =   -14.384 deg,	R =  -108.504 deg
};
P[54]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1307.099  mm,	Y =   732.604  mm,	Z =  -200.803  mm,
	W =  -108.392 deg,	P =   -14.307 deg,	R =  -112.625 deg
};
P[55]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1304.379  mm,	Y =   726.402  mm,	Z =  -199.332  mm,
	W =  -107.773 deg,	P =   -14.241 deg,	R =  -116.139 deg
};
P[56]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1298.680  mm,	Y =   715.351  mm,	Z =  -196.829  mm,
	W =  -106.932 deg,	P =   -14.149 deg,	R =  -121.162 deg
};
P[57]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1295.295  mm,	Y =   709.719  mm,	Z =  -195.768  mm,
	W =  -106.269 deg,	P =   -14.066 deg,	R =  -125.698 deg
};
P[58]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1288.576  mm,	Y =   699.956  mm,	Z =  -194.262  mm,
	W =  -105.781 deg,	P =   -13.988 deg,	R =  -130.143 deg
};
P[59]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1282.903  mm,	Y =   693.127  mm,	Z =  -193.484  mm,
	W =  -105.502 deg,	P =   -13.914 deg,	R =  -134.519 deg
};
P[60]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1274.512  mm,	Y =   684.812  mm,	Z =  -192.844  mm,
	W =  -105.438 deg,	P =   -13.851 deg,	R =  -138.498 deg
};
P[61]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1269.919  mm,	Y =   680.803  mm,	Z =  -192.656  mm,
	W =  -105.428 deg,	P =   -13.829 deg,	R =  -139.977 deg
};
P[62]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1259.872  mm,	Y =   671.821  mm,	Z =  -192.489  mm,
	W =  -105.443 deg,	P =   -13.863 deg,	R =  -137.727 deg
};
P[63]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1251.685  mm,	Y =   665.331  mm,	Z =  -192.417  mm,
	W =  -105.373 deg,	P =   -13.729 deg,	R =  -147.436 deg
};
P[64]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1245.464  mm,	Y =   661.425  mm,	Z =  -192.368  mm,
	W =  -105.298 deg,	P =   -13.637 deg,	R =  -156.529 deg
};
P[65]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1238.448  mm,	Y =   657.720  mm,	Z =  -192.337  mm,
	W =  -105.278 deg,	P =   -13.619 deg,	R =  -158.873 deg
};
P[66]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1226.389  mm,	Y =   652.874  mm,	Z =  -192.312  mm,
	W =  -105.242 deg,	P =   -13.593 deg,	R =  -162.872 deg
};
P[67]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1217.990  mm,	Y =   650.357  mm,	Z =  -192.308  mm,
	W =  -105.204 deg,	P =   -13.573 deg,	R =  -166.917 deg
};
P[68]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1209.191  mm,	Y =   648.317  mm,	Z =  -192.315  mm,
	W =  -105.160 deg,	P =   -13.560 deg,	R =  -171.451 deg
};
P[69]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1200.041  mm,	Y =   646.848  mm,	Z =  -192.334  mm,
	W =  -105.114 deg,	P =   -13.556 deg,	R =  -176.195 deg
};
P[70]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1188.348  mm,	Y =   645.948  mm,	Z =  -192.377  mm,
	W =  -105.069 deg,	P =   -13.561 deg,	R =   179.311 deg
};
P[71]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1179.921  mm,	Y =   645.976  mm,	Z =  -192.420  mm,
	W =  -105.038 deg,	P =   -13.569 deg,	R =   176.231 deg
};
P[72]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1168.508  mm,	Y =   646.694  mm,	Z =  -192.524  mm,
	W =  -105.170 deg,	P =   -13.572 deg,	R =   175.317 deg
};
P[73]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1157.958  mm,	Y =   647.939  mm,	Z =  -193.134  mm,
	W =  -106.961 deg,	P =   -13.569 deg,	R =   174.549 deg
};
P[74]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1148.131  mm,	Y =   649.490  mm,	Z =  -196.029  mm,
	W =  -109.346 deg,	P =   -13.539 deg,	R =   174.478 deg
};
P[75]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1141.070  mm,	Y =   650.964  mm,	Z =  -200.276  mm,
	W =  -112.145 deg,	P =   -13.468 deg,	R =   175.272 deg
};
P[76]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1133.368  mm,	Y =   653.012  mm,	Z =  -207.590  mm,
	W =  -114.824 deg,	P =   -13.371 deg,	R =   175.449 deg
};
P[77]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1126.211  mm,	Y =   655.784  mm,	Z =  -216.879  mm,
	W =  -120.114 deg,	P =   -13.109 deg,	R =   172.293 deg
};
P[78]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1121.396  mm,	Y =   658.800  mm,	Z =  -223.244  mm,
	W =  -126.491 deg,	P =   -12.649 deg,	R =   168.032 deg
};
P[79]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1113.662  mm,	Y =   662.958  mm,	Z =  -229.929  mm,
	W =  -119.899 deg,	P =   -13.263 deg,	R =   157.916 deg
};
P[80]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1105.454  mm,	Y =   665.995  mm,	Z =  -232.175  mm,
	W =  -106.920 deg,	P =   -13.744 deg,	R =   154.284 deg
};
P[81]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1094.486  mm,	Y =   670.514  mm,	Z =  -233.151  mm,
	W =  -105.725 deg,	P =   -13.738 deg,	R =   155.031 deg
};
P[82]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1088.146  mm,	Y =   673.677  mm,	Z =  -233.471  mm,
	W =  -105.804 deg,	P =   -13.784 deg,	R =   151.515 deg
};
P[83]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1076.823  mm,	Y =   680.339  mm,	Z =  -234.060  mm,
	W =  -105.884 deg,	P =   -13.836 deg,	R =   147.827 deg
};
P[84]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1071.139  mm,	Y =   684.310  mm,	Z =  -234.351  mm,
	W =  -105.989 deg,	P =   -13.919 deg,	R =   142.627 deg
};
P[85]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1061.389  mm,	Y =   691.981  mm,	Z =  -234.872  mm,
	W =  -106.066 deg,	P =   -13.990 deg,	R =   138.574 deg
};
P[86]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1052.777  mm,	Y =   699.848  mm,	Z =  -235.312  mm,
	W =  -106.118 deg,	P =   -14.044 deg,	R =   135.639 deg
};
P[87]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1045.053  mm,	Y =   708.223  mm,	Z =  -235.782  mm,
	W =  -106.192 deg,	P =   -14.130 deg,	R =   131.212 deg
};
P[88]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1041.364  mm,	Y =   712.855  mm,	Z =  -236.016  mm,
	W =  -106.261 deg,	P =   -14.227 deg,	R =   126.545 deg
};
P[89]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1035.004  mm,	Y =   722.014  mm,	Z =  -236.438  mm,
	W =  -106.325 deg,	P =   -14.335 deg,	R =   121.649 deg
};
P[90]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1029.831  mm,	Y =   731.271  mm,	Z =  -236.775  mm,
	W =  -106.396 deg,	P =   -14.486 deg,	R =   115.073 deg
};
P[91]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1025.162  mm,	Y =   741.844  mm,	Z =  -237.133  mm,
	W =  -106.437 deg,	P =   -14.604 deg,	R =   110.157 deg
};
P[92]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1021.917  mm,	Y =   751.680  mm,	Z =  -237.465  mm,
	W =  -106.467 deg,	P =   -14.723 deg,	R =   105.309 deg
};
P[93]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1019.960  mm,	Y =   759.798  mm,	Z =  -237.711  mm,
	W =  -106.486 deg,	P =   -14.842 deg,	R =   100.517 deg
};
P[94]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1018.096  mm,	Y =   771.645  mm,	Z =  -237.998  mm,
	W =  -106.495 deg,	P =   -14.962 deg,	R =    95.763 deg
};
P[95]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1017.726  mm,	Y =   775.629  mm,	Z =  -238.078  mm,
	W =  -106.506 deg,	P =   -15.000 deg,	R =    94.230 deg
};
P[96]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1017.537  mm,	Y =   792.428  mm,	Z =  -238.374  mm,
	W =  -106.482 deg,	P =   -15.197 deg,	R =    86.402 deg
};
P[97]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1017.800  mm,	Y =   796.609  mm,	Z =  -238.443  mm,
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
	X =  1017.802  mm,	Y =   796.611  mm,	Z =  -238.446  mm,
	W =  -106.501 deg,	P =   -15.194 deg,	R =    86.334 deg
};
/END
