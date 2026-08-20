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
     "id": "obj-51",
     "maxclass": "inlet",
     "numinlets": 0,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      160.0,
      20.0,
      30.0,
      30.0
     ],
     "comment": "fs2_gen, salida 1"
    }
   },
   {
    "box": {
     "id": "obj-52",
     "maxclass": "inlet",
     "numinlets": 0,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      230.0,
      20.0,
      30.0,
      30.0
     ],
     "comment": "fs2_gen, salida 7"
    }
   },
   {
    "box": {
     "annotation": "Transpone en semitonos, de -24 a 24.",
     "id": "obj-5",
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
      251.0,
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
     "id": "obj-6",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      150.0,
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
     "id": "obj-7",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      191.0,
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
     "id": "obj-8",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      20.0,
      169.0,
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
     "id": "obj-9",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      233.0,
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
     "id": "obj-10",
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
      209.0,
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
     "id": "obj-11",
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
      169.0,
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
     "id": "obj-12",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      60.0,
      150.0,
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
     "id": "obj-13",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      72.0,
      191.0,
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
     "id": "obj-14",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      74.0,
      233.0,
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
      74.0,
      251.0,
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
     "id": "obj-16",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      74.0,
      209.0,
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
     "id": "obj-17",
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
      209.0,
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
     "id": "obj-18",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      108.0,
      191.0,
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
     "id": "obj-19",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      124.0,
      251.0,
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
     "id": "obj-20",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      124.0,
      233.0,
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
     "id": "obj-21",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      172.0,
      233.0,
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
     "id": "obj-22",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      172.0,
      251.0,
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
     "id": "obj-23",
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
      209.0,
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
     "id": "obj-24",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      216.0,
      191.0,
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
     "id": "obj-25",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      234.0,
      169.0,
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
     "id": "obj-26",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      234.0,
      150.0,
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
     "id": "obj-27",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      248.0,
      251.0,
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
     "id": "obj-28",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      248.0,
      233.0,
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
     "id": "obj-29",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      276.0,
      150.0,
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
     "id": "obj-30",
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
      169.0,
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
     "id": "obj-31",
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
      209.0,
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
     "id": "obj-32",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      310.0,
      191.0,
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
     "id": "obj-33",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      318.0,
      150.0,
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
      318.0,
      169.0,
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
     "id": "obj-35",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      596.0,
      460.0,
      92.0,
      22.0
     ],
     "text": "prepend setlockindex",
     "varname": "fs2_set_prep"
    }
   },
   {
    "box": {
     "id": "obj-36",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      692.0,
      460.0,
      92.0,
      22.0
     ],
     "text": "prepend setfilter",
     "varname": "fs2_filtro_prep"
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
      20.0,
      500.0,
      92.0,
      22.0
     ],
     "text": "prepend setpermmode",
     "varname": "fs2_perm_prep"
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
      116.0,
      500.0,
      92.0,
      22.0
     ],
     "text": "prepend setcardmax",
     "varname": "fs2_nmax_prep"
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
      212.0,
      500.0,
      92.0,
      22.0
     ],
     "text": "prepend setcardmin",
     "varname": "fs2_nmin_prep"
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
      308.0,
      500.0,
      92.0,
      22.0
     ],
     "text": "prepend setcoprime",
     "varname": "fs2_salto_prep"
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
      404.0,
      500.0,
      92.0,
      22.0
     ],
     "text": "prepend set",
     "varname": "fs2_disp_forte_prep"
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
      500.0,
      500.0,
      92.0,
      22.0
     ],
     "text": "prepend setroot",
     "varname": "fs2_root_prep"
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
      596.0,
      500.0,
      92.0,
      22.0
     ],
     "text": "prepend setmasteroctave",
     "varname": "fs2_moct_prep"
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
      692.0,
      500.0,
      92.0,
      22.0
     ],
     "text": "prepend setvoiceindep",
     "varname": "fs2_indep_prep"
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
      20.0,
      540.0,
      92.0,
      22.0
     ],
     "text": "prepend setshape",
     "varname": "fs2_rot_prep"
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
      116.0,
      540.0,
      92.0,
      22.0
     ],
     "text": "prepend setorder",
     "varname": "fs2_orden_prep"
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
      212.0,
      540.0,
      92.0,
      22.0
     ],
     "text": "prepend setlock",
     "varname": "fs2_lock_prep"
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
     "text": "prepend setmode",
     "varname": "fs2_mode_prep"
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
     "text": "prepend set",
     "varname": "fs2_disp_idx_prep"
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
      "obj-10",
      0
     ],
     "destination": [
      "obj-35",
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
      "obj-47",
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
      "obj-48",
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
      "obj-37",
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
      "obj-42",
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
      "obj-43",
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
      "obj-45",
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
      "obj-22",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-8",
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
      "obj-11",
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
      "obj-25",
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
      "obj-30",
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
      "obj-34",
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
      "obj-41",
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
      "obj-31",
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
      "obj-35",
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
      "obj-36",
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
      "obj-37",
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
      "obj-38",
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
      "obj-39",
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
      "obj-40",
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
      "obj-42",
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
      "obj-43",
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
      "obj-44",
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
      "obj-45",
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
      "obj-46",
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
      "obj-47",
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
      "obj-4",
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
      "obj-17",
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
      "obj-8",
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
      "obj-25",
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
      "obj-31",
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
      "obj-49",
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
      "obj-41",
      0
     ]
    }
   }
  ],
  "parameters": {
   "obj-5": [
    "Root",
    "Root",
    0
   ],
   "obj-8": [
    "Indep",
    "Indep",
    0
   ],
   "obj-10": [
    "Set",
    "Set",
    0
   ],
   "obj-11": [
    "Orden",
    "Orden",
    0
   ],
   "obj-15": [
    "Oct Maestra",
    "Oct Maestra",
    0
   ],
   "obj-16": [
    "Lock",
    "Lock",
    0
   ],
   "obj-17": [
    "Modo",
    "Modo",
    0
   ],
   "obj-19": [
    "Rotacion",
    "Rotacion",
    0
   ],
   "obj-23": [
    "Perm",
    "Perm",
    0
   ],
   "obj-25": [
    "Filtro",
    "Filtro",
    0
   ],
   "obj-30": [
    "n min",
    "n min",
    0
   ],
   "obj-31": [
    "Salto",
    "Salto",
    0
   ],
   "obj-34": [
    "n max",
    "n max",
    0
   ]
  },
  "dependency_cache": [],
  "autosave": 0
 }
}