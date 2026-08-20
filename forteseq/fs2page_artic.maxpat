{
 "patcher": {
  "fileversion": 1,
  "appversion": {
   "major": 9,
   "minor": 0,
   "revision": 7,
   "architecture": "x64",
   "modernui": 1
  },
  "classnamespace": "box",
  "rect": [
   100.0,
   100.0,
   960.0,
   700.0
  ],
  "openinpresentation": 1,
  "default_fontsize": 10.0,
  "default_fontname": "Arial Bold",
  "gridsize": [
   8.0,
   8.0
  ],
  "boxes": [
   {
    "box": {
     "id": "obj-1",
     "maxclass": "inlet",
     "numinlets": 0,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      20.0,
      30.0,
      30.0
     ],
     "comment": "init: re-emite el estado de los controles hacia el motor"
    }
   },
   {
    "box": {
     "id": "obj-2",
     "maxclass": "inlet",
     "numinlets": 0,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      90.0,
      20.0,
      30.0,
      30.0
     ],
     "comment": "eco: la salida 4 del js, cruda; el route de abajo toma lo suyo"
    }
   },
   {
    "box": {
     "id": "obj-3",
     "maxclass": "outlet",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      620.0,
      30.0,
      30.0
     ],
     "comment": "mensajes hacia [js forteseq2.js]"
    }
   },
   {
    "box": {
     "id": "obj-4",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      70.0,
      70.0,
      22.0
     ],
     "text": "outputvalue",
     "varname": "pg_init"
    }
   },
   {
    "box": {
     "id": "obj-65",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 7,
     "outlettype": [
      "",
      "",
      "",
      "",
      "",
      "",
      ""
     ],
     "patching_rect": [
      90.0,
      70.0,
      520.0,
      22.0
     ],
     "text": "route accentgrid g0silence g1silence euclid euclidk euclidrot",
     "varname": "pg_echo"
    }
   },
   {
    "box": {
     "annotation": "Casilla 1 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-5",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      20.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 1",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 1",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc1"
    }
   },
   {
    "box": {
     "id": "obj-6",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      191.0,
      52.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      41.0,
      52.0,
      18.0
     ],
     "text": "Acento",
     "varname": "fs2_alb_acc"
    }
   },
   {
    "box": {
     "id": "obj-7",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      253.0,
      56.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      103.0,
      56.0,
      18.0
     ],
     "text": "Acentos",
     "varname": "fs2_alb_acentos"
    }
   },
   {
    "box": {
     "id": "obj-8",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      169.0,
      52.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      19.0,
      52.0,
      18.0
     ],
     "text": "Normal",
     "varname": "fs2_alb_norm"
    }
   },
   {
    "box": {
     "annotation": "Cuantas casillas de la grilla de acentos estan en juego, de 1 a 16.",
     "id": "obj-9",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      20.0,
      231.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      81.0,
      44.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        4
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Ciclo Acentos",
       "parameter_mmax": 16.0,
       "parameter_mmin": 1.0,
       "parameter_modmode": 4,
       "parameter_shortname": "Ciclo",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "fs2_ciclo"
    }
   },
   {
    "box": {
     "id": "obj-10",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      213.0,
      38.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      63.0,
      38.0,
      18.0
     ],
     "text": "Ciclo",
     "varname": "fs2_alb_ciclo"
    }
   },
   {
    "box": {
     "annotation": "Casilla 2 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-11",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      35.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      15.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 2",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 2",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc2"
    }
   },
   {
    "box": {
     "annotation": "Casilla 3 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-12",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      50.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      30.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 3",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 3",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc3"
    }
   },
   {
    "box": {
     "annotation": "Casilla 4 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-13",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      65.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      45.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 4",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 4",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc4"
    }
   },
   {
    "box": {
     "id": "obj-14",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      76.0,
      150.0,
      44.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      56.0,
      0.0,
      44.0,
      18.0
     ],
     "text": "V.Min",
     "varname": "fs2_ah1"
    }
   },
   {
    "box": {
     "annotation": "Velocidad minima de las notas acentuadas.",
     "id": "obj-15",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      76.0,
      191.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      56.0,
      41.0,
      44.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        95
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Vel Min Acento",
       "parameter_mmax": 127.0,
       "parameter_mmin": 1.0,
       "parameter_modmode": 4,
       "parameter_shortname": "VMin A",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "fs2_vmin_a"
    }
   },
   {
    "box": {
     "annotation": "Velocidad minima de las notas sin acento. Cada nota sale al azar entre Min y Max.",
     "id": "obj-16",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      76.0,
      169.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      56.0,
      19.0,
      44.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        55
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Vel Min Normal",
       "parameter_mmax": 127.0,
       "parameter_mmin": 1.0,
       "parameter_modmode": 4,
       "parameter_shortname": "VMin N",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "fs2_vmin_n"
    }
   },
   {
    "box": {
     "annotation": "Escribe los dos porcentajes de silencio de una vez. Solo ac. calla el grupo normal, y ahi la grilla de acentos deja de ser una dinamica y pasa a ser el ritmo. Solo norm. hace lo contrario. Ralo y Muy ralo adelgazan las dos.",
     "id": "obj-17",
     "maxclass": "live.menu",
     "numinlets": 1,
     "numoutlets": 3,
     "outlettype": [
      "",
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      76.0,
      251.0,
      96.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      56.0,
      101.0,
      96.0,
      18.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "Silencio",
        "Todo",
        "Solo ac.",
        "Solo norm.",
        "Ralo",
        "Muy ralo"
       ],
       "parameter_mmax": 5,
       "parameter_modmode": 0,
       "parameter_type": 2,
       "parameter_unitstyle": 9,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Preset Silencio",
       "parameter_shortname": "Sil Pre"
      }
     },
     "varname": "fs2_silpre"
    }
   },
   {
    "box": {
     "annotation": "Casilla 5 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-18",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      80.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      60.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 5",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 5",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc5"
    }
   },
   {
    "box": {
     "annotation": "Encendido: el ciclo de acentos toma el largo del set actual, asi los acentos caen siempre en las mismas notas del acorde. Apagado: usa el largo fijo de Ciclo.",
     "id": "obj-19",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      84.0,
      231.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      64.0,
      81.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Ciclo igual a n",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Ciclo n",
       "parameter_type": 2
      }
     },
     "varname": "fs2_tie"
    }
   },
   {
    "box": {
     "id": "obj-20",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      84.0,
      213.0,
      62.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      64.0,
      63.0,
      62.0,
      18.0
     ],
     "text": "Ciclo = n",
     "varname": "fs2_alb_tie"
    }
   },
   {
    "box": {
     "annotation": "Casilla 6 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-21",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      95.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      75.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 6",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 6",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc6"
    }
   },
   {
    "box": {
     "annotation": "Casilla 7 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-22",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      110.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      90.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 7",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 7",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc7"
    }
   },
   {
    "box": {
     "annotation": "Velocidad maxima de las notas sin acento.",
     "id": "obj-23",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      124.0,
      169.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      104.0,
      19.0,
      44.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        80
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Vel Max Normal",
       "parameter_mmax": 127.0,
       "parameter_mmin": 1.0,
       "parameter_modmode": 4,
       "parameter_shortname": "VMax N",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "fs2_vmax_n"
    }
   },
   {
    "box": {
     "annotation": "Velocidad maxima de las notas acentuadas.",
     "id": "obj-24",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      124.0,
      191.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      104.0,
      41.0,
      44.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        115
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Vel Max Acento",
       "parameter_mmax": 127.0,
       "parameter_mmin": 1.0,
       "parameter_modmode": 4,
       "parameter_shortname": "VMax A",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "fs2_vmax_a"
    }
   },
   {
    "box": {
     "id": "obj-25",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      124.0,
      150.0,
      44.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      104.0,
      0.0,
      44.0,
      18.0
     ],
     "text": "V.Max",
     "varname": "fs2_ah2"
    }
   },
   {
    "box": {
     "annotation": "Casilla 8 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-26",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      125.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      105.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 8",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 8",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc8"
    }
   },
   {
    "box": {
     "annotation": "Casilla 9 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-27",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      140.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      120.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 9",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 9",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc9"
    }
   },
   {
    "box": {
     "annotation": "Encendido: la grilla de acentos se genera sola como E(k,n) -- k acentos repartidos lo mas parejo que el ciclo permite -- y los toggles pasan a ser el dibujo de lo que salio. Apagado: la grilla es la que dibujaste a mano. Usa Ciclo como n, tambien cuando Ciclo = n esta encendido.",
     "id": "obj-28",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      148.0,
      231.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      128.0,
      81.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_type": 2,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Euclid",
       "parameter_shortname": "Euc"
      }
     },
     "varname": "fs2_euc"
    }
   },
   {
    "box": {
     "id": "obj-29",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      148.0,
      213.0,
      32.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      128.0,
      63.0,
      32.0,
      18.0
     ],
     "text": "Euc",
     "varname": "fs2_lbl_euc"
    }
   },
   {
    "box": {
     "annotation": "Casilla 10 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-30",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      155.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      135.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 10",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 10",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc10"
    }
   },
   {
    "box": {
     "annotation": "Casilla 11 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-31",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      170.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 11",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 11",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc11"
    }
   },
   {
    "box": {
     "id": "obj-32",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      172.0,
      150.0,
      44.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      152.0,
      0.0,
      44.0,
      18.0
     ],
     "text": "Fig",
     "varname": "fs2_ah3"
    }
   },
   {
    "box": {
     "annotation": "Largo de las notas sin acento como denominador: 4 = negra, 8 = corchea, 16 = semicorchea.",
     "id": "obj-33",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      172.0,
      169.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      152.0,
      19.0,
      44.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        16
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Figura Normal",
       "parameter_mmax": 32.0,
       "parameter_mmin": 1.0,
       "parameter_modmode": 4,
       "parameter_shortname": "Fig N",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "fs2_fig_n"
    }
   },
   {
    "box": {
     "annotation": "Largo de las notas acentuadas como denominador: 4 = negra, 8 = corchea, 16 = semicorchea.",
     "id": "obj-34",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      172.0,
      191.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      152.0,
      41.0,
      44.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        4
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Figura Acento",
       "parameter_mmax": 32.0,
       "parameter_mmin": 1.0,
       "parameter_modmode": 4,
       "parameter_shortname": "Fig A",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "fs2_fig_a"
    }
   },
   {
    "box": {
     "annotation": "Escribe de una vez el registro de las cuatro voces, V1 la mas aguda. Libre las suelta enteras. Las demas son rangos de trabajo, no los extremos del instrumento. Despues podes mover Min y Span de cada voz: la plantilla no las traba, y desde ahi el menu es solo el recuerdo de lo ultimo que se aplico.",
     "id": "obj-35",
     "maxclass": "live.menu",
     "numinlets": 1,
     "numoutlets": 3,
     "outlettype": [
      "",
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      180.0,
      251.0,
      96.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      160.0,
      101.0,
      96.0,
      18.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "Rango",
        "Libre",
        "SATB",
        "Cuerdas",
        "Maderas",
        "Metales",
        "Teclado",
        "Ancho",
        "Cluster"
       ],
       "parameter_mmax": 8,
       "parameter_modmode": 0,
       "parameter_type": 2,
       "parameter_unitstyle": 9,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Rango",
       "parameter_shortname": "Rango"
      }
     },
     "varname": "fs2_rango"
    }
   },
   {
    "box": {
     "id": "obj-36",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      184.0,
      213.0,
      34.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      164.0,
      63.0,
      34.0,
      18.0
     ],
     "text": "Puls",
     "varname": "fs2_lbl_puls"
    }
   },
   {
    "box": {
     "annotation": "Cuantos acentos reparte el generador sobre el ciclo. 3 sobre 8 da el tresillo, 5 sobre 8 el cinquillo, 5 sobre 16 la clave. Mas pulsos que casillas acentua todo.",
     "id": "obj-37",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      184.0,
      231.0,
      34.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      164.0,
      81.0,
      34.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 16.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        4
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Pulsos",
       "parameter_shortname": "Puls"
      }
     },
     "varname": "fs2_puls"
    }
   },
   {
    "box": {
     "annotation": "Casilla 12 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-38",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      185.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      165.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 12",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 12",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc12"
    }
   },
   {
    "box": {
     "annotation": "Casilla 13 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-39",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      200.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      180.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 13",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 13",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc13"
    }
   },
   {
    "box": {
     "annotation": "Casilla 14 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-40",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      215.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      195.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 14",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 14",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc14"
    }
   },
   {
    "box": {
     "annotation": "Probabilidad en porcentaje de que una nota sin acento se calle y quede silencio.",
     "id": "obj-41",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      220.0,
      169.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      200.0,
      19.0,
      44.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Silencio Normal",
       "parameter_mmax": 100.0,
       "parameter_mmin": 0.0,
       "parameter_modmode": 4,
       "parameter_shortname": "Sil N",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "fs2_sil_n"
    }
   },
   {
    "box": {
     "annotation": "Probabilidad en porcentaje de que una nota acentuada se calle y quede silencio.",
     "id": "obj-42",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      220.0,
      191.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      200.0,
      41.0,
      44.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Silencio Acento",
       "parameter_mmax": 100.0,
       "parameter_mmin": 0.0,
       "parameter_modmode": 4,
       "parameter_shortname": "Sil A",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "fs2_sil_a"
    }
   },
   {
    "box": {
     "id": "obj-43",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      220.0,
      150.0,
      44.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      200.0,
      0.0,
      44.0,
      18.0
     ],
     "text": "Sil",
     "varname": "fs2_ah4"
    }
   },
   {
    "box": {
     "annotation": "Desde que casilla arranca el patron. El mismo E(k,n) girado son ritmos distintos: es la diferencia entre la clave y su reverso.",
     "id": "obj-44",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      222.0,
      231.0,
      30.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      202.0,
      81.0,
      30.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 15.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Giro",
       "parameter_shortname": "Gir"
      }
     },
     "varname": "fs2_gir"
    }
   },
   {
    "box": {
     "id": "obj-45",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      222.0,
      213.0,
      26.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      202.0,
      63.0,
      26.0,
      18.0
     ],
     "text": "Gir",
     "varname": "fs2_lbl_gir"
    }
   },
   {
    "box": {
     "annotation": "Casilla 15 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-46",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      230.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      210.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 15",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 15",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc15"
    }
   },
   {
    "box": {
     "annotation": "Casilla 16 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
     "id": "obj-47",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      245.0,
      273.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      225.0,
      123.0,
      15.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Acento 16",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Acc 16",
       "parameter_type": 2
      }
     },
     "varname": "fs2_acc16"
    }
   },
   {
    "box": {
     "id": "obj-48",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      308.0,
      540.0,
      92.0,
      22.0
     ],
     "text": "prepend setaccenttie",
     "varname": "fs2_tie_prep"
    }
   },
   {
    "box": {
     "id": "obj-49",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      404.0,
      540.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupsilence 0",
     "varname": "fs2_sil_n_prep"
    }
   },
   {
    "box": {
     "id": "obj-50",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      500.0,
      540.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupdur 0",
     "varname": "fs2_fig_n_prep"
    }
   },
   {
    "box": {
     "id": "obj-51",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      596.0,
      540.0,
      92.0,
      22.0
     ],
     "text": "prepend seteuclid",
     "varname": "fs2_euc_prep"
    }
   },
   {
    "box": {
     "id": "obj-52",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      692.0,
      540.0,
      92.0,
      22.0
     ],
     "text": "prepend setrangetemplate",
     "varname": "fs2_rango_prep"
    }
   },
   {
    "box": {
     "id": "obj-53",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      580.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupvelmax 1",
     "varname": "fs2_vmax_a_prep"
    }
   },
   {
    "box": {
     "id": "obj-54",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      116.0,
      580.0,
      92.0,
      22.0
     ],
     "text": "prepend seteuclidk",
     "varname": "fs2_puls_prep"
    }
   },
   {
    "box": {
     "id": "obj-55",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      212.0,
      580.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupsilence 1",
     "varname": "fs2_sil_a_prep"
    }
   },
   {
    "box": {
     "id": "obj-56",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      308.0,
      580.0,
      92.0,
      22.0
     ],
     "text": "prepend setsilencepreset",
     "varname": "fs2_silpre_prep"
    }
   },
   {
    "box": {
     "id": "obj-57",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      404.0,
      580.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupvelmin 1",
     "varname": "fs2_vmin_a_prep"
    }
   },
   {
    "box": {
     "id": "obj-58",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      500.0,
      580.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupvelmin 0",
     "varname": "fs2_vmin_n_prep"
    }
   },
   {
    "box": {
     "id": "obj-59",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 16,
     "outlettype": [
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      ""
     ],
     "patching_rect": [
      596.0,
      580.0,
      92.0,
      22.0
     ],
     "text": "unpack 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0",
     "varname": "fs2_acc_unpack"
    }
   },
   {
    "box": {
     "id": "obj-60",
     "maxclass": "newobj",
     "numinlets": 16,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      692.0,
      580.0,
      92.0,
      22.0
     ],
     "text": "pak 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0",
     "varname": "fs2_accent_pak"
    }
   },
   {
    "box": {
     "id": "obj-61",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      620.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupvelmax 0",
     "varname": "fs2_vmax_n_prep"
    }
   },
   {
    "box": {
     "id": "obj-62",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      116.0,
      620.0,
      92.0,
      22.0
     ],
     "text": "prepend setaccentcycle",
     "varname": "fs2_ciclo_prep"
    }
   },
   {
    "box": {
     "id": "obj-63",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      212.0,
      620.0,
      92.0,
      22.0
     ],
     "text": "prepend seteuclidrot",
     "varname": "fs2_gir_prep"
    }
   },
   {
    "box": {
     "id": "obj-64",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      308.0,
      620.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupdur 1",
     "varname": "fs2_fig_a_prep"
    }
   },
   {
    "box": {
     "id": "obj-66",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "varname": "pg_accent_prep",
     "patching_rect": [
      692.0,
      614.0,
      132.0,
      22.0
     ],
     "text": "prepend setaccentgrid"
    }
   }
  ],
  "lines": [
   {
    "patchline": {
     "source": [
      "obj-1",
      0
     ],
     "destination": [
      "obj-4",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-2",
      0
     ],
     "destination": [
      "obj-65",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-16",
      0
     ],
     "destination": [
      "obj-58",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-23",
      0
     ],
     "destination": [
      "obj-61",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-33",
      0
     ],
     "destination": [
      "obj-50",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-41",
      0
     ],
     "destination": [
      "obj-49",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-15",
      0
     ],
     "destination": [
      "obj-57",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-24",
      0
     ],
     "destination": [
      "obj-53",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-34",
      0
     ],
     "destination": [
      "obj-64",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-42",
      0
     ],
     "destination": [
      "obj-55",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-9",
      0
     ],
     "destination": [
      "obj-62",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-19",
      0
     ],
     "destination": [
      "obj-48",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-5",
      0
     ],
     "destination": [
      "obj-60",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-11",
      0
     ],
     "destination": [
      "obj-60",
      1
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-12",
      0
     ],
     "destination": [
      "obj-60",
      2
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-13",
      0
     ],
     "destination": [
      "obj-60",
      3
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-18",
      0
     ],
     "destination": [
      "obj-60",
      4
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-21",
      0
     ],
     "destination": [
      "obj-60",
      5
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-22",
      0
     ],
     "destination": [
      "obj-60",
      6
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-26",
      0
     ],
     "destination": [
      "obj-60",
      7
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-27",
      0
     ],
     "destination": [
      "obj-60",
      8
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-30",
      0
     ],
     "destination": [
      "obj-60",
      9
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-31",
      0
     ],
     "destination": [
      "obj-60",
      10
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-38",
      0
     ],
     "destination": [
      "obj-60",
      11
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-39",
      0
     ],
     "destination": [
      "obj-60",
      12
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-40",
      0
     ],
     "destination": [
      "obj-60",
      13
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-46",
      0
     ],
     "destination": [
      "obj-60",
      14
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-47",
      0
     ],
     "destination": [
      "obj-60",
      15
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      0
     ],
     "destination": [
      "obj-5",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      1
     ],
     "destination": [
      "obj-11",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      2
     ],
     "destination": [
      "obj-12",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      3
     ],
     "destination": [
      "obj-13",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      4
     ],
     "destination": [
      "obj-18",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      5
     ],
     "destination": [
      "obj-21",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      6
     ],
     "destination": [
      "obj-22",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      7
     ],
     "destination": [
      "obj-26",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      8
     ],
     "destination": [
      "obj-27",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      9
     ],
     "destination": [
      "obj-30",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      10
     ],
     "destination": [
      "obj-31",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      11
     ],
     "destination": [
      "obj-38",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      12
     ],
     "destination": [
      "obj-39",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      13
     ],
     "destination": [
      "obj-40",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      14
     ],
     "destination": [
      "obj-46",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-59",
      15
     ],
     "destination": [
      "obj-47",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-28",
      0
     ],
     "destination": [
      "obj-51",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-37",
      0
     ],
     "destination": [
      "obj-54",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-44",
      0
     ],
     "destination": [
      "obj-63",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-35",
      0
     ],
     "destination": [
      "obj-52",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-17",
      0
     ],
     "destination": [
      "obj-56",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-48",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-49",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-50",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-51",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-52",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-53",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-54",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-55",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-56",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-57",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-58",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-61",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-62",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-63",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-64",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-16",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-23",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-33",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-41",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-15",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-24",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-34",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-42",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-9",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-19",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-5",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-11",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-12",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-13",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-18",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-21",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-22",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-26",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-27",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-30",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-31",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-38",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-39",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-40",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-46",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-47",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-28",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-37",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-4",
      0
     ],
     "destination": [
      "obj-44",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-65",
      0
     ],
     "destination": [
      "obj-59",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-65",
      1
     ],
     "destination": [
      "obj-41",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-65",
      2
     ],
     "destination": [
      "obj-42",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-65",
      3
     ],
     "destination": [
      "obj-28",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-65",
      4
     ],
     "destination": [
      "obj-37",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-65",
      5
     ],
     "destination": [
      "obj-44",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-60",
      0
     ],
     "destination": [
      "obj-66",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-66",
      0
     ],
     "destination": [
      "obj-3",
      0
     ]
    }
   }
  ],
  "parameters": {
   "obj-5": [
    "Acento 1",
    "Acento 1",
    0
   ],
   "obj-9": [
    "Ciclo Acentos",
    "Ciclo Acentos",
    0
   ],
   "obj-11": [
    "Acento 2",
    "Acento 2",
    0
   ],
   "obj-12": [
    "Acento 3",
    "Acento 3",
    0
   ],
   "obj-13": [
    "Acento 4",
    "Acento 4",
    0
   ],
   "obj-15": [
    "Vel Min Acento",
    "Vel Min Acento",
    0
   ],
   "obj-16": [
    "Vel Min Normal",
    "Vel Min Normal",
    0
   ],
   "obj-17": [
    "Preset Silencio",
    "Preset Silencio",
    0
   ],
   "obj-18": [
    "Acento 5",
    "Acento 5",
    0
   ],
   "obj-19": [
    "Ciclo igual a n",
    "Ciclo igual a n",
    0
   ],
   "obj-21": [
    "Acento 6",
    "Acento 6",
    0
   ],
   "obj-22": [
    "Acento 7",
    "Acento 7",
    0
   ],
   "obj-23": [
    "Vel Max Normal",
    "Vel Max Normal",
    0
   ],
   "obj-24": [
    "Vel Max Acento",
    "Vel Max Acento",
    0
   ],
   "obj-26": [
    "Acento 8",
    "Acento 8",
    0
   ],
   "obj-27": [
    "Acento 9",
    "Acento 9",
    0
   ],
   "obj-28": [
    "Euclid",
    "Euclid",
    0
   ],
   "obj-30": [
    "Acento 10",
    "Acento 10",
    0
   ],
   "obj-31": [
    "Acento 11",
    "Acento 11",
    0
   ],
   "obj-33": [
    "Figura Normal",
    "Figura Normal",
    0
   ],
   "obj-34": [
    "Figura Acento",
    "Figura Acento",
    0
   ],
   "obj-35": [
    "Rango",
    "Rango",
    0
   ],
   "obj-37": [
    "Pulsos",
    "Pulsos",
    0
   ],
   "obj-38": [
    "Acento 12",
    "Acento 12",
    0
   ],
   "obj-39": [
    "Acento 13",
    "Acento 13",
    0
   ],
   "obj-40": [
    "Acento 14",
    "Acento 14",
    0
   ],
   "obj-41": [
    "Silencio Normal",
    "Silencio Normal",
    0
   ],
   "obj-42": [
    "Silencio Acento",
    "Silencio Acento",
    0
   ],
   "obj-44": [
    "Giro",
    "Giro",
    0
   ],
   "obj-46": [
    "Acento 15",
    "Acento 15",
    0
   ],
   "obj-47": [
    "Acento 16",
    "Acento 16",
    0
   ]
  },
  "dependency_cache": [],
  "autosave": 0
 }
}