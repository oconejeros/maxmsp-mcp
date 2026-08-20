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
     "id": "obj-5",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      150.0,
      32.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      0.0,
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
     "id": "obj-6",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      56.0,
      150.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      36.0,
      0.0,
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
     "id": "obj-7",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      71.0,
      150.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      51.0,
      0.0,
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
     "id": "obj-8",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      86.0,
      150.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      66.0,
      0.0,
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
     "id": "obj-9",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      101.0,
      150.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      81.0,
      0.0,
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
     "id": "obj-10",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      116.0,
      150.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      96.0,
      0.0,
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
     "id": "obj-11",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      131.0,
      150.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      111.0,
      0.0,
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
     "id": "obj-12",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      146.0,
      150.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      126.0,
      0.0,
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
     "id": "obj-13",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      161.0,
      150.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      141.0,
      0.0,
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
     "id": "obj-14",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      176.0,
      150.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      156.0,
      0.0,
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
     "id": "obj-15",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      191.0,
      150.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      171.0,
      0.0,
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
     "id": "obj-16",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      206.0,
      150.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      186.0,
      0.0,
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
     "id": "obj-17",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      221.0,
      150.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      201.0,
      0.0,
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
     "id": "obj-18",
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
      150.0,
      90.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      222.0,
      0.0,
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
     "id": "obj-19",
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
      150.0,
      30.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      316.0,
      0.0,
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
     "id": "obj-20",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      370.0,
      150.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      350.0,
      0.0,
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
     "id": "obj-21",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      420.0,
      92.0,
      22.0
     ],
     "text": "prepend setmaskmode",
     "varname": "fs2_maskmode_prep"
    }
   },
   {
    "box": {
     "id": "obj-22",
     "maxclass": "newobj",
     "numinlets": 12,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      116.0,
      420.0,
      92.0,
      22.0
     ],
     "text": "pak 0 0 0 0 0 0 0 0 0 0 0 0",
     "varname": "fs2_mask_pak"
    }
   },
   {
    "box": {
     "id": "obj-23",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      212.0,
      420.0,
      92.0,
      22.0
     ],
     "text": "prepend setmaskk",
     "varname": "fs2_maskk_prep"
    }
   },
   {
    "box": {
     "id": "obj-24",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      308.0,
      420.0,
      92.0,
      22.0
     ],
     "text": "prepend setmask",
     "varname": "fs2_mask_prep"
    }
   },
   {
    "box": {
     "id": "obj-25",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      404.0,
      420.0,
      92.0,
      22.0
     ],
     "text": "prepend setmaskfit",
     "varname": "fs2_maskfit_prep"
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
      "obj-22",
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
      "obj-6",
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
      "obj-7",
      0
     ],
     "destination": [
      "obj-22",
      1
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
      "obj-22",
      2
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
      "obj-22",
      3
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
      "obj-22",
      4
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
      "obj-22",
      5
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
      "obj-22",
      6
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
      "obj-22",
      7
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-14",
      0
     ],
     "destination": [
      "obj-22",
      8
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
      "obj-22",
      9
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
      "obj-22",
      10
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
      "obj-22",
      11
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
      "obj-21",
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
      "obj-23",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-20",
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
      "obj-21",
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
      "obj-23",
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
      "obj-24",
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
      "obj-25",
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
      "obj-6",
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
      "obj-7",
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
      "obj-14",
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
      "obj-20",
      0
     ]
    }
   }
  ],
  "parameters": {
   "obj-6": [
    "Mask 1",
    "Mask 1",
    0
   ],
   "obj-7": [
    "Mask 2",
    "Mask 2",
    0
   ],
   "obj-8": [
    "Mask 3",
    "Mask 3",
    0
   ],
   "obj-9": [
    "Mask 4",
    "Mask 4",
    0
   ],
   "obj-10": [
    "Mask 5",
    "Mask 5",
    0
   ],
   "obj-11": [
    "Mask 6",
    "Mask 6",
    0
   ],
   "obj-12": [
    "Mask 7",
    "Mask 7",
    0
   ],
   "obj-13": [
    "Mask 8",
    "Mask 8",
    0
   ],
   "obj-14": [
    "Mask 9",
    "Mask 9",
    0
   ],
   "obj-15": [
    "Mask 10",
    "Mask 10",
    0
   ],
   "obj-16": [
    "Mask 11",
    "Mask 11",
    0
   ],
   "obj-17": [
    "Mask 12",
    "Mask 12",
    0
   ],
   "obj-18": [
    "Modo Mask",
    "Modo Mask",
    0
   ],
   "obj-19": [
    "Mask k",
    "Mask k",
    0
   ],
   "obj-20": [
    "Mask Fit",
    "Mask Fit",
    0
   ]
  },
  "dependency_cache": [],
  "autosave": 0
 }
}