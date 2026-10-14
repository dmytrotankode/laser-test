/PROG  TOR_XL_0510_2
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "WeldPRO Auto-Gen";
PROG_SIZE	= 5051;
CREATE		= DATE 26-10-06  TIME 10:53:52;
MODIFIED	= DATE 26-10-06  TIME 11:40:06;
FILE_NAME	= TOR_XL_0;
VERSION		= 0;
LINE_COUNT	= 77;
MEMORY_SIZE	= 5379;
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
   2:  !TOR XL holes, Feature1 ;
   3:   ;
   4:  UFRAME_NUM=2 ;
   5:  UTOOL_NUM=2 ;
   6:  !Feature Approach ;
   7:J P[1] 100% FINE    ;
   8:   ;
   9:  !Segment1 ;
  10:L P[2] 500mm/sec FINE
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
  77:  CALL ROTATE    ;
/POS
P[1]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   674.723  mm,	Y =   783.686  mm,	Z =  -313.775  mm,
	W =  -111.871 deg,	P =     -.809 deg,	R =    89.303 deg
};
P[2]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   951.846  mm,	Y =   778.892  mm,	Z =  -214.256  mm,
	W =  -111.748 deg,	P =     -.821 deg,	R =    89.300 deg
};
P[3]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   952.446  mm,	Y =   794.122  mm,	Z =  -213.558  mm,
	W =  -111.750 deg,	P =    -1.579 deg,	R =    82.759 deg
};
P[4]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   954.600  mm,	Y =   809.223  mm,	Z =  -211.831  mm,
	W =  -111.542 deg,	P =    -2.327 deg,	R =    76.133 deg
};
P[5]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   958.988  mm,	Y =   823.668  mm,	Z =  -208.699  mm,
	W =  -111.157 deg,	P =    -3.034 deg,	R =    69.667 deg
};
P[6]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   963.940  mm,	Y =   837.560  mm,	Z =  -206.002  mm,
	W =  -110.917 deg,	P =    -3.550 deg,	R =    64.468 deg
};
P[7]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   971.215  mm,	Y =   851.203  mm,	Z =  -203.749  mm,
	W =  -110.775 deg,	P =    -4.103 deg,	R =    58.939 deg
};
P[8]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   979.555  mm,	Y =   863.164  mm,	Z =  -200.260  mm,
	W =  -110.163 deg,	P =    -4.710 deg,	R =    52.422 deg
};
P[9]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   989.573  mm,	Y =   874.562  mm,	Z =  -198.496  mm,
	W =  -110.375 deg,	P =    -5.318 deg,	R =    45.018 deg
};
P[10]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   998.984  mm,	Y =   883.830  mm,	Z =  -198.545  mm,
	W =  -113.065 deg,	P =    -5.406 deg,	R =    43.995 deg
};
P[11]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1010.355  mm,	Y =   893.040  mm,	Z =  -197.758  mm,
	W =  -112.902 deg,	P =    -5.624 deg,	R =    40.058 deg
};
P[12]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1021.046  mm,	Y =   902.470  mm,	Z =  -196.568  mm,
	W =  -110.035 deg,	P =    -6.282 deg,	R =    29.406 deg
};
P[13]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1026.868  mm,	Y =   905.481  mm,	Z =  -196.011  mm,
	W =  -107.889 deg,	P =    -6.842 deg,	R =    20.156 deg
};
P[14]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1054.316  mm,	Y =   916.628  mm,	Z =  -194.688  mm,
	W =  -106.768 deg,	P =    -6.685 deg,	R =    15.520 deg
};
P[15]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1069.033  mm,	Y =   918.598  mm,	Z =  -193.460  mm,
	W =  -106.160 deg,	P =    -6.749 deg,	R =     7.955 deg
};
P[16]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1084.020  mm,	Y =   919.624  mm,	Z =  -192.948  mm,
	W =  -106.009 deg,	P =    -6.695 deg,	R =     1.516 deg
};
P[17]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1099.615  mm,	Y =   919.403  mm,	Z =  -191.894  mm,
	W =  -105.751 deg,	P =    -6.579 deg,	R =    -3.507 deg
};
P[18]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1113.892  mm,	Y =   918.133  mm,	Z =  -192.001  mm,
	W =  -105.349 deg,	P =    -6.560 deg,	R =    -6.554 deg
};
P[19]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1125.903  mm,	Y =   917.122  mm,	Z =  -195.240  mm,
	W =  -105.087 deg,	P =    -6.626 deg,	R =   -10.486 deg
};
P[20]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1138.624  mm,	Y =   914.595  mm,	Z =  -204.937  mm,
	W =  -105.562 deg,	P =    -6.526 deg,	R =   -15.592 deg
};
P[21]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1148.851  mm,	Y =   910.611  mm,	Z =  -215.755  mm,
	W =  -110.117 deg,	P =    -6.043 deg,	R =   -22.838 deg
};
P[22]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1156.783  mm,	Y =   905.545  mm,	Z =  -225.052  mm,
	W =  -114.372 deg,	P =    -6.098 deg,	R =   -22.029 deg
};
P[23]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1170.254  mm,	Y =   899.173  mm,	Z =  -228.985  mm,
	W =  -111.625 deg,	P =    -6.040 deg,	R =   -20.513 deg
};
P[24]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1183.804  mm,	Y =   893.345  mm,	Z =  -228.841  mm,
	W =  -111.143 deg,	P =    -5.770 deg,	R =   -26.805 deg
};
P[25]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1192.907  mm,	Y =   887.812  mm,	Z =  -228.688  mm,
	W =  -110.875 deg,	P =    -5.327 deg,	R =   -32.276 deg
};
P[26]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1210.084  mm,	Y =   875.165  mm,	Z =  -228.039  mm,
	W =  -110.703 deg,	P =    -4.916 deg,	R =   -37.753 deg
};
P[27]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1219.595  mm,	Y =   867.362  mm,	Z =  -228.022  mm,
	W =  -110.899 deg,	P =    -4.451 deg,	R =   -45.467 deg
};
P[28]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1225.462  mm,	Y =   859.896  mm,	Z =  -227.770  mm,
	W =  -110.820 deg,	P =    -4.031 deg,	R =   -48.643 deg
};
P[29]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1239.644  mm,	Y =   841.302  mm,	Z =  -227.813  mm,
	W =  -110.707 deg,	P =    -2.932 deg,	R =   -58.684 deg
};
P[30]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1247.637  mm,	Y =   826.756  mm,	Z =  -228.165  mm,
	W =  -110.993 deg,	P =    -2.084 deg,	R =   -66.501 deg
};
P[31]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1251.212  mm,	Y =   813.386  mm,	Z =  -227.515  mm,
	W =  -110.889 deg,	P =    -1.183 deg,	R =   -74.143 deg
};
P[32]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1254.689  mm,	Y =   798.540  mm,	Z =  -228.102  mm,
	W =  -110.847 deg,	P =     1.751 deg,	R =   -81.538 deg
};
P[33]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1255.728  mm,	Y =   783.634  mm,	Z =  -228.191  mm,
	W =  -110.728 deg,	P =     1.134 deg,	R =   -87.475 deg
};
P[34]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1254.973  mm,	Y =   768.725  mm,	Z =  -228.250  mm,
	W =  -110.745 deg,	P =      .393 deg,	R =   -94.846 deg
};
P[35]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1253.543  mm,	Y =   754.028  mm,	Z =  -228.623  mm,
	W =  -110.910 deg,	P =     -.346 deg,	R =  -101.864 deg
};
P[36]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1250.125  mm,	Y =   738.805  mm,	Z =  -229.048  mm,
	W =  -110.996 deg,	P =     3.003 deg,	R =  -109.627 deg
};
P[37]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1243.898  mm,	Y =   725.099  mm,	Z =  -229.129  mm,
	W =  -110.878 deg,	P =     3.763 deg,	R =  -117.047 deg
};
P[38]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1237.015  mm,	Y =   711.910  mm,	Z =  -229.682  mm,
	W =  -110.723 deg,	P =     4.475 deg,	R =  -124.471 deg
};
P[39]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1228.322  mm,	Y =   699.977  mm,	Z =  -230.375  mm,
	W =  -110.763 deg,	P =     5.073 deg,	R =  -131.503 deg
};
P[40]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1218.174  mm,	Y =   688.688  mm,	Z =  -230.812  mm,
	W =  -110.791 deg,	P =     5.551 deg,	R =  -138.520 deg
};
P[41]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1206.419  mm,	Y =   679.134  mm,	Z =  -231.220  mm,
	W =  -110.893 deg,	P =     5.849 deg,	R =  -142.755 deg
};
P[42]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1193.754  mm,	Y =   670.761  mm,	Z =  -231.490  mm,
	W =  -111.092 deg,	P =     6.176 deg,	R =  -149.383 deg
};
P[43]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1179.977  mm,	Y =   663.257  mm,	Z =  -231.967  mm,
	W =  -111.179 deg,	P =     6.485 deg,	R =  -154.203 deg
};
P[44]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1165.920  mm,	Y =   657.463  mm,	Z =  -230.974  mm,
	W =  -112.669 deg,	P =     6.718 deg,	R =  -160.135 deg
};
P[45]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1155.823  mm,	Y =   650.664  mm,	Z =  -224.174  mm,
	W =  -113.015 deg,	P =     6.515 deg,	R =  -154.164 deg
};
P[46]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1146.004  mm,	Y =   646.440  mm,	Z =  -212.042  mm,
	W =  -107.029 deg,	P =     6.676 deg,	R =  -158.738 deg
};
P[47]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1137.842  mm,	Y =   641.510  mm,	Z =  -204.454  mm,
	W =  -105.474 deg,	P =     6.835 deg,	R =  -165.077 deg
};
P[48]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1124.947  mm,	Y =   639.895  mm,	Z =  -197.119  mm,
	W =  -105.261 deg,	P =     6.901 deg,	R =  -169.946 deg
};
P[49]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1110.395  mm,	Y =   638.697  mm,	Z =  -195.256  mm,
	W =  -105.610 deg,	P =     6.917 deg,	R =  -173.094 deg
};
P[50]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1095.590  mm,	Y =   637.404  mm,	Z =  -195.910  mm,
	W =  -106.011 deg,	P =     6.906 deg,	R =  -177.396 deg
};
P[51]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1080.722  mm,	Y =   637.438  mm,	Z =  -196.188  mm,
	W =  -106.202 deg,	P =     6.816 deg,	R =   176.086 deg
};
P[52]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1065.979  mm,	Y =   639.042  mm,	Z =  -196.847  mm,
	W =  -106.523 deg,	P =     6.629 deg,	R =   169.301 deg
};
P[53]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1051.551  mm,	Y =   642.401  mm,	Z =  -197.833  mm,
	W =  -107.666 deg,	P =     6.368 deg,	R =   162.895 deg
};
P[54]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1037.562  mm,	Y =   647.260  mm,	Z =  -199.063  mm,
	W =  -109.461 deg,	P =     5.993 deg,	R =   155.890 deg
};
P[55]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1024.514  mm,	Y =   654.303  mm,	Z =  -199.867  mm,
	W =  -112.261 deg,	P =     5.201 deg,	R =   144.592 deg
};
P[56]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1012.501  mm,	Y =   663.166  mm,	Z =  -200.352  mm,
	W =  -113.330 deg,	P =     4.658 deg,	R =   138.167 deg
};
P[57]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1000.361  mm,	Y =   671.991  mm,	Z =  -200.684  mm,
	W =  -111.027 deg,	P =     4.674 deg,	R =   138.356 deg
};
P[58]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   989.548  mm,	Y =   682.517  mm,	Z =  -200.988  mm,
	W =  -110.131 deg,	P =     4.129 deg,	R =   132.496 deg
};
P[59]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   980.287  mm,	Y =   694.384  mm,	Z =  -202.297  mm,
	W =  -110.747 deg,	P =     3.348 deg,	R =   124.813 deg
};
P[60]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   972.484  mm,	Y =   707.105  mm,	Z =  -204.396  mm,
	W =  -111.077 deg,	P =     2.804 deg,	R =   119.797 deg
};
P[61]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   966.044  mm,	Y =   720.453  mm,	Z =  -207.028  mm,
	W =  -111.219 deg,	P =     2.102 deg,	R =   113.592 deg
};
P[62]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   960.887  mm,	Y =   734.354  mm,	Z =  -209.375  mm,
	W =  -111.499 deg,	P =     1.536 deg,	R =   108.754 deg
};
P[63]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   956.386  mm,	Y =   748.652  mm,	Z =  -211.170  mm,
	W =  -111.854 deg,	P =      .591 deg,	R =   100.867 deg
};
P[64]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   953.536  mm,	Y =   763.469  mm,	Z =  -213.371  mm,
	W =  -111.882 deg,	P =     -.056 deg,	R =    95.529 deg
};
P[65]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   951.899  mm,	Y =   778.627  mm,	Z =  -213.551  mm,
	W =  -111.892 deg,	P =     -.795 deg,	R =    89.420 deg
};
P[66]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   952.224  mm,	Y =   778.898  mm,	Z =  -214.000  mm,
	W =  -111.871 deg,	P =     -.809 deg,	R =    89.303 deg
};
P[67]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   674.723  mm,	Y =   783.686  mm,	Z =  -313.775  mm,
	W =  -111.871 deg,	P =     -.809 deg,	R =    89.303 deg
};
/END
