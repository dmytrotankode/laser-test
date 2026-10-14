/PROG  TOR_XL_1010_1
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "WeldPRO Auto-Gen";
PROG_SIZE	= 5051;
CREATE		= DATE 26-10-11  TIME 12:59:48;
MODIFIED	= DATE 26-10-11  TIME 13:28:52;
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
	X =   951.049  mm,	Y =   778.973  mm,	Z =  -216.625  mm,
	W =  -111.674 deg,	P =     -.828 deg,	R =    89.298 deg
};
P[3]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   952.669  mm,	Y =   794.119  mm,	Z =  -216.203  mm,
	W =  -111.640 deg,	P =    -1.568 deg,	R =    82.756 deg
};
P[4]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   954.365  mm,	Y =   809.218  mm,	Z =  -215.723  mm,
	W =  -111.401 deg,	P =    -2.285 deg,	R =    76.127 deg
};
P[5]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   957.954  mm,	Y =   823.552  mm,	Z =  -214.007  mm,
	W =  -110.993 deg,	P =    -2.948 deg,	R =    69.659 deg
};
P[6]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   962.861  mm,	Y =   837.376  mm,	Z =  -211.544  mm,
	W =  -110.757 deg,	P =    -3.433 deg,	R =    64.459 deg
};
P[7]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   969.570  mm,	Y =   850.819  mm,	Z =  -209.188  mm,
	W =  -110.643 deg,	P =    -3.973 deg,	R =    58.931 deg
};
P[8]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   977.377  mm,	Y =   862.529  mm,	Z =  -206.662  mm,
	W =  -110.034 deg,	P =    -4.529 deg,	R =    52.413 deg
};
P[9]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   985.251  mm,	Y =   873.092  mm,	Z =  -205.456  mm,
	W =  -110.283 deg,	P =    -5.129 deg,	R =    45.011 deg
};
P[10]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   994.494  mm,	Y =   882.363  mm,	Z =  -205.079  mm,
	W =  -112.979 deg,	P =    -5.227 deg,	R =    43.988 deg
};
P[11]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1005.580  mm,	Y =   891.395  mm,	Z =  -204.294  mm,
	W =  -112.832 deg,	P =    -5.439 deg,	R =    40.052 deg
};
P[12]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1021.606  mm,	Y =   903.001  mm,	Z =  -203.367  mm,
	W =  -110.034 deg,	P =    -6.282 deg,	R =    29.406 deg
};
P[13]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1027.036  mm,	Y =   907.472  mm,	Z =  -203.041  mm,
	W =  -107.889 deg,	P =    -6.842 deg,	R =    20.156 deg
};
P[14]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1054.776  mm,	Y =   917.523  mm,	Z =  -200.512  mm,
	W =  -106.768 deg,	P =    -6.685 deg,	R =    15.520 deg
};
P[15]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1069.402  mm,	Y =   921.620  mm,	Z =  -200.078  mm,
	W =  -106.160 deg,	P =    -6.749 deg,	R =     7.955 deg
};
P[16]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1084.615  mm,	Y =   922.543  mm,	Z =  -198.675  mm,
	W =  -106.009 deg,	P =    -6.695 deg,	R =     1.516 deg
};
P[17]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1100.517  mm,	Y =   922.605  mm,	Z =  -198.008  mm,
	W =  -105.751 deg,	P =    -6.579 deg,	R =    -3.507 deg
};
P[18]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1114.662  mm,	Y =   919.954  mm,	Z =  -196.846  mm,
	W =  -105.349 deg,	P =    -6.560 deg,	R =    -6.554 deg
};
P[19]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1126.511  mm,	Y =   918.095  mm,	Z =  -198.860  mm,
	W =  -105.087 deg,	P =    -6.626 deg,	R =   -10.486 deg
};
P[20]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1138.771  mm,	Y =   914.496  mm,	Z =  -206.407  mm,
	W =  -105.562 deg,	P =    -6.526 deg,	R =   -15.592 deg
};
P[21]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1149.017  mm,	Y =   910.665  mm,	Z =  -217.005  mm,
	W =  -110.117 deg,	P =    -6.043 deg,	R =   -22.838 deg
};
P[22]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1156.972  mm,	Y =   905.689  mm,	Z =  -226.193  mm,
	W =  -114.372 deg,	P =    -6.098 deg,	R =   -22.029 deg
};
P[23]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1170.530  mm,	Y =   898.761  mm,	Z =  -232.787  mm,
	W =  -111.624 deg,	P =    -6.040 deg,	R =   -20.513 deg
};
P[24]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1183.802  mm,	Y =   892.567  mm,	Z =  -232.286  mm,
	W =  -111.143 deg,	P =    -5.770 deg,	R =   -26.805 deg
};
P[25]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1192.902  mm,	Y =   887.286  mm,	Z =  -231.652  mm,
	W =  -110.875 deg,	P =    -5.327 deg,	R =   -32.277 deg
};
P[26]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1210.469  mm,	Y =   875.248  mm,	Z =  -230.965  mm,
	W =  -110.703 deg,	P =    -4.916 deg,	R =   -37.753 deg
};
P[27]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1219.995  mm,	Y =   867.474  mm,	Z =  -230.594  mm,
	W =  -110.899 deg,	P =    -4.451 deg,	R =   -45.467 deg
};
P[28]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1225.995  mm,	Y =   860.157  mm,	Z =  -229.973  mm,
	W =  -110.820 deg,	P =    -4.031 deg,	R =   -48.643 deg
};
P[29]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1240.366  mm,	Y =   841.677  mm,	Z =  -228.888  mm,
	W =  -110.707 deg,	P =    -2.931 deg,	R =   -58.684 deg
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
	X =  1252.184  mm,	Y =   813.654  mm,	Z =  -227.900  mm,
	W =  -110.889 deg,	P =    -1.183 deg,	R =   -74.143 deg
};
P[32]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1256.098  mm,	Y =   798.733  mm,	Z =  -227.571  mm,
	W =  -110.847 deg,	P =     1.751 deg,	R =   -81.538 deg
};
P[33]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1257.648  mm,	Y =   783.698  mm,	Z =  -227.186  mm,
	W =  -110.728 deg,	P =     1.134 deg,	R =   -87.475 deg
};
P[34]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1256.434  mm,	Y =   768.586  mm,	Z =  -226.240  mm,
	W =  -110.745 deg,	P =      .393 deg,	R =   -94.846 deg
};
P[35]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1254.510  mm,	Y =   753.840  mm,	Z =  -226.045  mm,
	W =  -110.910 deg,	P =     -.346 deg,	R =  -101.864 deg
};
P[36]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1251.261  mm,	Y =   738.215  mm,	Z =  -225.748  mm,
	W =  -110.996 deg,	P =     3.003 deg,	R =  -109.627 deg
};
P[37]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1244.923  mm,	Y =   724.331  mm,	Z =  -225.829  mm,
	W =  -110.878 deg,	P =     3.763 deg,	R =  -117.047 deg
};
P[38]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1237.463  mm,	Y =   711.145  mm,	Z =  -224.868  mm,
	W =  -110.723 deg,	P =     4.475 deg,	R =  -124.471 deg
};
P[39]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1228.508  mm,	Y =   699.160  mm,	Z =  -224.880  mm,
	W =  -110.763 deg,	P =     5.073 deg,	R =  -131.503 deg
};
P[40]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1217.742  mm,	Y =   688.349  mm,	Z =  -225.178  mm,
	W =  -110.791 deg,	P =     5.551 deg,	R =  -138.520 deg
};
P[41]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1205.590  mm,	Y =   679.235  mm,	Z =  -225.378  mm,
	W =  -110.894 deg,	P =     5.849 deg,	R =  -142.755 deg
};
P[42]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1193.607  mm,	Y =   669.845  mm,	Z =  -226.009  mm,
	W =  -111.092 deg,	P =     6.176 deg,	R =  -149.383 deg
};
P[43]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1178.945  mm,	Y =   663.748  mm,	Z =  -225.678  mm,
	W =  -111.179 deg,	P =     6.485 deg,	R =  -154.203 deg
};
P[44]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1165.180  mm,	Y =   657.715  mm,	Z =  -225.798  mm,
	W =  -112.670 deg,	P =     6.718 deg,	R =  -160.135 deg
};
P[45]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1154.402  mm,	Y =   652.444  mm,	Z =  -219.766  mm,
	W =  -113.015 deg,	P =     6.516 deg,	R =  -154.164 deg
};
P[46]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1144.900  mm,	Y =   648.102  mm,	Z =  -208.394  mm,
	W =  -107.029 deg,	P =     6.676 deg,	R =  -158.738 deg
};
P[47]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1136.266  mm,	Y =   645.501  mm,	Z =  -200.316  mm,
	W =  -105.474 deg,	P =     6.835 deg,	R =  -165.078 deg
};
P[48]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1123.686  mm,	Y =   643.080  mm,	Z =  -191.456  mm,
	W =  -105.261 deg,	P =     6.901 deg,	R =  -169.946 deg
};
P[49]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1109.220  mm,	Y =   641.773  mm,	Z =  -188.680  mm,
	W =  -105.610 deg,	P =     6.917 deg,	R =  -173.095 deg
};
P[50]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1094.725  mm,	Y =   640.228  mm,	Z =  -189.826  mm,
	W =  -106.011 deg,	P =     6.906 deg,	R =  -177.396 deg
};
P[51]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1080.223  mm,	Y =   640.229  mm,	Z =  -190.431  mm,
	W =  -106.202 deg,	P =     6.816 deg,	R =   176.086 deg
};
P[52]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1065.930  mm,	Y =   642.091  mm,	Z =  -191.552  mm,
	W =  -106.523 deg,	P =     6.629 deg,	R =   169.301 deg
};
P[53]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1051.850  mm,	Y =   645.361  mm,	Z =  -192.591  mm,
	W =  -107.666 deg,	P =     6.368 deg,	R =   162.894 deg
};
P[54]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1038.271  mm,	Y =   650.167  mm,	Z =  -193.914  mm,
	W =  -109.461 deg,	P =     5.993 deg,	R =   155.890 deg
};
P[55]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1025.233  mm,	Y =   656.030  mm,	Z =  -195.316  mm,
	W =  -112.261 deg,	P =     5.201 deg,	R =   144.591 deg
};
P[56]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1013.571  mm,	Y =   664.870  mm,	Z =  -196.178  mm,
	W =  -113.330 deg,	P =     4.658 deg,	R =   138.166 deg
};
P[57]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1002.561  mm,	Y =   674.936  mm,	Z =  -196.847  mm,
	W =  -111.027 deg,	P =     4.674 deg,	R =   138.356 deg
};
P[58]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   991.302  mm,	Y =   684.408  mm,	Z =  -198.072  mm,
	W =  -110.131 deg,	P =     4.129 deg,	R =   132.496 deg
};
P[59]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   981.075  mm,	Y =   695.106  mm,	Z =  -199.847  mm,
	W =  -110.747 deg,	P =     3.348 deg,	R =   124.813 deg
};
P[60]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   972.386  mm,	Y =   707.134  mm,	Z =  -202.881  mm,
	W =  -111.077 deg,	P =     2.804 deg,	R =   119.796 deg
};
P[61]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   965.512  mm,	Y =   720.278  mm,	Z =  -205.594  mm,
	W =  -111.219 deg,	P =     2.102 deg,	R =   113.592 deg
};
P[62]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   959.523  mm,	Y =   733.892  mm,	Z =  -209.319  mm,
	W =  -111.499 deg,	P =     1.536 deg,	R =   108.754 deg
};
P[63]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   955.360  mm,	Y =   748.445  mm,	Z =  -212.107  mm,
	W =  -111.854 deg,	P =      .591 deg,	R =   100.867 deg
};
P[64]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   952.328  mm,	Y =   763.353  mm,	Z =  -215.021  mm,
	W =  -111.882 deg,	P =     -.056 deg,	R =    95.529 deg
};
P[65]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   950.890  mm,	Y =   778.676  mm,	Z =  -216.349  mm,
	W =  -111.892 deg,	P =     -.795 deg,	R =    89.420 deg
};
P[66]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   950.569  mm,	Y =   778.951  mm,	Z =  -216.319  mm,
	W =  -111.871 deg,	P =     -.809 deg,	R =    89.302 deg
};
P[67]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   674.723  mm,	Y =   783.686  mm,	Z =  -313.775  mm,
	W =  -111.871 deg,	P =     -.809 deg,	R =    89.303 deg
};
/END
