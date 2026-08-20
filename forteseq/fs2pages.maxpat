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
   1100.0,
   800.0
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
     "comment": "init",
     "patching_rect": [
      20.0,
      20.0,
      30.0,
      30.0
     ]
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
     "comment": "eco (salida 4 del js)",
     "patching_rect": [
      90.0,
      20.0,
      30.0,
      30.0
     ]
    }
   },
   {
    "box": {
     "id": "obj-3",
     "maxclass": "inlet",
     "numinlets": 0,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "comment": "salida 1 del js",
     "patching_rect": [
      160.0,
      20.0,
      30.0,
      30.0
     ]
    }
   },
   {
    "box": {
     "id": "obj-4",
     "maxclass": "inlet",
     "numinlets": 0,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "comment": "salida 7 del js",
     "patching_rect": [
      230.0,
      20.0,
      30.0,
      30.0
     ]
    }
   },
   {
    "box": {
     "id": "obj-5",
     "maxclass": "outlet",
     "numinlets": 1,
     "numoutlets": 0,
     "comment": "mensajes hacia [js forteseq2.js]",
     "patching_rect": [
      20.0,
      90.0,
      30.0,
      30.0
     ]
    }
   },
   {
    "box": {
     "id": "obj-6",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      270.0,
      70.0,
      22.0
     ],
     "text": "outputvalue",
     "varname": "pg_init"
    }
   },
   {
    "box": {
     "annotation": "Transpone en semitonos, de -24 a 24.",
     "id": "obj-7",
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
      451.0,
      48.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      101.0,
      48.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Root",
       "parameter_mmax": 24.0,
       "parameter_mmin": -24.0,
       "parameter_modmode": 4,
       "parameter_shortname": "Root",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "fs2_root"
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
      350.0,
      34.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      0.0,
      34.0,
      18.0
     ],
     "text": "Indep",
     "varname": "fs2_lbl_indep"
    }
   },
   {
    "box": {
     "id": "obj-9",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      391.0,
      28.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      41.0,
      28.0,
      18.0
     ],
     "text": "Set",
     "varname": "fs2_lbl_set"
    }
   },
   {
    "box": {
     "annotation": "Voces independientes. Apagado: todas las voces reciben la misma nota y solo cambian de octava y registro. Encendido: cada voz lee el set con su propio cursor, su Grado y su Div.",
     "id": "obj-10",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      20.0,
      369.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      19.0,
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
       "parameter_longname": "Indep",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Indep",
       "parameter_type": 2
      }
     },
     "varname": "fs2_indep"
    }
   },
   {
    "box": {
     "id": "obj-11",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      433.0,
      36.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      83.0,
      36.0,
      18.0
     ],
     "text": "Root",
     "varname": "fs2_lbl_root"
    }
   },
   {
    "box": {
     "annotation": "Elige el set de clases de altura del catalogo de Forte (1-351). Moverlo salta a ese set en el acto, aunque Lock este apagado.",
     "id": "obj-12",
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
      409.0,
      48.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      59.0,
      48.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Set",
       "parameter_mmax": 351.0,
       "parameter_mmin": 1.0,
       "parameter_modmode": 4,
       "parameter_shortname": "Set",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "fs2_set"
    }
   },
   {
    "box": {
     "annotation": "En que orden recorre el catalogo. Card: como se genera (cardinalidad y binario). Forte: el orden del catalogo de Forte. Cons: del set mas consonante al mas tenso, segun el vector interValico. Vec: encadenado por notas comunes, cada set comparte lo mas posible con el anterior.",
     "id": "obj-13",
     "maxclass": "live.tab",
     "numinlets": 1,
     "numoutlets": 3,
     "outlettype": [
      "",
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      60.0,
      369.0,
      168.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      40.0,
      19.0,
      168.0,
      18.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "Card",
        "Forte",
        "Cons",
        "Vec"
       ],
       "parameter_mmax": 3,
       "parameter_modmode": 0,
       "parameter_type": 2,
       "parameter_unitstyle": 9,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Orden",
       "parameter_shortname": "Orden"
      }
     },
     "varname": "fs2_orden"
    }
   },
   {
    "box": {
     "id": "obj-14",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      60.0,
      350.0,
      40.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      40.0,
      0.0,
      40.0,
      18.0
     ],
     "text": "Orden",
     "varname": "fs2_lbl_orden"
    }
   },
   {
    "box": {
     "id": "obj-15",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      72.0,
      391.0,
      32.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      52.0,
      41.0,
      32.0,
      18.0
     ],
     "text": "Lock",
     "varname": "fs2_lbl_lock"
    }
   },
   {
    "box": {
     "id": "obj-16",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      74.0,
      433.0,
      30.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      54.0,
      83.0,
      30.0,
      18.0
     ],
     "text": "Oct",
     "varname": "fs2_lbl_moct"
    }
   },
   {
    "box": {
     "annotation": "Transpone todo el device en octavas, de -5 a 5. Se suma a la octava de cada voz.",
     "id": "obj-17",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      74.0,
      451.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      54.0,
      101.0,
      44.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Oct Maestra",
       "parameter_mmax": 5.0,
       "parameter_mmin": -5.0,
       "parameter_modmode": 4,
       "parameter_shortname": "OctM",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "fs2_moct"
    }
   },
   {
    "box": {
     "annotation": "Fija el set elegido. Apagado, el motor va avanzando por el catalogo solo.",
     "id": "obj-18",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      74.0,
      409.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      54.0,
      59.0,
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
       "parameter_longname": "Lock",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Lock",
       "parameter_type": 2
      }
     },
     "varname": "fs2_lock"
    }
   },
   {
    "box": {
     "annotation": "Acordes: todas las notas del set suenan juntas. Arpegio: una nota por paso.",
     "id": "obj-19",
     "maxclass": "live.tab",
     "numinlets": 1,
     "numoutlets": 3,
     "outlettype": [
      "",
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      100.0,
      409.0,
      110.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      80.0,
      59.0,
      110.0,
      18.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "Acordes",
        "Arpegio"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Modo",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Modo",
       "parameter_type": 2,
       "parameter_unitstyle": 9
      }
     },
     "varname": "fs2_mode",
     "num_lines_patching": 1,
     "num_lines_presentation": 1
    }
   },
   {
    "box": {
     "id": "obj-20",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      108.0,
      391.0,
      40.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      88.0,
      41.0,
      40.0,
      18.0
     ],
     "text": "Modo",
     "varname": "fs2_lbl_modo"
    }
   },
   {
    "box": {
     "annotation": "Cada cuanto rota la forma del set. Apagado: una vez por pasada completa del catalogo. Encendido: en cada cambio de set.",
     "id": "obj-21",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      124.0,
      451.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      104.0,
      101.0,
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
       "parameter_longname": "Rotacion",
       "parameter_mmax": 1,
       "parameter_modmode": 0,
       "parameter_shortname": "Rot",
       "parameter_type": 2
      }
     },
     "varname": "fs2_rot"
    }
   },
   {
    "box": {
     "id": "obj-22",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      124.0,
      433.0,
      30.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      104.0,
      83.0,
      30.0,
      18.0
     ],
     "text": "Rot",
     "varname": "fs2_lbl_rot"
    }
   },
   {
    "box": {
     "id": "obj-23",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      172.0,
      433.0,
      68.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      152.0,
      83.0,
      68.0,
      18.0
     ],
     "text": "Set actual",
     "varname": "fs2_lbl_setnow"
    }
   },
   {
    "box": {
     "id": "obj-24",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      172.0,
      451.0,
      40.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      152.0,
      101.0,
      40.0,
      18.0
     ],
     "text": "1",
     "varname": "fs2_disp_idx"
    }
   },
   {
    "box": {
     "annotation": "En que orden se leen las notas del set. Normal: en orden ascendente. Super: todas las permutaciones. Minima: superpermutacion minima (solo hasta 5 notas). Modos: una pasada por cada modo, cada una empezando un grado mas arriba. Coprimo: salta de a N grados (ver Salto). Zigzag: la mas grave, la mas aguda, la segunda mas grave... Urna: al azar, pero sin repetir ninguna hasta haberlas tocado todas.",
     "id": "obj-25",
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
      216.0,
      409.0,
      90.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      196.0,
      59.0,
      90.0,
      18.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "Normal",
        "Super",
        "Minima",
        "Modos",
        "Coprimo",
        "Zigzag",
        "Urna"
       ],
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Perm",
       "parameter_mmax": 6,
       "parameter_modmode": 0,
       "parameter_shortname": "Perm",
       "parameter_type": 2,
       "parameter_unitstyle": 9
      }
     },
     "varname": "fs2_perm"
    }
   },
   {
    "box": {
     "id": "obj-26",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      216.0,
      391.0,
      50.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      196.0,
      41.0,
      50.0,
      18.0
     ],
     "text": "Lectura",
     "varname": "fs2_lbl_perm"
    }
   },
   {
    "box": {
     "annotation": "Enciende el filtro del catalogo: cardinalidad y mascara. Apagado, se recorren los 351 sets.",
     "id": "obj-27",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      234.0,
      369.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      214.0,
      19.0,
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
       "parameter_longname": "Filtro",
       "parameter_shortname": "Filtro"
      }
     },
     "varname": "fs2_filtro"
    }
   },
   {
    "box": {
     "id": "obj-28",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      234.0,
      350.0,
      38.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      214.0,
      0.0,
      38.0,
      18.0
     ],
     "text": "Filtro",
     "varname": "fs2_lbl_filtro"
    }
   },
   {
    "box": {
     "id": "obj-29",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      248.0,
      451.0,
      112.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      228.0,
      101.0,
      112.0,
      18.0
     ],
     "text": "--",
     "varname": "fs2_disp_forte",
     "fontsize": 10.0
    }
   },
   {
    "box": {
     "id": "obj-30",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      248.0,
      433.0,
      44.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      228.0,
      83.0,
      44.0,
      18.0
     ],
     "text": "Forte",
     "varname": "fs2_lbl_forte"
    }
   },
   {
    "box": {
     "id": "obj-31",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      276.0,
      350.0,
      38.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      256.0,
      0.0,
      38.0,
      18.0
     ],
     "text": "n min",
     "varname": "fs2_lbl_nmin"
    }
   },
   {
    "box": {
     "annotation": "Cardinalidad minima: cuantas notas tiene el set mas chico que se deja sonar.",
     "id": "obj-32",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      276.0,
      369.0,
      38.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      256.0,
      19.0,
      38.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 1.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "n min",
       "parameter_shortname": "n min"
      }
     },
     "varname": "fs2_nmin"
    }
   },
   {
    "box": {
     "annotation": "De cuantos grados es el salto en la lectura Coprimo. El motor lo corrige al valor coprimo mas cercano al pedido, que es lo unico que garantiza pasar por todos los grados antes de repetir. En un set de 7 notas, 2 es una cadena de terceras.",
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
      310.0,
      409.0,
      38.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      290.0,
      59.0,
      38.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 1.0,
       "parameter_mmax": 11.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        2
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Salto",
       "parameter_shortname": "Salto"
      }
     },
     "varname": "fs2_salto"
    }
   },
   {
    "box": {
     "id": "obj-34",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      310.0,
      391.0,
      38.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      290.0,
      41.0,
      38.0,
      18.0
     ],
     "text": "Salto",
     "varname": "fs2_lbl_salto"
    }
   },
   {
    "box": {
     "id": "obj-35",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      318.0,
      350.0,
      38.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      298.0,
      0.0,
      38.0,
      18.0
     ],
     "text": "n max",
     "varname": "fs2_lbl_nmax"
    }
   },
   {
    "box": {
     "annotation": "Cardinalidad maxima: cuantas notas tiene el set mas grande que se deja sonar.",
     "id": "obj-36",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      318.0,
      369.0,
      38.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      298.0,
      19.0,
      38.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 1.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        12
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "n max",
       "parameter_shortname": "n max"
      }
     },
     "varname": "fs2_nmax"
    }
   },
   {
    "box": {
     "id": "obj-37",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      596.0,
      660.0,
      92.0,
      22.0
     ],
     "text": "prepend setlockindex",
     "varname": "fs2_set_prep"
    }
   },
   {
    "box": {
     "id": "obj-38",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      692.0,
      660.0,
      92.0,
      22.0
     ],
     "text": "prepend setfilter",
     "varname": "fs2_filtro_prep"
    }
   },
   {
    "box": {
     "id": "obj-39",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      700.0,
      92.0,
      22.0
     ],
     "text": "prepend setpermmode",
     "varname": "fs2_perm_prep"
    }
   },
   {
    "box": {
     "id": "obj-40",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      116.0,
      700.0,
      92.0,
      22.0
     ],
     "text": "prepend setcardmax",
     "varname": "fs2_nmax_prep"
    }
   },
   {
    "box": {
     "id": "obj-41",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      212.0,
      700.0,
      92.0,
      22.0
     ],
     "text": "prepend setcardmin",
     "varname": "fs2_nmin_prep"
    }
   },
   {
    "box": {
     "id": "obj-42",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      308.0,
      700.0,
      92.0,
      22.0
     ],
     "text": "prepend setcoprime",
     "varname": "fs2_salto_prep"
    }
   },
   {
    "box": {
     "id": "obj-43",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      404.0,
      700.0,
      92.0,
      22.0
     ],
     "text": "prepend set",
     "varname": "fs2_disp_forte_prep"
    }
   },
   {
    "box": {
     "id": "obj-44",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      500.0,
      700.0,
      92.0,
      22.0
     ],
     "text": "prepend setroot",
     "varname": "fs2_root_prep"
    }
   },
   {
    "box": {
     "id": "obj-45",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      596.0,
      700.0,
      92.0,
      22.0
     ],
     "text": "prepend setmasteroctave",
     "varname": "fs2_moct_prep"
    }
   },
   {
    "box": {
     "id": "obj-46",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      692.0,
      700.0,
      92.0,
      22.0
     ],
     "text": "prepend setvoiceindep",
     "varname": "fs2_indep_prep"
    }
   },
   {
    "box": {
     "id": "obj-47",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      740.0,
      92.0,
      22.0
     ],
     "text": "prepend setshape",
     "varname": "fs2_rot_prep"
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
      116.0,
      740.0,
      92.0,
      22.0
     ],
     "text": "prepend setorder",
     "varname": "fs2_orden_prep"
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
      212.0,
      740.0,
      92.0,
      22.0
     ],
     "text": "prepend setlock",
     "varname": "fs2_lock_prep"
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
      308.0,
      740.0,
      92.0,
      22.0
     ],
     "text": "prepend setmode",
     "varname": "fs2_mode_prep"
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
      404.0,
      740.0,
      92.0,
      22.0
     ],
     "text": "prepend set",
     "varname": "fs2_disp_idx_prep"
    }
   },
   {
    "box": {
     "id": "obj-52",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      970.0,
      70.0,
      22.0
     ],
     "text": "outputvalue",
     "varname": "pg_init"
    }
   },
   {
    "box": {
     "id": "obj-53",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      1050.0,
      32.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      150.0,
      32.0,
      18.0
     ],
     "text": "Mask",
     "varname": "fs2_lbl_mask"
    }
   },
   {
    "box": {
     "annotation": "Celda 1 de la mascara: C. Las celdas son alturas absolutas, no dependen del Root.",
     "id": "obj-54",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      56.0,
      1050.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      36.0,
      150.0,
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
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask 1",
       "parameter_shortname": "Mk1"
      }
     },
     "varname": "fs2_mk1"
    }
   },
   {
    "box": {
     "annotation": "Celda 2 de la mascara: C#. Las celdas son alturas absolutas, no dependen del Root.",
     "id": "obj-55",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      71.0,
      1050.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      51.0,
      150.0,
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
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask 2",
       "parameter_shortname": "Mk2"
      }
     },
     "varname": "fs2_mk2"
    }
   },
   {
    "box": {
     "annotation": "Celda 3 de la mascara: D. Las celdas son alturas absolutas, no dependen del Root.",
     "id": "obj-56",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      86.0,
      1050.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      66.0,
      150.0,
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
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask 3",
       "parameter_shortname": "Mk3"
      }
     },
     "varname": "fs2_mk3"
    }
   },
   {
    "box": {
     "annotation": "Celda 4 de la mascara: D#. Las celdas son alturas absolutas, no dependen del Root.",
     "id": "obj-57",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      101.0,
      1050.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      81.0,
      150.0,
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
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask 4",
       "parameter_shortname": "Mk4"
      }
     },
     "varname": "fs2_mk4"
    }
   },
   {
    "box": {
     "annotation": "Celda 5 de la mascara: E. Las celdas son alturas absolutas, no dependen del Root.",
     "id": "obj-58",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      116.0,
      1050.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      96.0,
      150.0,
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
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask 5",
       "parameter_shortname": "Mk5"
      }
     },
     "varname": "fs2_mk5"
    }
   },
   {
    "box": {
     "annotation": "Celda 6 de la mascara: F. Las celdas son alturas absolutas, no dependen del Root.",
     "id": "obj-59",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      131.0,
      1050.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      111.0,
      150.0,
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
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask 6",
       "parameter_shortname": "Mk6"
      }
     },
     "varname": "fs2_mk6"
    }
   },
   {
    "box": {
     "annotation": "Celda 7 de la mascara: F#. Las celdas son alturas absolutas, no dependen del Root.",
     "id": "obj-60",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      146.0,
      1050.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      126.0,
      150.0,
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
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask 7",
       "parameter_shortname": "Mk7"
      }
     },
     "varname": "fs2_mk7"
    }
   },
   {
    "box": {
     "annotation": "Celda 8 de la mascara: G. Las celdas son alturas absolutas, no dependen del Root.",
     "id": "obj-61",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      161.0,
      1050.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      141.0,
      150.0,
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
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask 8",
       "parameter_shortname": "Mk8"
      }
     },
     "varname": "fs2_mk8"
    }
   },
   {
    "box": {
     "annotation": "Celda 9 de la mascara: G#. Las celdas son alturas absolutas, no dependen del Root.",
     "id": "obj-62",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      176.0,
      1050.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      156.0,
      150.0,
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
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask 9",
       "parameter_shortname": "Mk9"
      }
     },
     "varname": "fs2_mk9"
    }
   },
   {
    "box": {
     "annotation": "Celda 10 de la mascara: A. Las celdas son alturas absolutas, no dependen del Root.",
     "id": "obj-63",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      191.0,
      1050.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      171.0,
      150.0,
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
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask 10",
       "parameter_shortname": "Mk10"
      }
     },
     "varname": "fs2_mk10"
    }
   },
   {
    "box": {
     "annotation": "Celda 11 de la mascara: A#. Las celdas son alturas absolutas, no dependen del Root.",
     "id": "obj-64",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      206.0,
      1050.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      186.0,
      150.0,
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
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask 11",
       "parameter_shortname": "Mk11"
      }
     },
     "varname": "fs2_mk11"
    }
   },
   {
    "box": {
     "annotation": "Celda 12 de la mascara: B. Las celdas son alturas absolutas, no dependen del Root.",
     "id": "obj-65",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      221.0,
      1050.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      201.0,
      150.0,
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
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask 12",
       "parameter_shortname": "Mk12"
      }
     },
     "varname": "fs2_mk12"
    }
   },
   {
    "box": {
     "annotation": "Como se compara un set con la mascara. Sub: el set entra dentro de la mascara (mascara = escala). Con: el set contiene toda la mascara (mascara = intervalo obligatorio). Int: comparte al menos k notas con la mascara.",
     "id": "obj-66",
     "maxclass": "live.tab",
     "numinlets": 1,
     "numoutlets": 3,
     "outlettype": [
      "",
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      242.0,
      1050.0,
      90.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      222.0,
      150.0,
      90.0,
      18.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "Sub",
        "Con",
        "Int"
       ],
       "parameter_mmax": 2,
       "parameter_modmode": 0,
       "parameter_type": 2,
       "parameter_unitstyle": 9,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Modo Mask",
       "parameter_shortname": "Modo Mask"
      }
     },
     "varname": "fs2_maskmode"
    }
   },
   {
    "box": {
     "annotation": "Cuantas notas en comun exige el modo Int.",
     "id": "obj-67",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      336.0,
      1050.0,
      30.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      316.0,
      150.0,
      30.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 1.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask k",
       "parameter_shortname": "Mask k"
      }
     },
     "varname": "fs2_maskk"
    }
   },
   {
    "box": {
     "annotation": "Ajuste: si un set no cumple la mascara donde esta guardado, se lo transpone a donde si la cumple y suena ahi. Sin ajuste casi nada pasa el filtro (ni siquiera la escala diatonica pasa el filtro de su propia escala). Con ajuste, la mascara manda sobre el Root.",
     "id": "obj-68",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      370.0,
      1050.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      350.0,
      150.0,
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
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Mask Fit",
       "parameter_shortname": "Mask Fit"
      }
     },
     "varname": "fs2_maskfit"
    }
   },
   {
    "box": {
     "id": "obj-69",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      1320.0,
      92.0,
      22.0
     ],
     "text": "prepend setmaskmode",
     "varname": "fs2_maskmode_prep"
    }
   },
   {
    "box": {
     "id": "obj-70",
     "maxclass": "newobj",
     "numinlets": 12,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      116.0,
      1320.0,
      92.0,
      22.0
     ],
     "text": "pak 0 0 0 0 0 0 0 0 0 0 0 0",
     "varname": "fs2_mask_pak"
    }
   },
   {
    "box": {
     "id": "obj-71",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      212.0,
      1320.0,
      92.0,
      22.0
     ],
     "text": "prepend setmaskk",
     "varname": "fs2_maskk_prep"
    }
   },
   {
    "box": {
     "id": "obj-72",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      308.0,
      1320.0,
      92.0,
      22.0
     ],
     "text": "prepend setmask",
     "varname": "fs2_mask_prep"
    }
   },
   {
    "box": {
     "id": "obj-73",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      404.0,
      1320.0,
      92.0,
      22.0
     ],
     "text": "prepend setmaskfit",
     "varname": "fs2_maskfit_prep"
    }
   },
   {
    "box": {
     "id": "obj-74",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      1670.0,
      70.0,
      22.0
     ],
     "text": "outputvalue",
     "varname": "pg_init"
    }
   },
   {
    "box": {
     "id": "obj-75",
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
      1670.0,
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
     "id": "obj-76",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      20.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      423.0,
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
     "id": "obj-77",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      1791.0,
      52.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      341.0,
      52.0,
      18.0
     ],
     "text": "Acento",
     "varname": "fs2_alb_acc"
    }
   },
   {
    "box": {
     "id": "obj-78",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      1853.0,
      56.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      403.0,
      56.0,
      18.0
     ],
     "text": "Acentos",
     "varname": "fs2_alb_acentos"
    }
   },
   {
    "box": {
     "id": "obj-79",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      1769.0,
      52.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      319.0,
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
     "id": "obj-80",
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
      1831.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      381.0,
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
     "id": "obj-81",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      1813.0,
      38.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      363.0,
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
     "id": "obj-82",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      35.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      15.0,
      423.0,
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
     "id": "obj-83",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      50.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      30.0,
      423.0,
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
     "id": "obj-84",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      65.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      45.0,
      423.0,
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
     "id": "obj-85",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      76.0,
      1750.0,
      44.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      56.0,
      300.0,
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
     "id": "obj-86",
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
      1791.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      56.0,
      341.0,
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
     "id": "obj-87",
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
      1769.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      56.0,
      319.0,
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
     "id": "obj-88",
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
      1851.0,
      96.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      56.0,
      401.0,
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
     "id": "obj-89",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      80.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      60.0,
      423.0,
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
     "id": "obj-90",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      84.0,
      1831.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      64.0,
      381.0,
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
     "id": "obj-91",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      84.0,
      1813.0,
      62.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      64.0,
      363.0,
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
     "id": "obj-92",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      95.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      75.0,
      423.0,
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
     "id": "obj-93",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      110.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      90.0,
      423.0,
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
     "id": "obj-94",
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
      1769.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      104.0,
      319.0,
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
     "id": "obj-95",
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
      1791.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      104.0,
      341.0,
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
     "id": "obj-96",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      124.0,
      1750.0,
      44.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      104.0,
      300.0,
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
     "id": "obj-97",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      125.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      105.0,
      423.0,
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
     "id": "obj-98",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      140.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      120.0,
      423.0,
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
     "id": "obj-99",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      148.0,
      1831.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      128.0,
      381.0,
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
     "id": "obj-100",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      148.0,
      1813.0,
      32.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      128.0,
      363.0,
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
     "id": "obj-101",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      155.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      135.0,
      423.0,
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
     "id": "obj-102",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      170.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
      423.0,
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
     "id": "obj-103",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      172.0,
      1750.0,
      44.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      152.0,
      300.0,
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
     "id": "obj-104",
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
      1769.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      152.0,
      319.0,
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
     "id": "obj-105",
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
      1791.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      152.0,
      341.0,
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
     "id": "obj-106",
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
      1851.0,
      96.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      160.0,
      401.0,
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
     "id": "obj-107",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      184.0,
      1813.0,
      34.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      164.0,
      363.0,
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
     "id": "obj-108",
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
      1831.0,
      34.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      164.0,
      381.0,
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
     "id": "obj-109",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      185.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      165.0,
      423.0,
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
     "id": "obj-110",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      200.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      180.0,
      423.0,
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
     "id": "obj-111",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      215.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      195.0,
      423.0,
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
     "id": "obj-112",
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
      1769.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      200.0,
      319.0,
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
     "id": "obj-113",
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
      1791.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      200.0,
      341.0,
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
     "id": "obj-114",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      220.0,
      1750.0,
      44.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      200.0,
      300.0,
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
     "id": "obj-115",
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
      1831.0,
      30.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      202.0,
      381.0,
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
     "id": "obj-116",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      222.0,
      1813.0,
      26.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      202.0,
      363.0,
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
     "id": "obj-117",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      230.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      210.0,
      423.0,
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
     "id": "obj-118",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      245.0,
      1873.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      225.0,
      423.0,
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
     "id": "obj-119",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      308.0,
      2140.0,
      92.0,
      22.0
     ],
     "text": "prepend setaccenttie",
     "varname": "fs2_tie_prep"
    }
   },
   {
    "box": {
     "id": "obj-120",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      404.0,
      2140.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupsilence 0",
     "varname": "fs2_sil_n_prep"
    }
   },
   {
    "box": {
     "id": "obj-121",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      500.0,
      2140.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupdur 0",
     "varname": "fs2_fig_n_prep"
    }
   },
   {
    "box": {
     "id": "obj-122",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      596.0,
      2140.0,
      92.0,
      22.0
     ],
     "text": "prepend seteuclid",
     "varname": "fs2_euc_prep"
    }
   },
   {
    "box": {
     "id": "obj-123",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      692.0,
      2140.0,
      92.0,
      22.0
     ],
     "text": "prepend setrangetemplate",
     "varname": "fs2_rango_prep"
    }
   },
   {
    "box": {
     "id": "obj-124",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      2180.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupvelmax 1",
     "varname": "fs2_vmax_a_prep"
    }
   },
   {
    "box": {
     "id": "obj-125",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      116.0,
      2180.0,
      92.0,
      22.0
     ],
     "text": "prepend seteuclidk",
     "varname": "fs2_puls_prep"
    }
   },
   {
    "box": {
     "id": "obj-126",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      212.0,
      2180.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupsilence 1",
     "varname": "fs2_sil_a_prep"
    }
   },
   {
    "box": {
     "id": "obj-127",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      308.0,
      2180.0,
      92.0,
      22.0
     ],
     "text": "prepend setsilencepreset",
     "varname": "fs2_silpre_prep"
    }
   },
   {
    "box": {
     "id": "obj-128",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      404.0,
      2180.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupvelmin 1",
     "varname": "fs2_vmin_a_prep"
    }
   },
   {
    "box": {
     "id": "obj-129",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      500.0,
      2180.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupvelmin 0",
     "varname": "fs2_vmin_n_prep"
    }
   },
   {
    "box": {
     "id": "obj-130",
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
      2180.0,
      92.0,
      22.0
     ],
     "text": "unpack 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0",
     "varname": "fs2_acc_unpack"
    }
   },
   {
    "box": {
     "id": "obj-131",
     "maxclass": "newobj",
     "numinlets": 16,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      692.0,
      2180.0,
      92.0,
      22.0
     ],
     "text": "pak 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0",
     "varname": "fs2_accent_pak"
    }
   },
   {
    "box": {
     "id": "obj-132",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      2220.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupvelmax 0",
     "varname": "fs2_vmax_n_prep"
    }
   },
   {
    "box": {
     "id": "obj-133",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      116.0,
      2220.0,
      92.0,
      22.0
     ],
     "text": "prepend setaccentcycle",
     "varname": "fs2_ciclo_prep"
    }
   },
   {
    "box": {
     "id": "obj-134",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      212.0,
      2220.0,
      92.0,
      22.0
     ],
     "text": "prepend seteuclidrot",
     "varname": "fs2_gir_prep"
    }
   },
   {
    "box": {
     "id": "obj-135",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      308.0,
      2220.0,
      92.0,
      22.0
     ],
     "text": "prepend setgroupdur 1",
     "varname": "fs2_fig_a_prep"
    }
   },
   {
    "box": {
     "id": "obj-136",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "varname": "pg_accent_prep",
     "patching_rect": [
      692.0,
      2214.0,
      132.0,
      22.0
     ],
     "text": "prepend setaccentgrid"
    }
   },
   {
    "box": {
     "id": "obj-137",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      2370.0,
      70.0,
      22.0
     ],
     "text": "outputvalue",
     "varname": "pg_init"
    }
   },
   {
    "box": {
     "id": "obj-138",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 11,
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
      ""
     ],
     "patching_rect": [
      90.0,
      2370.0,
      520.0,
      22.0
     ],
     "text": "route drum drumbase harmrate rootseq voicing voicelead fav favonly vecmin vecmax",
     "varname": "pg_echo"
    }
   },
   {
    "box": {
     "annotation": "Como se reparte el acorde en modo Acordes. Extendido es el de siempre: las notas abiertas parejo sobre cuatro octavas. Cerrado las apila dentro de una. Drop 2 baja una octava la segunda voz desde arriba y Drop 3 la tercera, que es de donde sale el sonido de seccion de vientos; Drop 2+4 baja las dos. Abierto alterna una si una no. Un drop que no cabe en el acorde vuelve al cerrado en vez de hundir el bajo.",
     "id": "obj-139",
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
      20.0,
      2499.0,
      140.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      509.0,
      140.0,
      18.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "Extendido",
        "Cerrado",
        "Drop 2",
        "Drop 3",
        "Drop 2+4",
        "Abierto"
       ],
       "parameter_mmax": 5,
       "parameter_modmode": 0,
       "parameter_type": 2,
       "parameter_unitstyle": 9,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Voicing",
       "parameter_shortname": "Voic"
      }
     },
     "varname": "fs2_voic"
    }
   },
   {
    "box": {
     "id": "obj-140",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      2481.0,
      50.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      491.0,
      50.0,
      18.0
     ],
     "text": "Voicing",
     "varname": "fs2_lbl_voic"
    }
   },
   {
    "box": {
     "id": "obj-141",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      2440.0,
      30.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      450.0,
      30.0,
      18.0
     ],
     "text": "Drum",
     "varname": "fs2_lbl_drum"
    }
   },
   {
    "box": {
     "id": "obj-142",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      2523.0,
      54.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      533.0,
      54.0,
      18.0
     ],
     "text": "Raiz sec",
     "varname": "fs2_lbl_rseq"
    }
   },
   {
    "box": {
     "annotation": "Una raiz que camina en cada cambio armonico, encima del dial Raiz -- el dial sigue siendo el origen del paseo, asi que moverlo transporta la secuencia entera. Todas arrancan en 0, de modo que encender una no salta la armonia: el paseo empieza en el proximo cambio de set. Azar sortea una de las doce cada vez. Ojo con Ajuste: la secuencia manda, y el set se va de la mascara que lo dejaba pasar.",
     "id": "obj-143",
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
      20.0,
      2541.0,
      140.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      551.0,
      140.0,
      18.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_enum": [
        "Raiz fija",
        "Cuartas",
        "Quintas",
        "3as m",
        "3as M",
        "Tonos",
        "Cromatica",
        "Tritono",
        "I IV V",
        "Azar"
       ],
       "parameter_mmax": 9,
       "parameter_modmode": 0,
       "parameter_type": 2,
       "parameter_unitstyle": 9,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Sec Raiz",
       "parameter_shortname": "Sec Raiz"
      }
     },
     "varname": "fs2_rseq"
    }
   },
   {
    "box": {
     "annotation": "Cada clase de altura pasa a ser un pad de Drum Rack en vez de una nota: el set elige QUE tambores suenan y la lectura elige cuando. Mientras esta encendido, nada de lo que mueve una nota en vertical se aplica -- octavas, Oct global y el rango de cada voz quedan de adorno, porque un rack no tiene registros: sus filas son instrumentos distintos, y plegar al rango caeria en otro tambor, no en el mismo mas grave. La Raiz si cuenta: corre el set entero por el rack.",
     "id": "obj-144",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      20.0,
      2459.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      469.0,
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
       "parameter_longname": "Drum",
       "parameter_shortname": "Drum"
      }
     },
     "varname": "fs2_drum"
    }
   },
   {
    "box": {
     "id": "obj-145",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      50.0,
      2440.0,
      26.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      30.0,
      450.0,
      26.0,
      18.0
     ],
     "text": "Pad",
     "varname": "fs2_lbl_pad"
    }
   },
   {
    "box": {
     "annotation": "Que nota MIDI es el primer pad. 36 es C1, el de abajo a la izquierda de un Drum Rack de Live, y las doce clases de altura ocupan de ahi hacia arriba.",
     "id": "obj-146",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      50.0,
      2459.0,
      38.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      30.0,
      469.0,
      38.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 115.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        36
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Pad",
       "parameter_shortname": "Pad"
      }
     },
     "varname": "fs2_pad"
    }
   },
   {
    "box": {
     "id": "obj-147",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      90.0,
      2440.0,
      36.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      70.0,
      450.0,
      36.0,
      18.0
     ],
     "text": "R.Arm",
     "varname": "fs2_lbl_rarm"
    }
   },
   {
    "box": {
     "annotation": "Cada cuantos pasos cambia el set. En 0 manda la lectura, como siempre: el set cambia cuando termina la pasada. Con cualquier otro valor la armonia va por su cuenta, y ahi una lectura larga -- una superpermutacion, un ciclo de 720 pasos -- puede correr sobre acordes que cambian cada 4. Fijar le gana: un set congelado no se mueve.",
     "id": "obj-148",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      90.0,
      2459.0,
      38.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      70.0,
      469.0,
      38.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 64.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "Ritmo Arm",
       "parameter_shortname": "R.Arm"
      }
     },
     "varname": "fs2_rarm"
    }
   },
   {
    "box": {
     "id": "obj-149",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      130.0,
      2440.0,
      30.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      110.0,
      450.0,
      30.0,
      18.0
     ],
     "text": "Cond",
     "varname": "fs2_lbl_cond"
    }
   },
   {
    "box": {
     "annotation": "Conduccion de voces en modo Acordes. Al cambiar el set, prueba todas sus inversiones en todas las octavas al alcance y se queda con la que menos se mueve respecto del acorde que acaba de sonar. No cambia ninguna nota del set: elige inversion y octava. Con el rango de cada voz apretado el plegado puede deshacer parte del trabajo.",
     "id": "obj-150",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      130.0,
      2459.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      110.0,
      469.0,
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
       "parameter_longname": "Conduccion",
       "parameter_shortname": "Cond"
      }
     },
     "varname": "fs2_cond"
    }
   },
   {
    "box": {
     "id": "obj-151",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      170.0,
      2440.0,
      64.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
      450.0,
      64.0,
      18.0
     ],
     "text": "Vector min",
     "varname": "fs2_lbl_vmin"
    }
   },
   {
    "box": {
     "id": "obj-152",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      170.0,
      2562.0,
      60.0,
      18.0
     ],
     "text": "apilar",
     "varname": "fs2_apilar",
     "presentation": 1,
     "presentation_rect": [
      150.0,
      572.0,
      60.0,
      18.0
     ]
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de semitono (segunda menor) puede tener el set COMO MAXIMO; 12 no prohibe nada y 0 prohibe el intervalo entero -- ic1 max 0 es 'sin semitonos'. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
     "id": "obj-153",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      170.0,
      2499.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
      509.0,
      26.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        12
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "IC1 Max",
       "parameter_shortname": "IC1max"
      }
     },
     "varname": "fs2_vmx1"
    }
   },
   {
    "box": {
     "id": "obj-154",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      170.0,
      2481.0,
      64.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
      491.0,
      64.0,
      18.0
     ],
     "text": "Vector max",
     "varname": "fs2_lbl_vmax"
    }
   },
   {
    "box": {
     "id": "obj-155",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      170.0,
      2523.0,
      26.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
      533.0,
      26.0,
      18.0
     ],
     "text": "Fav",
     "varname": "fs2_lbl_fav"
    }
   },
   {
    "box": {
     "annotation": "Marca o desmarca el set que esta sonando en este momento, que es lo que hace utilizable el boton mientras uno navega: oir algo, marcarlo, seguir. El boton se repinta solo cada vez que la armonia cambia, asi que siempre dice si el set actual esta en la lista. La lista viaja con el Live set, no con los presets del device: recuperar un preset no borra una tarde de marcar.",
     "id": "obj-156",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      170.0,
      2541.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
      551.0,
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
       "parameter_longname": "Fav",
       "parameter_shortname": "Fav"
      }
     },
     "varname": "fs2_fav"
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de semitono (segunda menor) tiene que tener el set COMO MINIMO para pasar el filtro; 0 no exige nada. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
     "id": "obj-157",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      170.0,
      2459.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
      469.0,
      26.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "IC1 Min",
       "parameter_shortname": "IC1min"
      }
     },
     "varname": "fs2_vmn1"
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de tono (segunda mayor) puede tener el set COMO MAXIMO; 12 no prohibe nada y 0 prohibe el intervalo entero -- ic1 max 0 es 'sin semitonos'. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
     "id": "obj-158",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      197.0,
      2499.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      177.0,
      509.0,
      26.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        12
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "IC2 Max",
       "parameter_shortname": "IC2max"
      }
     },
     "varname": "fs2_vmx2"
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de tono (segunda mayor) tiene que tener el set COMO MINIMO para pasar el filtro; 0 no exige nada. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
     "id": "obj-159",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      197.0,
      2459.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      177.0,
      469.0,
      26.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "IC2 Min",
       "parameter_shortname": "IC2min"
      }
     },
     "varname": "fs2_vmn2"
    }
   },
   {
    "box": {
     "id": "obj-160",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      205.0,
      2523.0,
      32.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      185.0,
      533.0,
      32.0,
      18.0
     ],
     "text": "Solo",
     "varname": "fs2_lbl_favo"
    }
   },
   {
    "box": {
     "annotation": "El recorrido pisa unicamente los sets marcados. Es un filtro mas, no un modo aparte: se combina con la cardinalidad, el vector y la mascara en vez de reemplazarlos. Con la lista vacia no pasaria ningun set, asi que el device vuelve al catalogo entero y lo avisa por consola.",
     "id": "obj-161",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      205.0,
      2541.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      185.0,
      551.0,
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
       "parameter_longname": "Solo Fav",
       "parameter_shortname": "SoloFav"
      }
     },
     "varname": "fs2_favonly"
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de tercera menor puede tener el set COMO MAXIMO; 12 no prohibe nada y 0 prohibe el intervalo entero -- ic1 max 0 es 'sin semitonos'. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
     "id": "obj-162",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      224.0,
      2499.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      204.0,
      509.0,
      26.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        12
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "IC3 Max",
       "parameter_shortname": "IC3max"
      }
     },
     "varname": "fs2_vmx3"
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de tercera menor tiene que tener el set COMO MINIMO para pasar el filtro; 0 no exige nada. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
     "id": "obj-163",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      224.0,
      2459.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      204.0,
      469.0,
      26.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "IC3 Min",
       "parameter_shortname": "IC3min"
      }
     },
     "varname": "fs2_vmn3"
    }
   },
   {
    "box": {
     "id": "obj-164",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      236.0,
      2562.0,
      66.0,
      18.0
     ],
     "text": "unisono",
     "varname": "fs2_unisono",
     "presentation": 1,
     "presentation_rect": [
      216.0,
      572.0,
      66.0,
      18.0
     ]
    }
   },
   {
    "box": {
     "id": "obj-165",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      240.0,
      2541.0,
      66.0,
      18.0
     ],
     "text": "limpiar",
     "varname": "fs2_favclr_ui",
     "presentation": 1,
     "presentation_rect": [
      220.0,
      551.0,
      66.0,
      18.0
     ]
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de tercera mayor puede tener el set COMO MAXIMO; 12 no prohibe nada y 0 prohibe el intervalo entero -- ic1 max 0 es 'sin semitonos'. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
     "id": "obj-166",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      251.0,
      2499.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      231.0,
      509.0,
      26.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        12
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "IC4 Max",
       "parameter_shortname": "IC4max"
      }
     },
     "varname": "fs2_vmx4"
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de tercera mayor tiene que tener el set COMO MINIMO para pasar el filtro; 0 no exige nada. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
     "id": "obj-167",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      251.0,
      2459.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      231.0,
      469.0,
      26.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "IC4 Min",
       "parameter_shortname": "IC4min"
      }
     },
     "varname": "fs2_vmn4"
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de cuarta justa puede tener el set COMO MAXIMO; 12 no prohibe nada y 0 prohibe el intervalo entero -- ic1 max 0 es 'sin semitonos'. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
     "id": "obj-168",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      278.0,
      2499.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      258.0,
      509.0,
      26.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        12
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "IC5 Max",
       "parameter_shortname": "IC5max"
      }
     },
     "varname": "fs2_vmx5"
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de cuarta justa tiene que tener el set COMO MINIMO para pasar el filtro; 0 no exige nada. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
     "id": "obj-169",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      278.0,
      2459.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      258.0,
      469.0,
      26.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "IC5 Min",
       "parameter_shortname": "IC5min"
      }
     },
     "varname": "fs2_vmn5"
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de tritono tiene que tener el set COMO MINIMO para pasar el filtro; 0 no exige nada. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
     "id": "obj-170",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      305.0,
      2459.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      285.0,
      469.0,
      26.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "IC6 Min",
       "parameter_shortname": "IC6min"
      }
     },
     "varname": "fs2_vmn6"
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de tritono puede tener el set COMO MAXIMO; 12 no prohibe nada y 0 prohibe el intervalo entero -- ic1 max 0 es 'sin semitonos'. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
     "id": "obj-171",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      305.0,
      2499.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      285.0,
      509.0,
      26.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_mmin": 0.0,
       "parameter_mmax": 12.0,
       "parameter_modmode": 4,
       "parameter_type": 1,
       "parameter_unitstyle": 0,
       "parameter_initial": [
        12
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "IC6 Max",
       "parameter_shortname": "IC6max"
      }
     },
     "varname": "fs2_vmx6"
    }
   },
   {
    "box": {
     "id": "obj-172",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      116.0,
      2790.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmin 5",
     "varname": "fs2_vmn5_prep"
    }
   },
   {
    "box": {
     "id": "obj-173",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      212.0,
      2790.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmin 3",
     "varname": "fs2_vmn3_prep"
    }
   },
   {
    "box": {
     "id": "obj-174",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      308.0,
      2790.0,
      92.0,
      22.0
     ],
     "text": "prepend setvoicelead",
     "varname": "fs2_cond_prep"
    }
   },
   {
    "box": {
     "id": "obj-175",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      404.0,
      2790.0,
      92.0,
      22.0
     ],
     "text": "prepend setdrumbase",
     "varname": "fs2_pad_prep"
    }
   },
   {
    "box": {
     "id": "obj-176",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      500.0,
      2790.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmin 4",
     "varname": "fs2_vmn4_prep"
    }
   },
   {
    "box": {
     "id": "obj-177",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      596.0,
      2790.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmax 2",
     "varname": "fs2_vmx2_prep"
    }
   },
   {
    "box": {
     "id": "obj-178",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      692.0,
      2790.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmax 3",
     "varname": "fs2_vmx3_prep"
    }
   },
   {
    "box": {
     "id": "obj-179",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      2830.0,
      92.0,
      22.0
     ],
     "text": "prepend setfavonly",
     "varname": "fs2_favonly_prep"
    }
   },
   {
    "box": {
     "id": "obj-180",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 6,
     "outlettype": [
      "int",
      "int",
      "int",
      "int",
      "int",
      "int"
     ],
     "patching_rect": [
      116.0,
      2830.0,
      92.0,
      22.0
     ],
     "text": "unpack 0 0 0 0 0 0",
     "varname": "fs2_vecmax_unp"
    }
   },
   {
    "box": {
     "id": "obj-181",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      212.0,
      2830.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmax 1",
     "varname": "fs2_vmx1_prep"
    }
   },
   {
    "box": {
     "id": "obj-182",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      308.0,
      2830.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmax 5",
     "varname": "fs2_vmx5_prep"
    }
   },
   {
    "box": {
     "id": "obj-183",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      404.0,
      2830.0,
      92.0,
      22.0
     ],
     "text": "prepend setdrum",
     "varname": "fs2_drum_prep"
    }
   },
   {
    "box": {
     "id": "obj-184",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      500.0,
      2830.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmax 6",
     "varname": "fs2_vmx6_prep"
    }
   },
   {
    "box": {
     "id": "obj-185",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      596.0,
      2830.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmax 4",
     "varname": "fs2_vmx4_prep"
    }
   },
   {
    "box": {
     "id": "obj-186",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      692.0,
      2830.0,
      92.0,
      22.0
     ],
     "text": "prepend setrootseq",
     "varname": "fs2_rseq_prep"
    }
   },
   {
    "box": {
     "id": "obj-187",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      2870.0,
      92.0,
      22.0
     ],
     "text": "stackvoices 0",
     "varname": "fs2_unisono_msg"
    }
   },
   {
    "box": {
     "id": "obj-188",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      116.0,
      2870.0,
      92.0,
      22.0
     ],
     "text": "prepend setharmrate",
     "varname": "fs2_rarm_prep"
    }
   },
   {
    "box": {
     "id": "obj-189",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 6,
     "outlettype": [
      "int",
      "int",
      "int",
      "int",
      "int",
      "int"
     ],
     "patching_rect": [
      212.0,
      2870.0,
      92.0,
      22.0
     ],
     "text": "unpack 0 0 0 0 0 0",
     "varname": "fs2_vecmin_unp"
    }
   },
   {
    "box": {
     "id": "obj-190",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      308.0,
      2870.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmin 2",
     "varname": "fs2_vmn2_prep"
    }
   },
   {
    "box": {
     "id": "obj-191",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      404.0,
      2870.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmin 6",
     "varname": "fs2_vmn6_prep"
    }
   },
   {
    "box": {
     "id": "obj-192",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      500.0,
      2870.0,
      92.0,
      22.0
     ],
     "text": "stackvoices 1",
     "varname": "fs2_apilar_msg"
    }
   },
   {
    "box": {
     "id": "obj-193",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      596.0,
      2870.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmin 1",
     "varname": "fs2_vmn1_prep"
    }
   },
   {
    "box": {
     "id": "obj-194",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      692.0,
      2870.0,
      92.0,
      22.0
     ],
     "text": "prepend setvoicing",
     "varname": "fs2_voic_prep"
    }
   },
   {
    "box": {
     "id": "obj-195",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      2910.0,
      92.0,
      22.0
     ],
     "text": "prepend setfav",
     "varname": "fs2_fav_prep"
    }
   },
   {
    "box": {
     "id": "obj-196",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      116.0,
      2910.0,
      92.0,
      22.0
     ],
     "text": "clearfavs",
     "varname": "fs2_favclr"
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
      "obj-6",
      0
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
      "obj-37",
      0
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
      "obj-49",
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
      "obj-50",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-25",
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
      "obj-7",
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
      "obj-17",
      0
     ],
     "destination": [
      "obj-45",
      0
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
      "obj-47",
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
      "obj-24",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-10",
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
      "obj-13",
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
      "obj-27",
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
      "obj-32",
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
      "obj-36",
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
      "obj-43",
      0
     ],
     "destination": [
      "obj-29",
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
      "obj-42",
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
      "obj-5",
      0
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
      "obj-5",
      0
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
      "obj-5",
      0
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
      "obj-5",
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
      "obj-5",
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
      "obj-5",
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
      "obj-5",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-45",
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
      "obj-46",
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
      "obj-47",
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
      "obj-48",
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
      "obj-49",
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
      "obj-50",
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
      "obj-6",
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
      "obj-6",
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
      "obj-6",
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
      "obj-6",
      0
     ],
     "destination": [
      "obj-25",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-6",
      0
     ],
     "destination": [
      "obj-7",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-6",
      0
     ],
     "destination": [
      "obj-17",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-6",
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
      "obj-6",
      0
     ],
     "destination": [
      "obj-10",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-6",
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
      "obj-6",
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
      "obj-6",
      0
     ],
     "destination": [
      "obj-32",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-6",
      0
     ],
     "destination": [
      "obj-36",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-6",
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
      "obj-3",
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
      "obj-4",
      0
     ],
     "destination": [
      "obj-43",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-1",
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
      "obj-70",
      0
     ],
     "destination": [
      "obj-72",
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
      "obj-70",
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
      "obj-70",
      1
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
      "obj-70",
      2
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
      "obj-70",
      3
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
      "obj-70",
      4
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
      "obj-70",
      5
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
      "obj-70",
      6
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
      "obj-70",
      7
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
      "obj-70",
      8
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
      "obj-70",
      9
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
      "obj-70",
      10
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
      "obj-70",
      11
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
      "obj-69",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-67",
      0
     ],
     "destination": [
      "obj-71",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-68",
      0
     ],
     "destination": [
      "obj-73",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-69",
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
      "obj-71",
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
      "obj-72",
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
      "obj-73",
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
      "obj-52",
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
      "obj-52",
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
      "obj-52",
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
      "obj-52",
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
      "obj-52",
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
      "obj-52",
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
      "obj-52",
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
      "obj-52",
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
      "obj-52",
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
      "obj-52",
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
      "obj-52",
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
      "obj-52",
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
      "obj-52",
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
      "obj-52",
      0
     ],
     "destination": [
      "obj-67",
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
      "obj-68",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-1",
      0
     ],
     "destination": [
      "obj-74",
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
      "obj-75",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-87",
      0
     ],
     "destination": [
      "obj-129",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-94",
      0
     ],
     "destination": [
      "obj-132",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-104",
      0
     ],
     "destination": [
      "obj-121",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-112",
      0
     ],
     "destination": [
      "obj-120",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-86",
      0
     ],
     "destination": [
      "obj-128",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-95",
      0
     ],
     "destination": [
      "obj-124",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-105",
      0
     ],
     "destination": [
      "obj-135",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-113",
      0
     ],
     "destination": [
      "obj-126",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-80",
      0
     ],
     "destination": [
      "obj-133",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-90",
      0
     ],
     "destination": [
      "obj-119",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-76",
      0
     ],
     "destination": [
      "obj-131",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-82",
      0
     ],
     "destination": [
      "obj-131",
      1
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-83",
      0
     ],
     "destination": [
      "obj-131",
      2
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-84",
      0
     ],
     "destination": [
      "obj-131",
      3
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-89",
      0
     ],
     "destination": [
      "obj-131",
      4
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-92",
      0
     ],
     "destination": [
      "obj-131",
      5
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-93",
      0
     ],
     "destination": [
      "obj-131",
      6
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-97",
      0
     ],
     "destination": [
      "obj-131",
      7
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-98",
      0
     ],
     "destination": [
      "obj-131",
      8
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-101",
      0
     ],
     "destination": [
      "obj-131",
      9
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-102",
      0
     ],
     "destination": [
      "obj-131",
      10
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-109",
      0
     ],
     "destination": [
      "obj-131",
      11
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-110",
      0
     ],
     "destination": [
      "obj-131",
      12
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-111",
      0
     ],
     "destination": [
      "obj-131",
      13
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-117",
      0
     ],
     "destination": [
      "obj-131",
      14
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-118",
      0
     ],
     "destination": [
      "obj-131",
      15
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      0
     ],
     "destination": [
      "obj-76",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      1
     ],
     "destination": [
      "obj-82",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      2
     ],
     "destination": [
      "obj-83",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      3
     ],
     "destination": [
      "obj-84",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      4
     ],
     "destination": [
      "obj-89",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      5
     ],
     "destination": [
      "obj-92",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      6
     ],
     "destination": [
      "obj-93",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      7
     ],
     "destination": [
      "obj-97",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      8
     ],
     "destination": [
      "obj-98",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      9
     ],
     "destination": [
      "obj-101",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      10
     ],
     "destination": [
      "obj-102",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      11
     ],
     "destination": [
      "obj-109",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      12
     ],
     "destination": [
      "obj-110",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      13
     ],
     "destination": [
      "obj-111",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      14
     ],
     "destination": [
      "obj-117",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-130",
      15
     ],
     "destination": [
      "obj-118",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-99",
      0
     ],
     "destination": [
      "obj-122",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-108",
      0
     ],
     "destination": [
      "obj-125",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-115",
      0
     ],
     "destination": [
      "obj-134",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-106",
      0
     ],
     "destination": [
      "obj-123",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-88",
      0
     ],
     "destination": [
      "obj-127",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-119",
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
      "obj-120",
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
      "obj-121",
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
      "obj-122",
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
      "obj-123",
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
      "obj-124",
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
      "obj-125",
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
      "obj-126",
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
      "obj-127",
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
      "obj-128",
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
      "obj-129",
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
      "obj-132",
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
      "obj-133",
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
      "obj-134",
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
      "obj-135",
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
      "obj-74",
      0
     ],
     "destination": [
      "obj-87",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-94",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-104",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-112",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-86",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-95",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-105",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-113",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-80",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-90",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-76",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-82",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-83",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-84",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-89",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-92",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-93",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-97",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-98",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-101",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-102",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-109",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-110",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-111",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-117",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-118",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-99",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-108",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-74",
      0
     ],
     "destination": [
      "obj-115",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-75",
      0
     ],
     "destination": [
      "obj-130",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-75",
      1
     ],
     "destination": [
      "obj-112",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-75",
      2
     ],
     "destination": [
      "obj-113",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-75",
      3
     ],
     "destination": [
      "obj-99",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-75",
      4
     ],
     "destination": [
      "obj-108",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-75",
      5
     ],
     "destination": [
      "obj-115",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-131",
      0
     ],
     "destination": [
      "obj-136",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-136",
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
      "obj-1",
      0
     ],
     "destination": [
      "obj-137",
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
      "obj-138",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-144",
      0
     ],
     "destination": [
      "obj-183",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-146",
      0
     ],
     "destination": [
      "obj-175",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-148",
      0
     ],
     "destination": [
      "obj-188",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-150",
      0
     ],
     "destination": [
      "obj-174",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-139",
      0
     ],
     "destination": [
      "obj-194",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-143",
      0
     ],
     "destination": [
      "obj-186",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-165",
      0
     ],
     "destination": [
      "obj-196",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-157",
      0
     ],
     "destination": [
      "obj-193",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-153",
      0
     ],
     "destination": [
      "obj-181",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-159",
      0
     ],
     "destination": [
      "obj-190",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-158",
      0
     ],
     "destination": [
      "obj-177",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-163",
      0
     ],
     "destination": [
      "obj-173",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-162",
      0
     ],
     "destination": [
      "obj-178",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-167",
      0
     ],
     "destination": [
      "obj-176",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-166",
      0
     ],
     "destination": [
      "obj-185",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-169",
      0
     ],
     "destination": [
      "obj-172",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-168",
      0
     ],
     "destination": [
      "obj-182",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-170",
      0
     ],
     "destination": [
      "obj-191",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-171",
      0
     ],
     "destination": [
      "obj-184",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-156",
      0
     ],
     "destination": [
      "obj-195",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-161",
      0
     ],
     "destination": [
      "obj-179",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-189",
      0
     ],
     "destination": [
      "obj-157",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-189",
      1
     ],
     "destination": [
      "obj-159",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-189",
      2
     ],
     "destination": [
      "obj-163",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-189",
      3
     ],
     "destination": [
      "obj-167",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-189",
      4
     ],
     "destination": [
      "obj-169",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-189",
      5
     ],
     "destination": [
      "obj-170",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-180",
      0
     ],
     "destination": [
      "obj-153",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-180",
      1
     ],
     "destination": [
      "obj-158",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-180",
      2
     ],
     "destination": [
      "obj-162",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-180",
      3
     ],
     "destination": [
      "obj-166",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-180",
      4
     ],
     "destination": [
      "obj-168",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-180",
      5
     ],
     "destination": [
      "obj-171",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-152",
      0
     ],
     "destination": [
      "obj-192",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-164",
      0
     ],
     "destination": [
      "obj-187",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-172",
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
      "obj-173",
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
      "obj-174",
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
      "obj-175",
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
      "obj-176",
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
      "obj-177",
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
      "obj-178",
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
      "obj-179",
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
      "obj-181",
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
      "obj-182",
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
      "obj-183",
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
      "obj-184",
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
      "obj-185",
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
      "obj-186",
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
      "obj-187",
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
      "obj-188",
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
      "obj-190",
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
      "obj-191",
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
      "obj-192",
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
      "obj-193",
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
      "obj-194",
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
      "obj-195",
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
      "obj-196",
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
      "obj-137",
      0
     ],
     "destination": [
      "obj-144",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-146",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-148",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-150",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-139",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-143",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-157",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-153",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-159",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-158",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-163",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-162",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-167",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-166",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-169",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-168",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-170",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-171",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-137",
      0
     ],
     "destination": [
      "obj-161",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-138",
      0
     ],
     "destination": [
      "obj-144",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-138",
      1
     ],
     "destination": [
      "obj-146",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-138",
      2
     ],
     "destination": [
      "obj-148",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-138",
      3
     ],
     "destination": [
      "obj-143",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-138",
      4
     ],
     "destination": [
      "obj-139",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-138",
      5
     ],
     "destination": [
      "obj-150",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-138",
      6
     ],
     "destination": [
      "obj-156",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-138",
      7
     ],
     "destination": [
      "obj-161",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-138",
      8
     ],
     "destination": [
      "obj-189",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-138",
      9
     ],
     "destination": [
      "obj-180",
      0
     ]
    }
   }
  ],
  "parameters": {
   "obj-7": [
    "Root",
    "Root",
    0
   ],
   "obj-10": [
    "Indep",
    "Indep",
    0
   ],
   "obj-12": [
    "Set",
    "Set",
    0
   ],
   "obj-13": [
    "Orden",
    "Orden",
    0
   ],
   "obj-17": [
    "Oct Maestra",
    "Oct Maestra",
    0
   ],
   "obj-18": [
    "Lock",
    "Lock",
    0
   ],
   "obj-19": [
    "Modo",
    "Modo",
    0
   ],
   "obj-21": [
    "Rotacion",
    "Rotacion",
    0
   ],
   "obj-25": [
    "Perm",
    "Perm",
    0
   ],
   "obj-27": [
    "Filtro",
    "Filtro",
    0
   ],
   "obj-32": [
    "n min",
    "n min",
    0
   ],
   "obj-33": [
    "Salto",
    "Salto",
    0
   ],
   "obj-36": [
    "n max",
    "n max",
    0
   ],
   "obj-54": [
    "Mask 1",
    "Mask 1",
    0
   ],
   "obj-55": [
    "Mask 2",
    "Mask 2",
    0
   ],
   "obj-56": [
    "Mask 3",
    "Mask 3",
    0
   ],
   "obj-57": [
    "Mask 4",
    "Mask 4",
    0
   ],
   "obj-58": [
    "Mask 5",
    "Mask 5",
    0
   ],
   "obj-59": [
    "Mask 6",
    "Mask 6",
    0
   ],
   "obj-60": [
    "Mask 7",
    "Mask 7",
    0
   ],
   "obj-61": [
    "Mask 8",
    "Mask 8",
    0
   ],
   "obj-62": [
    "Mask 9",
    "Mask 9",
    0
   ],
   "obj-63": [
    "Mask 10",
    "Mask 10",
    0
   ],
   "obj-64": [
    "Mask 11",
    "Mask 11",
    0
   ],
   "obj-65": [
    "Mask 12",
    "Mask 12",
    0
   ],
   "obj-66": [
    "Modo Mask",
    "Modo Mask",
    0
   ],
   "obj-67": [
    "Mask k",
    "Mask k",
    0
   ],
   "obj-68": [
    "Mask Fit",
    "Mask Fit",
    0
   ],
   "obj-76": [
    "Acento 1",
    "Acento 1",
    0
   ],
   "obj-80": [
    "Ciclo Acentos",
    "Ciclo Acentos",
    0
   ],
   "obj-82": [
    "Acento 2",
    "Acento 2",
    0
   ],
   "obj-83": [
    "Acento 3",
    "Acento 3",
    0
   ],
   "obj-84": [
    "Acento 4",
    "Acento 4",
    0
   ],
   "obj-86": [
    "Vel Min Acento",
    "Vel Min Acento",
    0
   ],
   "obj-87": [
    "Vel Min Normal",
    "Vel Min Normal",
    0
   ],
   "obj-88": [
    "Preset Silencio",
    "Preset Silencio",
    0
   ],
   "obj-89": [
    "Acento 5",
    "Acento 5",
    0
   ],
   "obj-90": [
    "Ciclo igual a n",
    "Ciclo igual a n",
    0
   ],
   "obj-92": [
    "Acento 6",
    "Acento 6",
    0
   ],
   "obj-93": [
    "Acento 7",
    "Acento 7",
    0
   ],
   "obj-94": [
    "Vel Max Normal",
    "Vel Max Normal",
    0
   ],
   "obj-95": [
    "Vel Max Acento",
    "Vel Max Acento",
    0
   ],
   "obj-97": [
    "Acento 8",
    "Acento 8",
    0
   ],
   "obj-98": [
    "Acento 9",
    "Acento 9",
    0
   ],
   "obj-99": [
    "Euclid",
    "Euclid",
    0
   ],
   "obj-101": [
    "Acento 10",
    "Acento 10",
    0
   ],
   "obj-102": [
    "Acento 11",
    "Acento 11",
    0
   ],
   "obj-104": [
    "Figura Normal",
    "Figura Normal",
    0
   ],
   "obj-105": [
    "Figura Acento",
    "Figura Acento",
    0
   ],
   "obj-106": [
    "Rango",
    "Rango",
    0
   ],
   "obj-108": [
    "Pulsos",
    "Pulsos",
    0
   ],
   "obj-109": [
    "Acento 12",
    "Acento 12",
    0
   ],
   "obj-110": [
    "Acento 13",
    "Acento 13",
    0
   ],
   "obj-111": [
    "Acento 14",
    "Acento 14",
    0
   ],
   "obj-112": [
    "Silencio Normal",
    "Silencio Normal",
    0
   ],
   "obj-113": [
    "Silencio Acento",
    "Silencio Acento",
    0
   ],
   "obj-115": [
    "Giro",
    "Giro",
    0
   ],
   "obj-117": [
    "Acento 15",
    "Acento 15",
    0
   ],
   "obj-118": [
    "Acento 16",
    "Acento 16",
    0
   ],
   "obj-139": [
    "Voicing",
    "Voicing",
    0
   ],
   "obj-143": [
    "Sec Raiz",
    "Sec Raiz",
    0
   ],
   "obj-144": [
    "Drum",
    "Drum",
    0
   ],
   "obj-146": [
    "Pad",
    "Pad",
    0
   ],
   "obj-148": [
    "Ritmo Arm",
    "Ritmo Arm",
    0
   ],
   "obj-150": [
    "Conduccion",
    "Conduccion",
    0
   ],
   "obj-153": [
    "IC1 Max",
    "IC1 Max",
    0
   ],
   "obj-156": [
    "Fav",
    "Fav",
    0
   ],
   "obj-157": [
    "IC1 Min",
    "IC1 Min",
    0
   ],
   "obj-158": [
    "IC2 Max",
    "IC2 Max",
    0
   ],
   "obj-159": [
    "IC2 Min",
    "IC2 Min",
    0
   ],
   "obj-161": [
    "Solo Fav",
    "Solo Fav",
    0
   ],
   "obj-162": [
    "IC3 Max",
    "IC3 Max",
    0
   ],
   "obj-163": [
    "IC3 Min",
    "IC3 Min",
    0
   ],
   "obj-166": [
    "IC4 Max",
    "IC4 Max",
    0
   ],
   "obj-167": [
    "IC4 Min",
    "IC4 Min",
    0
   ],
   "obj-168": [
    "IC5 Max",
    "IC5 Max",
    0
   ],
   "obj-169": [
    "IC5 Min",
    "IC5 Min",
    0
   ],
   "obj-170": [
    "IC6 Min",
    "IC6 Min",
    0
   ],
   "obj-171": [
    "IC6 Max",
    "IC6 Max",
    0
   ]
  },
  "dependency_cache": [],
  "autosave": 0
 }
}