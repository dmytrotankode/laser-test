/PROG  CORR_NABI1023_002
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "WeldPRO Auto-Gen";
PROG_SIZE	= 5051;
CREATE		= DATE 26-10-11  TIME 12:59:48;
MODIFIED	= DATE 26-10-11  TIME 13:28:52;
FILE_NAME	= CORR_NAB;
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
	X =   956.815  mm,	Y =   769.405  mm,	Z =  -201.316  mm,
	W =  -111.674 deg,	P =     -.828 deg,	R =    89.298 deg
};
P[3]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   957.384  mm,	Y =   784.558  mm,	Z =  -200.424  mm,
	W =  -111.640 deg,	P =    -1.568 deg,	R =    82.756 deg
};
P[4]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   958.384  mm,	Y =   799.696  mm,	Z =  -199.543  mm,
	W =  -111.401 deg,	P =    -2.285 deg,	R =    76.127 deg
};
P[5]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   961.423  mm,	Y =   814.126  mm,	Z =  -197.690  mm,
	W =  -110.993 deg,	P =    -2.948 deg,	R =    69.659 deg
};
P[6]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   965.862  mm,	Y =   828.091  mm,	Z =  -195.268  mm,
	W =  -110.757 deg,	P =    -3.433 deg,	R =    64.459 deg
};
P[7]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   972.082  mm,	Y =   841.773  mm,	Z =  -193.166  mm,
	W =  -110.643 deg,	P =    -3.973 deg,	R =    58.931 deg
};
P[8]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   979.487  mm,	Y =   853.775  mm,	Z =  -191.082  mm,
	W =  -110.034 deg,	P =    -4.529 deg,	R =    52.413 deg
};
P[9]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   986.881  mm,	Y =   864.665  mm,	Z =  -190.321  mm,
	W =  -110.283 deg,	P =    -5.129 deg,	R =    45.011 deg
};
P[10]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   995.577  mm,	Y =   874.388  mm,	Z =  -190.626  mm,
	W =  -112.979 deg,	P =    -5.227 deg,	R =    43.988 deg
};
P[11]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1006.113  mm,	Y =   883.966  mm,	Z =  -190.741  mm,
	W =  -112.832 deg,	P =    -5.439 deg,	R =    40.052 deg
};
P[12]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1021.380  mm,	Y =   896.351  mm,	Z =  -191.105  mm,
	W =  -110.034 deg,	P =    -6.282 deg,	R =    29.406 deg
};
P[13]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1026.536  mm,	Y =   901.043  mm,	Z =  -191.099  mm,
	W =  -107.889 deg,	P =    -6.842 deg,	R =    20.156 deg
};
P[14]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1053.547  mm,	Y =   912.498  mm,	Z =  -191.383  mm,
	W =  -106.768 deg,	P =    -6.685 deg,	R =    15.520 deg
};
P[15]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1067.765  mm,	Y =   917.323  mm,	Z =  -192.366  mm,
	W =  -106.160 deg,	P =    -6.749 deg,	R =     7.955 deg
};
P[16]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1082.834  mm,	Y =   918.984  mm,	Z =  -192.615  mm,
	W =  -106.009 deg,	P =    -6.695 deg,	R =     1.516 deg
};
P[17]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1098.525  mm,	Y =   919.864  mm,	Z =  -193.726  mm,
	W =  -105.751 deg,	P =    -6.579 deg,	R =    -3.507 deg
};
P[18]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1112.681  mm,	Y =   917.941  mm,	Z =  -194.297  mm,
	W =  -105.349 deg,	P =    -6.560 deg,	R =    -6.554 deg
};
P[19]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1124.168  mm,	Y =   916.783  mm,	Z =  -197.656  mm,
	W =  -105.087 deg,	P =    -6.626 deg,	R =   -10.486 deg
};
P[20]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1135.502  mm,	Y =   914.096  mm,	Z =  -206.533  mm,
	W =  -105.562 deg,	P =    -6.526 deg,	R =   -15.592 deg
};
P[21]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1144.571  mm,	Y =   911.134  mm,	Z =  -218.136  mm,
	W =  -110.117 deg,	P =    -6.043 deg,	R =   -22.838 deg
};
P[22]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1151.609  mm,	Y =   906.924  mm,	Z =  -228.301  mm,
	W =  -114.372 deg,	P =    -6.098 deg,	R =   -22.029 deg
};
P[23]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1164.448  mm,	Y =   901.030  mm,	Z =  -236.669  mm,
	W =  -111.624 deg,	P =    -6.040 deg,	R =   -20.513 deg
};
P[24]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1177.839  mm,	Y =   895.523  mm,	Z =  -237.869  mm,
	W =  -111.143 deg,	P =    -5.770 deg,	R =   -26.805 deg
};
P[25]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1187.103  mm,	Y =   890.697  mm,	Z =  -238.431  mm,
	W =  -110.875 deg,	P =    -5.327 deg,	R =   -32.277 deg
};
P[26]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1205.029  mm,	Y =   879.601  mm,	Z =  -240.219  mm,
	W =  -110.703 deg,	P =    -4.916 deg,	R =   -37.753 deg
};
P[27]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1214.799  mm,	Y =   872.309  mm,	Z =  -241.160  mm,
	W =  -110.899 deg,	P =    -4.451 deg,	R =   -45.467 deg
};
P[28]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1221.124  mm,	Y =   865.301  mm,	Z =  -241.508  mm,
	W =  -110.820 deg,	P =    -4.031 deg,	R =   -48.643 deg
};
P[29]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1236.257  mm,	Y =   847.570  mm,	Z =  -242.744  mm,
	W =  -110.707 deg,	P =    -2.931 deg,	R =   -58.684 deg
};
P[30]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1244.206  mm,	Y =   833.026  mm,	Z =  -243.405  mm,
	W =  -110.993 deg,	P =    -2.084 deg,	R =   -66.501 deg
};
P[31]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1249.323  mm,	Y =   820.172  mm,	Z =  -244.133  mm,
	W =  -110.889 deg,	P =    -1.183 deg,	R =   -74.143 deg
};
P[32]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1253.923  mm,	Y =   805.475  mm,	Z =  -244.826  mm,
	W =  -110.847 deg,	P =     1.751 deg,	R =   -81.538 deg
};
P[33]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1256.213  mm,	Y =   790.536  mm,	Z =  -245.204  mm,
	W =  -110.728 deg,	P =     1.134 deg,	R =   -87.475 deg
};
P[34]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1255.848  mm,	Y =   775.352  mm,	Z =  -244.716  mm,
	W =  -110.745 deg,	P =      .393 deg,	R =   -94.846 deg
};
P[35]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1254.682  mm,	Y =   760.529  mm,	Z =  -244.889  mm,
	W =  -110.910 deg,	P =     -.346 deg,	R =  -101.864 deg
};
P[36]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1252.277  mm,	Y =   744.758  mm,	Z =  -244.860  mm,
	W =  -110.996 deg,	P =     3.003 deg,	R =  -109.627 deg
};
P[37]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1246.696  mm,	Y =   730.575  mm,	Z =  -244.780  mm,
	W =  -110.878 deg,	P =     3.763 deg,	R =  -117.047 deg
};
P[38]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1240.101  mm,	Y =   716.996  mm,	Z =  -243.536  mm,
	W =  -110.723 deg,	P =     4.475 deg,	R =  -124.471 deg
};
P[39]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1231.871  mm,	Y =   704.572  mm,	Z =  -243.038  mm,
	W =  -110.763 deg,	P =     5.073 deg,	R =  -131.503 deg
};
P[40]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1221.770  mm,	Y =   693.234  mm,	Z =  -242.573  mm,
	W =  -110.791 deg,	P =     5.551 deg,	R =  -138.520 deg
};
P[41]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1210.260  mm,	Y =   683.495  mm,	Z =  -241.765  mm,
	W =  -110.894 deg,	P =     5.849 deg,	R =  -142.755 deg
};
P[42]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1198.864  mm,	Y =   673.524  mm,	Z =  -241.444  mm,
	W =  -111.092 deg,	P =     6.176 deg,	R =  -149.383 deg
};
P[43]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1184.797  mm,	Y =   666.645  mm,	Z =  -239.715  mm,
	W =  -111.179 deg,	P =     6.485 deg,	R =  -154.203 deg
};
P[44]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1171.581  mm,	Y =   659.900  mm,	Z =  -238.563  mm,
	W =  -112.670 deg,	P =     6.718 deg,	R =  -160.135 deg
};
P[45]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1162.036  mm,	Y =   653.775  mm,	Z =  -231.528  mm,
	W =  -113.015 deg,	P =     6.516 deg,	R =  -154.164 deg
};
P[46]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1154.121  mm,	Y =   648.574  mm,	Z =  -219.478  mm,
	W =  -107.029 deg,	P =     6.676 deg,	R =  -158.738 deg
};
P[47]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1146.669  mm,	Y =   645.272  mm,	Z =  -210.753  mm,
	W =  -105.474 deg,	P =     6.835 deg,	R =  -165.078 deg
};
P[48]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1135.470  mm,	Y =   641.882  mm,	Z =  -200.781  mm,
	W =  -105.261 deg,	P =     6.901 deg,	R =  -169.946 deg
};
P[49]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1121.663  mm,	Y =   639.698  mm,	Z =  -196.477  mm,
	W =  -105.610 deg,	P =     6.917 deg,	R =  -173.095 deg
};
P[50]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1107.372  mm,	Y =   637.426  mm,	Z =  -196.045  mm,
	W =  -106.011 deg,	P =     6.906 deg,	R =  -177.396 deg
};
P[51]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1093.050  mm,	Y =   636.699  mm,	Z =  -195.064  mm,
	W =  -106.202 deg,	P =     6.816 deg,	R =   176.086 deg
};
P[52]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1078.786  mm,	Y =   637.861  mm,	Z =  -194.546  mm,
	W =  -106.523 deg,	P =     6.629 deg,	R =   169.301 deg
};
P[53]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1064.694  mm,	Y =   640.427  mm,	Z =  -193.910  mm,
	W =  -107.666 deg,	P =     6.368 deg,	R =   162.894 deg
};
P[54]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1051.002  mm,	Y =   644.562  mm,	Z =  -193.560  mm,
	W =  -109.461 deg,	P =     5.993 deg,	R =   155.890 deg
};
P[55]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1037.815  mm,	Y =   649.807  mm,	Z =  -193.391  mm,
	W =  -112.261 deg,	P =     5.201 deg,	R =   144.591 deg
};
P[56]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1025.853  mm,	Y =   658.049  mm,	Z =  -192.624  mm,
	W =  -113.330 deg,	P =     4.658 deg,	R =   138.166 deg
};
P[57]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1014.398  mm,	Y =   667.522  mm,	Z =  -191.565  mm,
	W =  -111.027 deg,	P =     4.674 deg,	R =   138.356 deg
};
P[58]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   1002.717  mm,	Y =   676.439  mm,	Z =  -191.163  mm,
	W =  -110.131 deg,	P =     4.129 deg,	R =   132.496 deg
};
P[59]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   991.968  mm,	Y =   686.651  mm,	Z =  -191.393  mm,
	W =  -110.747 deg,	P =     3.348 deg,	R =   124.813 deg
};
P[60]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   982.496  mm,	Y =   698.302  mm,	Z =  -192.927  mm,
	W =  -111.077 deg,	P =     2.804 deg,	R =   119.796 deg
};
P[61]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   974.793  mm,	Y =   711.160  mm,	Z =  -194.324  mm,
	W =  -111.219 deg,	P =     2.102 deg,	R =   113.592 deg
};
P[62]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   967.811  mm,	Y =   724.561  mm,	Z =  -196.769  mm,
	W =  -111.499 deg,	P =     1.536 deg,	R =   108.754 deg
};
P[63]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   962.713  mm,	Y =   738.970  mm,	Z =  -198.497  mm,
	W =  -111.854 deg,	P =      .591 deg,	R =   100.867 deg
};
P[64]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   958.667  mm,	Y =   753.791  mm,	Z =  -200.426  mm,
	W =  -111.882 deg,	P =     -.056 deg,	R =    95.529 deg
};
P[65]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   956.362  mm,	Y =   769.053  mm,	Z =  -200.966  mm,
	W =  -111.892 deg,	P =     -.795 deg,	R =    89.420 deg
};
P[66]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   956.037  mm,	Y =   769.309  mm,	Z =  -200.888  mm,
	W =  -111.871 deg,	P =     -.809 deg,	R =    89.302 deg
};
P[67]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   674.723  mm,	Y =   783.686  mm,	Z =  -313.775  mm,
	W =  -111.871 deg,	P =     -.809 deg,	R =    89.303 deg
};
/END
