/PROG  TORXL_NEW_PROG
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "WeldPRO Auto-Gen";
PROG_SIZE	= 7006;
CREATE		= DATE 26-06-20  TIME 11:11:22;
MODIFIED	= DATE 26-06-20  TIME 11:17:04;
FILE_NAME	= TORXL_NEW_PROG;
VERSION		= 0;
LINE_COUNT	= 112;
MEMORY_SIZE	= 7326;
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
   2:  !Tor XL_176 _2, Feature1 ;
   3:   ;
   4:  UFRAME_NUM=2 ;
   5:  UTOOL_NUM=2 ;
   6:  !Feature Approach ;
   7:J P[1] 40% FINE    ;
   8:   ;
   9:  !Segment1 ;
  10:L P[2] 200mm/sec FINE    ;
  11:  CALL LASER_ON    ;
  12:   ;
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
 107:L P[97] R[23:moving]mm/sec FINE    ;
 108:  CALL LASER_OFF    ;
 109:   ;
 110:  !Feature Retreat ;
 111:L P[98] 200mm/sec FINE    ;
 112:  CALL ROTATE    ;
/POS
P[1]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =   925.216  mm,	Y =   852.339  mm,	Z =  -242.204  mm,
	W =  -107.900 deg,	P =   -14.496 deg,	R =    86.345 deg
};
P[2]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1017.549  mm,	Y =   791.023  mm,	Z =  -227.541  mm,
	W =  -107.900 deg,	P =   -14.496 deg,	R =    86.345 deg
};
P[3]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1018.670  mm,	Y =   800.955  mm,	Z =  -227.755  mm,
	W =  -107.878 deg,	P =   -14.613 deg,	R =    81.637 deg
};
P[4]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1020.553  mm,	Y =   810.770  mm,	Z =  -227.956  mm,
	W =  -107.842 deg,	P =   -14.743 deg,	R =    76.286 deg
};
P[5]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1023.212  mm,	Y =   820.405  mm,	Z =  -228.143  mm,
	W =  -107.799 deg,	P =   -14.857 deg,	R =    71.464 deg
};
P[6]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1026.674  mm,	Y =   829.800  mm,	Z =  -227.714  mm,
	W =  -107.729 deg,	P =   -14.997 deg,	R =    65.281 deg
};
P[7]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1030.982  mm,	Y =   838.830  mm,	Z =  -227.566  mm,
	W =  -107.669 deg,	P =   -15.093 deg,	R =    60.811 deg
};
P[8]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1036.095  mm,	Y =   847.423  mm,	Z =  -227.569  mm,
	W =  -107.592 deg,	P =   -15.195 deg,	R =    55.794 deg
};
P[9]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1041.915  mm,	Y =   855.560  mm,	Z =  -227.449  mm,
	W =  -107.510 deg,	P =   -15.287 deg,	R =    50.981 deg
};
P[10]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1048.335  mm,	Y =   863.193  mm,	Z =  -228.202  mm,
	W =  -107.443 deg,	P =   -15.352 deg,	R =    47.312 deg
};
P[11]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1055.335  mm,	Y =   870.359  mm,	Z =  -227.616  mm,
	W =  -107.357 deg,	P =   -15.424 deg,	R =    42.935 deg
};
P[12]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1062.797  mm,	Y =   876.995  mm,	Z =  -228.033  mm,
	W =  -107.290 deg,	P =   -15.473 deg,	R =    39.733 deg
};
P[13]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1070.753  mm,	Y =   883.069  mm,	Z =  -227.709  mm,
	W =  -107.198 deg,	P =   -15.532 deg,	R =    35.477 deg
};
P[14]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1079.116  mm,	Y =   888.556  mm,	Z =  -227.547  mm,
	W =  -107.097 deg,	P =   -15.586 deg,	R =    31.069 deg
};
P[15]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1087.820  mm,	Y =   893.475  mm,	Z =  -227.548  mm,
	W =  -106.999 deg,	P =   -15.630 deg,	R =    26.922 deg
};
P[16]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1096.794  mm,	Y =   897.896  mm,	Z =  -227.355  mm,
	W =  -106.955 deg,	P =   -15.647 deg,	R =    25.111 deg
};
P[17]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1105.638  mm,	Y =   902.348  mm,	Z =  -229.308  mm,
	W =  -116.887 deg,	P =   -15.387 deg,	R =    30.058 deg
};
P[18]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1113.585  mm,	Y =   907.298  mm,	Z =  -232.538  mm,
	W =  -128.139 deg,	P =   -14.664 deg,	R =    26.538 deg
};
P[19]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1119.748  mm,	Y =   911.485  mm,	Z =  -227.999  mm,
	W =  -120.811 deg,	P =   -15.279 deg,	R =    16.221 deg
};
P[20]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1125.799  mm,	Y =   914.389  mm,	Z =  -220.917  mm,
	W =  -116.747 deg,	P =   -15.506 deg,	R =    11.788 deg
};
P[21]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1131.949  mm,	Y =   916.675  mm,	Z =  -213.787  mm,
	W =  -114.108 deg,	P =   -15.611 deg,	R =     9.687 deg
};
P[22]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1139.244  mm,	Y =   918.679  mm,	Z =  -204.135  mm,
	W =  -111.507 deg,	P =   -15.682 deg,	R =     9.676 deg
};
P[23]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1147.972  mm,	Y =   920.409  mm,	Z =  -196.419  mm,
	W =  -108.866 deg,	P =   -15.726 deg,	R =     8.430 deg
};
P[24]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1157.618  mm,	Y =   921.822  mm,	Z =  -191.530  mm,
	W =  -106.869 deg,	P =   -15.740 deg,	R =     6.850 deg
};
P[25]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1167.546  mm,	Y =   922.904  mm,	Z =  -191.395  mm,
	W =  -106.283 deg,	P =   -15.742 deg,	R =     5.674 deg
};
P[26]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1177.506  mm,	Y =   923.749  mm,	Z =  -191.634  mm,
	W =  -106.303 deg,	P =   -15.742 deg,	R =     3.732 deg
};
P[27]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1187.497  mm,	Y =   924.047  mm,	Z =  -191.861  mm,
	W =  -106.346 deg,	P =   -15.738 deg,	R =     -.483 deg
};
P[28]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1197.475  mm,	Y =   923.490  mm,	Z =  -192.067  mm,
	W =  -106.395 deg,	P =   -15.723 deg,	R =    -5.295 deg
};
P[29]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1207.355  mm,	Y =   922.021  mm,	Z =  -192.611  mm,
	W =  -106.444 deg,	P =   -15.699 deg,	R =   -10.039 deg
};
P[30]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1217.097  mm,	Y =   919.807  mm,	Z =  -193.314  mm,
	W =  -106.487 deg,	P =   -15.669 deg,	R =   -14.284 deg
};
P[31]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1226.690  mm,	Y =   917.001  mm,	Z =  -193.639  mm,
	W =  -106.530 deg,	P =   -15.632 deg,	R =   -18.515 deg
};
P[32]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1236.045  mm,	Y =   913.492  mm,	Z =  -194.123  mm,
	W =  -106.574 deg,	P =   -15.585 deg,	R =   -22.931 deg
};
P[33]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1244.992  mm,	Y =   909.044  mm,	Z =  -194.215  mm,
	W =  -106.637 deg,	P =   -15.502 deg,	R =   -29.417 deg
};
P[34]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1249.828  mm,	Y =   905.793  mm,	Z =  -194.066  mm,
	W =  -106.744 deg,	P =   -15.404 deg,	R =   -35.234 deg
};
P[35]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1260.921  mm,	Y =   897.023  mm,	Z =  -194.824  mm,
	W =  -106.725 deg,	P =   -15.353 deg,	R =   -38.974 deg
};
P[36]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1268.751  mm,	Y =   890.811  mm,	Z =  -195.752  mm,
	W =  -106.722 deg,	P =   -15.359 deg,	R =   -38.624 deg
};
P[37]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1276.338  mm,	Y =   884.306  mm,	Z =  -196.206  mm,
	W =  -106.878 deg,	P =   -15.247 deg,	R =   -44.737 deg
};
P[38]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1283.332  mm,	Y =   877.183  mm,	Z =  -196.741  mm,
	W =  -107.070 deg,	P =   -15.190 deg,	R =   -47.603 deg
};
P[39]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1289.721  mm,	Y =   869.559  mm,	Z =  -197.173  mm,
	W =  -107.612 deg,	P =   -15.092 deg,	R =   -52.149 deg
};
P[40]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1295.448  mm,	Y =   861.463  mm,	Z =  -199.185  mm,
	W =  -108.324 deg,	P =   -14.988 deg,	R =   -56.548 deg
};
P[41]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1300.552  mm,	Y =   852.994  mm,	Z =  -201.041  mm,
	W =  -108.977 deg,	P =   -14.901 deg,	R =   -60.015 deg
};
P[42]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1305.035  mm,	Y =   844.201  mm,	Z =  -202.634  mm,
	W =  -109.668 deg,	P =   -14.805 deg,	R =   -63.574 deg
};
P[43]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1308.897  mm,	Y =   835.117  mm,	Z =  -204.166  mm,
	W =  -110.541 deg,	P =   -14.678 deg,	R =   -68.091 deg
};
P[44]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1312.119  mm,	Y =   825.753  mm,	Z =  -206.587  mm,
	W =  -111.312 deg,	P =   -14.551 deg,	R =   -72.476 deg
};
P[45]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1314.721  mm,	Y =   816.173  mm,	Z =  -208.390  mm,
	W =  -111.676 deg,	P =   -14.482 deg,	R =   -74.873 deg
};
P[46]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.582  mm,	Y =   806.428  mm,	Z =  -210.180  mm,
	W =  -112.043 deg,	P =   -14.395 deg,	R =   -77.924 deg
};
P[47]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1318.061  mm,	Y =   796.508  mm,	Z =  -211.388  mm,
	W =  -112.464 deg,	P =   -14.256 deg,	R =   -82.908 deg
};
P[48]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1318.694  mm,	Y =   786.506  mm,	Z =  -212.779  mm,
	W =  -112.578 deg,	P =   -13.564 deg,	R =   -88.178 deg
};
P[49]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1318.572  mm,	Y =   776.497  mm,	Z =  -213.275  mm,
	W =  -112.522 deg,	P =   -13.925 deg,	R =   -91.603 deg
};
P[50]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1317.725  mm,	Y =   766.569  mm,	Z =  -212.734  mm,
	W =  -112.203 deg,	P =   -14.399 deg,	R =   -96.403 deg
};
P[51]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1316.180  mm,	Y =   756.765  mm,	Z =  -211.959  mm,
	W =  -111.694 deg,	P =   -13.833 deg,	R =  -100.836 deg
};
P[52]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1314.021  mm,	Y =   747.129  mm,	Z =  -210.693  mm,
	W =  -111.053 deg,	P =   -13.745 deg,	R =  -105.265 deg
};
P[53]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1311.259  mm,	Y =   737.689  mm,	Z =  -209.207  mm,
	W =  -110.521 deg,	P =   -13.682 deg,	R =  -108.504 deg
};
P[54]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1307.873  mm,	Y =   728.475  mm,	Z =  -207.771  mm,
	W =  -109.810 deg,	P =   -13.605 deg,	R =  -112.625 deg
};
P[55]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1303.863  mm,	Y =   719.535  mm,	Z =  -205.939  mm,
	W =  -109.191 deg,	P =   -13.539 deg,	R =  -116.139 deg
};
P[56]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1299.220  mm,	Y =   710.897  mm,	Z =  -203.997  mm,
	W =  -108.350 deg,	P =   -13.447 deg,	R =  -121.162 deg
};
P[57]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1293.904  mm,	Y =   702.599  mm,	Z =  -202.604  mm,
	W =  -107.687 deg,	P =   -13.364 deg,	R =  -125.698 deg
};
P[58]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1287.962  mm,	Y =   694.706  mm,	Z =  -200.793  mm,
	W =  -107.199 deg,	P =   -13.286 deg,	R =  -130.143 deg
};
P[59]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1281.380  mm,	Y =   687.233  mm,	Z =  -200.293  mm,
	W =  -106.920 deg,	P =   -13.212 deg,	R =  -134.519 deg
};
P[60]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1274.192  mm,	Y =   680.321  mm,	Z =  -199.578  mm,
	W =  -106.856 deg,	P =   -13.149 deg,	R =  -138.498 deg
};
P[61]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1266.505  mm,	Y =   673.916  mm,	Z =  -199.616  mm,
	W =  -106.846 deg,	P =   -13.127 deg,	R =  -139.977 deg
};
P[62]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1259.042  mm,	Y =   667.266  mm,	Z =  -199.398  mm,
	W =  -106.861 deg,	P =   -13.161 deg,	R =  -137.727 deg
};
P[63]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1251.189  mm,	Y =   661.080  mm,	Z =  -199.520  mm,
	W =  -106.791 deg,	P =   -13.027 deg,	R =  -147.436 deg
};
P[64]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1242.572  mm,	Y =   656.024  mm,	Z =  -199.390  mm,
	W =  -106.716 deg,	P =   -12.935 deg,	R =  -156.529 deg
};
P[65]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1233.431  mm,	Y =   651.941  mm,	Z =  -199.694  mm,
	W =  -106.696 deg,	P =   -12.917 deg,	R =  -158.873 deg
};
P[66]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1224.008  mm,	Y =   648.712  mm,	Z =  -198.270  mm,
	W =  -106.660 deg,	P =   -12.891 deg,	R =  -162.872 deg
};
P[67]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1214.376  mm,	Y =   646.028  mm,	Z =  -198.174  mm,
	W =  -106.622 deg,	P =   -12.871 deg,	R =  -166.917 deg
};
P[68]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1204.577  mm,	Y =   644.024  mm,	Z =  -198.273  mm,
	W =  -106.578 deg,	P =   -12.858 deg,	R =  -171.451 deg
};
P[69]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1194.652  mm,	Y =   642.877  mm,	Z =  -198.027  mm,
	W =  -106.532 deg,	P =   -12.854 deg,	R =  -176.195 deg
};
P[70]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1184.669  mm,	Y =   642.637  mm,	Z =  -197.441  mm,
	W =  -106.487 deg,	P =   -12.859 deg,	R =   179.311 deg
};
P[71]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1174.678  mm,	Y =   643.036  mm,	Z =  -197.412  mm,
	W =  -106.456 deg,	P =   -12.867 deg,	R =   176.231 deg
};
P[72]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1164.720  mm,	Y =   643.790  mm,	Z =  -196.727  mm,
	W =  -106.588 deg,	P =   -12.870 deg,	R =   175.317 deg
};
P[73]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1154.939  mm,	Y =   644.705  mm,	Z =  -197.228  mm,
	W =  -108.379 deg,	P =   -12.867 deg,	R =   174.549 deg
};
P[74]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1145.876  mm,	Y =   645.835  mm,	Z =  -200.730  mm,
	W =  -110.764 deg,	P =   -12.837 deg,	R =   174.478 deg
};
P[75]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1138.006  mm,	Y =   647.145  mm,	Z =  -208.006  mm,
	W =  -113.563 deg,	P =   -12.766 deg,	R =   175.272 deg
};
P[76]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1131.649  mm,	Y =   648.793  mm,	Z =  -214.691  mm,
	W =  -116.242 deg,	P =   -12.669 deg,	R =   175.449 deg
};
P[77]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1125.474  mm,	Y =   650.912  mm,	Z =  -222.141  mm,
	W =  -121.532 deg,	P =   -12.407 deg,	R =   172.293 deg
};
P[78]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1119.473  mm,	Y =   654.041  mm,	Z =  -229.498  mm,
	W =  -127.909 deg,	P =   -11.947 deg,	R =   168.032 deg
};
P[79]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1111.853  mm,	Y =   658.771  mm,	Z =  -232.815  mm,
	W =  -121.317 deg,	P =   -12.561 deg,	R =   157.916 deg
};
P[80]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1102.982  mm,	Y =   663.199  mm,	Z =  -232.908  mm,
	W =  -108.338 deg,	P =   -13.042 deg,	R =   154.284 deg
};
P[81]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1093.862  mm,	Y =   667.286  mm,	Z =  -232.892  mm,
	W =  -107.143 deg,	P =   -13.036 deg,	R =   155.031 deg
};
P[82]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1084.948  mm,	Y =   671.783  mm,	Z =  -232.031  mm,
	W =  -107.222 deg,	P =   -13.082 deg,	R =   151.515 deg
};
P[83]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1076.305  mm,	Y =   676.804  mm,	Z =  -232.258  mm,
	W =  -107.302 deg,	P =   -13.134 deg,	R =   147.827 deg
};
P[84]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1068.091  mm,	Y =   682.490  mm,	Z =  -231.595  mm,
	W =  -107.407 deg,	P =   -13.217 deg,	R =   142.627 deg
};
P[85]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1060.271  mm,	Y =   688.714  mm,	Z =  -231.856  mm,
	W =  -107.484 deg,	P =   -13.288 deg,	R =   138.574 deg
};
P[86]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1052.924  mm,	Y =   695.488  mm,	Z =  -231.129  mm,
	W =  -107.536 deg,	P =   -13.342 deg,	R =   135.639 deg
};
P[87]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1046.093  mm,	Y =   702.785  mm,	Z =  -230.665  mm,
	W =  -107.610 deg,	P =   -13.428 deg,	R =   131.212 deg
};
P[88]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1039.853  mm,	Y =   710.591  mm,	Z =  -230.548  mm,
	W =  -107.679 deg,	P =   -13.525 deg,	R =   126.545 deg
};
P[89]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1034.275  mm,	Y =   718.881  mm,	Z =  -230.828  mm,
	W =  -107.743 deg,	P =   -13.633 deg,	R =   121.649 deg
};
P[90]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1029.472  mm,	Y =   727.654  mm,	Z =  -229.995  mm,
	W =  -107.814 deg,	P =   -13.784 deg,	R =   115.073 deg
};
P[91]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1025.461  mm,	Y =   736.811  mm,	Z =  -229.862  mm,
	W =  -107.855 deg,	P =   -13.902 deg,	R =   110.157 deg
};
P[92]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =  1022.261  mm,	Y =   746.289  mm,	Z =  -229.426  mm,
	W =  -107.885 deg,	P =   -14.021 deg,	R =   105.309 deg
};
P[93]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1019.849  mm,	Y =   755.993  mm,	Z =  -229.295  mm,
	W =  -107.904 deg,	P =   -14.140 deg,	R =   100.517 deg
};
P[94]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1018.221  mm,	Y =   765.866  mm,	Z =  -228.917  mm,
	W =  -107.913 deg,	P =   -14.260 deg,	R =    95.764 deg
};
P[95]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1017.361  mm,	Y =   775.832  mm,	Z =  -228.805  mm,
	W =  -107.911 deg,	P =   -14.378 deg,	R =    91.085 deg
};
P[96]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1017.264  mm,	Y =   785.829  mm,	Z =  -228.968  mm,
	W =  -107.900 deg,	P =   -14.495 deg,	R =    86.402 deg
};
P[97]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 1, 0',
	X =  1017.528  mm,	Y =   791.000  mm,	Z =  -228.500  mm,
	W =  -107.900 deg,	P =   -14.496 deg,	R =    86.345 deg
};
P[98]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'F D T, 0, 0, 0',
	X =   925.216  mm,	Y =   852.339  mm,	Z =  -242.204  mm,
	W =  -107.900 deg,	P =   -14.496 deg,	R =    86.345 deg
};
/END
