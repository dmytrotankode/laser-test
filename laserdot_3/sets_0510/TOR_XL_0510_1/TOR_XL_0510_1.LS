/PROG  TOR_XL_0510_1
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "WeldPRO Auto-Gen";
PROG_SIZE	= 5043;
CREATE		= DATE 26-10-06  TIME 10:08:22;
MODIFIED	= DATE 26-10-06  TIME 10:43:26;
FILE_NAME	= TOR_XL_P;
VERSION		= 0;
LINE_COUNT	= 77;
MEMORY_SIZE	= 5371;
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
	X =   956.562  mm,	Y =   778.558  mm,	Z =  -194.999  mm,
	W =  -111.748 deg,	P =     -.821 deg,	R =    89.300 deg
};
P[3]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   957.183  mm,	Y =   792.989  mm,	Z =  -194.452  mm,
	W =  -111.750 deg,	P =    -1.579 deg,	R =    82.759 deg
};
P[4]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   960.129  mm,	Y =   807.027  mm,	Z =  -191.976  mm,
	W =  -111.542 deg,	P =    -2.327 deg,	R =    76.133 deg
};
P[5]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   965.181  mm,	Y =   820.298  mm,	Z =  -189.683  mm,
	W =  -111.157 deg,	P =    -3.034 deg,	R =    69.667 deg
};
P[6]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   971.002  mm,	Y =   832.902  mm,	Z =  -187.290  mm,
	W =  -110.917 deg,	P =    -3.549 deg,	R =    64.468 deg
};
P[7]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   978.269  mm,	Y =   845.398  mm,	Z =  -185.160  mm,
	W =  -110.775 deg,	P =    -4.103 deg,	R =    58.939 deg
};
P[8]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   985.089  mm,	Y =   857.155  mm,	Z =  -183.425  mm,
	W =  -110.163 deg,	P =    -4.710 deg,	R =    52.422 deg
};
P[9]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =   994.012  mm,	Y =   867.994  mm,	Z =  -182.298  mm,
	W =  -110.375 deg,	P =    -5.318 deg,	R =    45.018 deg
};
P[10]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1002.824  mm,	Y =   877.618  mm,	Z =  -182.144  mm,
	W =  -113.065 deg,	P =    -5.406 deg,	R =    43.995 deg
};
P[11]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1013.254  mm,	Y =   887.297  mm,	Z =  -182.742  mm,
	W =  -112.902 deg,	P =    -5.624 deg,	R =    40.058 deg
};
P[12]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1023.103  mm,	Y =   895.730  mm,	Z =  -182.769  mm,
	W =  -110.035 deg,	P =    -6.282 deg,	R =    29.406 deg
};
P[13]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1027.559  mm,	Y =   899.139  mm,	Z =  -183.257  mm,
	W =  -107.890 deg,	P =    -6.842 deg,	R =    20.154 deg
};
P[14]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1054.240  mm,	Y =   912.416  mm,	Z =  -184.452  mm,
	W =  -106.769 deg,	P =    -6.685 deg,	R =    15.520 deg
};
P[15]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1068.376  mm,	Y =   916.217  mm,	Z =  -185.176  mm,
	W =  -106.161 deg,	P =    -6.750 deg,	R =     7.955 deg
};
P[16]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1083.285  mm,	Y =   918.491  mm,	Z =  -186.430  mm,
	W =  -106.009 deg,	P =    -6.695 deg,	R =     1.516 deg
};
P[17]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1099.125  mm,	Y =   919.237  mm,	Z =  -187.752  mm,
	W =  -105.751 deg,	P =    -6.579 deg,	R =    -3.506 deg
};
P[18]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1113.610  mm,	Y =   918.420  mm,	Z =  -189.287  mm,
	W =  -105.349 deg,	P =    -6.560 deg,	R =    -6.553 deg
};
P[19]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1125.441  mm,	Y =   917.393  mm,	Z =  -190.906  mm,
	W =  -105.087 deg,	P =    -6.626 deg,	R =   -10.486 deg
};
P[20]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1137.892  mm,	Y =   915.174  mm,	Z =  -197.423  mm,
	W =  -105.562 deg,	P =    -6.526 deg,	R =   -15.591 deg
};
P[21]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1148.654  mm,	Y =   911.795  mm,	Z =  -209.707  mm,
	W =  -110.117 deg,	P =    -6.043 deg,	R =   -22.838 deg
};
P[22]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1157.082  mm,	Y =   906.393  mm,	Z =  -224.670  mm,
	W =  -114.372 deg,	P =    -6.098 deg,	R =   -22.029 deg
};
P[23]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1170.822  mm,	Y =   898.862  mm,	Z =  -235.044  mm,
	W =  -111.625 deg,	P =    -6.040 deg,	R =   -20.513 deg
};
P[24]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1184.409  mm,	Y =   892.851  mm,	Z =  -236.393  mm,
	W =  -111.143 deg,	P =    -5.770 deg,	R =   -26.805 deg
};
P[25]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1193.790  mm,	Y =   887.627  mm,	Z =  -237.759  mm,
	W =  -110.876 deg,	P =    -5.327 deg,	R =   -32.276 deg
};
P[26]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1211.142  mm,	Y =   874.849  mm,	Z =  -240.011  mm,
	W =  -110.703 deg,	P =    -4.916 deg,	R =   -37.753 deg
};
P[27]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1220.172  mm,	Y =   866.525  mm,	Z =  -240.887  mm,
	W =  -110.899 deg,	P =    -4.451 deg,	R =   -45.467 deg
};
P[28]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1226.537  mm,	Y =   859.488  mm,	Z =  -242.189  mm,
	W =  -110.820 deg,	P =    -4.031 deg,	R =   -48.642 deg
};
P[29]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1240.304  mm,	Y =   840.730  mm,	Z =  -244.057  mm,
	W =  -110.707 deg,	P =    -2.932 deg,	R =   -58.684 deg
};
P[30]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1247.241  mm,	Y =   825.915  mm,	Z =  -245.046  mm,
	W =  -110.993 deg,	P =    -2.084 deg,	R =   -66.501 deg
};
P[31]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1251.759  mm,	Y =   813.134  mm,	Z =  -246.499  mm,
	W =  -110.889 deg,	P =    -1.183 deg,	R =   -74.143 deg
};
P[32]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1254.231  mm,	Y =   799.052  mm,	Z =  -246.820  mm,
	W =  -110.803 deg,	P =     1.751 deg,	R =   -81.538 deg
};
P[33]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1256.199  mm,	Y =   784.042  mm,	Z =  -247.743  mm,
	W =  -110.728 deg,	P =     1.134 deg,	R =   -87.474 deg
};
P[34]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1255.590  mm,	Y =   768.809  mm,	Z =  -247.986  mm,
	W =  -110.745 deg,	P =      .393 deg,	R =   -94.846 deg
};
P[35]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 0',
	X =  1253.569  mm,	Y =   753.900  mm,	Z =  -248.489  mm,
	W =  -110.910 deg,	P =     -.346 deg,	R =  -101.864 deg
};
P[36]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1249.490  mm,	Y =   740.104  mm,	Z =  -248.290  mm,
	W =  -110.996 deg,	P =     3.003 deg,	R =  -109.626 deg
};
P[37]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1244.247  mm,	Y =   726.348  mm,	Z =  -248.445  mm,
	W =  -110.877 deg,	P =     3.763 deg,	R =  -117.046 deg
};
P[38]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1237.565  mm,	Y =   713.265  mm,	Z =  -247.917  mm,
	W =  -110.723 deg,	P =     4.475 deg,	R =  -124.471 deg
};
P[39]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1229.307  mm,	Y =   701.156  mm,	Z =  -247.681  mm,
	W =  -110.763 deg,	P =     5.073 deg,	R =  -131.503 deg
};
P[40]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1219.087  mm,	Y =   689.996  mm,	Z =  -246.767  mm,
	W =  -110.791 deg,	P =     5.551 deg,	R =  -138.519 deg
};
P[41]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1207.603  mm,	Y =   680.176  mm,	Z =  -246.572  mm,
	W =  -110.893 deg,	P =     5.849 deg,	R =  -142.755 deg
};
P[42]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1195.164  mm,	Y =   671.306  mm,	Z =  -245.268  mm,
	W =  -111.092 deg,	P =     6.176 deg,	R =  -149.382 deg
};
P[43]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1181.672  mm,	Y =   662.832  mm,	Z =  -243.778  mm,
	W =  -111.178 deg,	P =     6.485 deg,	R =  -154.203 deg
};
P[44]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1167.335  mm,	Y =   657.584  mm,	Z =  -242.620  mm,
	W =  -112.669 deg,	P =     6.718 deg,	R =  -160.134 deg
};
P[45]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, -1, 1',
	X =  1156.830  mm,	Y =   651.844  mm,	Z =  -236.607  mm,
	W =  -113.015 deg,	P =     6.515 deg,	R =  -154.164 deg
};
P[46]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1147.906  mm,	Y =   645.135  mm,	Z =  -223.155  mm,
	W =  -107.029 deg,	P =     6.676 deg,	R =  -158.737 deg
};
P[47]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1138.821  mm,	Y =   640.904  mm,	Z =  -211.050  mm,
	W =  -105.474 deg,	P =     6.835 deg,	R =  -165.077 deg
};
P[48]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1125.828  mm,	Y =   638.432  mm,	Z =  -202.181  mm,
	W =  -105.261 deg,	P =     6.901 deg,	R =  -169.946 deg
};
P[49]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1111.156  mm,	Y =   636.227  mm,	Z =  -199.054  mm,
	W =  -105.610 deg,	P =     6.917 deg,	R =  -173.094 deg
};
P[50]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1095.966  mm,	Y =   634.858  mm,	Z =  -198.064  mm,
	W =  -106.011 deg,	P =     6.906 deg,	R =  -177.396 deg
};
P[51]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1080.687  mm,	Y =   635.169  mm,	Z =  -197.197  mm,
	W =  -106.202 deg,	P =     6.816 deg,	R =   176.086 deg
};
P[52]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1065.491  mm,	Y =   637.061  mm,	Z =  -195.892  mm,
	W =  -106.523 deg,	P =     6.629 deg,	R =   169.302 deg
};
P[53]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1051.056  mm,	Y =   642.113  mm,	Z =  -194.354  mm,
	W =  -107.666 deg,	P =     6.368 deg,	R =   162.895 deg
};
P[54]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1036.866  mm,	Y =   647.034  mm,	Z =  -193.917  mm,
	W =  -109.461 deg,	P =     5.993 deg,	R =   155.891 deg
};
P[55]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1023.998  mm,	Y =   654.631  mm,	Z =  -193.165  mm,
	W =  -112.261 deg,	P =     5.201 deg,	R =   144.592 deg
};
P[56]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1012.510  mm,	Y =   664.179  mm,	Z =  -192.144  mm,
	W =  -113.330 deg,	P =     4.658 deg,	R =   138.167 deg
};
P[57]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =  1000.774  mm,	Y =   673.720  mm,	Z =  -190.408  mm,
	W =  -111.027 deg,	P =     4.674 deg,	R =   138.357 deg
};
P[58]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   990.736  mm,	Y =   684.772  mm,	Z =  -189.083  mm,
	W =  -110.131 deg,	P =     4.129 deg,	R =   132.497 deg
};
P[59]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   981.857  mm,	Y =   696.349  mm,	Z =  -190.047  mm,
	W =  -110.747 deg,	P =     3.348 deg,	R =   124.814 deg
};
P[60]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   974.005  mm,	Y =   708.737  mm,	Z =  -190.923  mm,
	W =  -111.077 deg,	P =     2.804 deg,	R =   119.797 deg
};
P[61]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   967.863  mm,	Y =   721.841  mm,	Z =  -192.208  mm,
	W =  -111.219 deg,	P =     2.102 deg,	R =   113.593 deg
};
P[62]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   963.239  mm,	Y =   735.576  mm,	Z =  -194.418  mm,
	W =  -111.499 deg,	P =     1.536 deg,	R =   108.755 deg
};
P[63]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   959.196  mm,	Y =   749.365  mm,	Z =  -194.688  mm,
	W =  -111.854 deg,	P =      .591 deg,	R =   100.868 deg
};
P[64]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   957.039  mm,	Y =   763.790  mm,	Z =  -195.081  mm,
	W =  -111.882 deg,	P =     -.055 deg,	R =    95.530 deg
};
P[65]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   957.559  mm,	Y =   778.303  mm,	Z =  -194.333  mm,
	W =  -111.892 deg,	P =     -.795 deg,	R =    89.421 deg
};
P[66]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 1',
	X =   957.074  mm,	Y =   778.570  mm,	Z =  -194.952  mm,
	W =  -111.871 deg,	P =     -.809 deg,	R =    89.303 deg
};
P[67]{
   GP1:
	UF : 2, UT : 2,		CONFIG : 'N U T, 0, 0, 0',
	X =   674.723  mm,	Y =   783.686  mm,	Z =  -313.775  mm,
	W =  -111.871 deg,	P =     -.809 deg,	R =    89.303 deg
};
/END
