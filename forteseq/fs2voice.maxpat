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
   420.0
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
     "id": "obj-13",
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
     "varname": "v_init_msg"
    }
   },
   {
    "box": {
     "id": "obj-2",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      20.0,
      130.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      6.0,
      5.0,
      14.0,
      14.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_longname": "V#1 On",
       "parameter_shortname": "On",
       "parameter_type": 2,
       "parameter_initial": [
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_mmax": 1,
       "parameter_modmode": 0
      }
     },
     "varname": "v_on",
     "annotation": "Enciende la voz #1. Una voz apagada esta muteada en el motor y no suena ni por el reloj ni por disparo externo."
    }
   },
   {
    "box": {
     "id": "obj-3",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      120.0,
      130.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      34.0,
      5.0,
      14.0,
      14.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_longname": "V#1 Ext",
       "parameter_shortname": "Ext",
       "parameter_type": 2,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_enum": [
        "off",
        "on"
       ],
       "parameter_mmax": 1,
       "parameter_modmode": 0
      }
     },
     "varname": "v_ext",
     "annotation": "Externa: el reloj compartido saltea esta voz y solo suena cuando un Hub en modo Enviar la dispara."
    }
   },
   {
    "box": {
     "id": "obj-4",
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
      130.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      60.0,
      4.0,
      40.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_longname": "V#1 Oct",
       "parameter_shortname": "Oct",
       "parameter_type": 1,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_mmin": -4.0,
       "parameter_mmax": 4.0,
       "parameter_modmode": 4,
       "parameter_unitstyle": 0
      }
     },
     "varname": "v_oct",
     "annotation": "Octava base de esta voz, sobre el root y la octava maestra. El patron de octavas (Ev.N / O.Rng / Pasos) arranca desde aqui."
    }
   },
   {
    "box": {
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
      330.0,
      130.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      108.0,
      4.0,
      40.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_longname": "V#1 Fase",
       "parameter_shortname": "Fase",
       "parameter_type": 1,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_mmin": 0.0,
       "parameter_mmax": 15.0,
       "parameter_modmode": 4,
       "parameter_unitstyle": 0
      }
     },
     "varname": "v_fase",
     "annotation": "Desplaza donde lee esta voz la grilla de acentos, para que no acentuen todas en el mismo punto."
    }
   },
   {
    "box": {
     "id": "obj-6",
     "maxclass": "live.text",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      ""
     ],
     "mode": 1,
     "patching_rect": [
      440.0,
      130.0,
      50.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      154.0,
      4.0,
      32.0,
      16.0
     ],
     "text": "Trig",
     "varname": "v_trig",
     "parameter_enable": 0
    }
   },
   {
    "box": {
     "id": "obj-7",
     "maxclass": "newobj",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      "int"
     ],
     "patching_rect": [
      20.0,
      180.0,
      40.0,
      22.0
     ],
     "text": "== 0",
     "varname": "v_on_inv"
    }
   },
   {
    "box": {
     "id": "obj-8",
     "maxclass": "newobj",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      230.0,
      160.0,
      22.0
     ],
     "text": "prepend setvoicemute #1",
     "varname": "v_mute_prep"
    }
   },
   {
    "box": {
     "id": "obj-9",
     "maxclass": "newobj",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      200.0,
      230.0,
      180.0,
      22.0
     ],
     "text": "prepend setvoiceexternal #1",
     "varname": "v_ext_prep"
    }
   },
   {
    "box": {
     "id": "obj-11",
     "maxclass": "newobj",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      610.0,
      230.0,
      170.0,
      22.0
     ],
     "text": "prepend setvoicephase #1",
     "varname": "v_phase_prep"
    }
   },
   {
    "box": {
     "id": "obj-15",
     "maxclass": "newobj",
     "numinlets": 2,
     "numoutlets": 2,
     "outlettype": [
      "bang",
      ""
     ],
     "patching_rect": [
      800.0,
      180.0,
      40.0,
      22.0
     ],
     "text": "sel 1",
     "varname": "v_trig_sel"
    }
   },
   {
    "box": {
     "id": "obj-12",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      800.0,
      230.0,
      110.0,
      22.0
     ],
     "text": "triggervoice #1",
     "varname": "v_trig_msg"
    }
   },
   {
    "box": {
     "id": "obj-14",
     "maxclass": "outlet",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      300.0,
      30.0,
      30.0
     ],
     "comment": "mensajes hacia [js forteseq2.js]"
    }
   },
   {
    "box": {
     "id": "obj-16",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      360.0,
      560.0,
      20.0
     ],
     "text": "Una tira por voz. El numero de voz llega como argumento #1. Oct es la octava base del patron: con O.Rng en 0 la voz se queda fija en esa octava."
    }
   },
   {
    "box": {
     "annotation": "Nota MIDI mas grave del registro de esta voz.",
     "id": "obj-20",
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
      380.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      192.0,
      4.0,
      40.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        40
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "V#1 Min",
       "parameter_mmax": 127.0,
       "parameter_mmin": 0.0,
       "parameter_modmode": 4,
       "parameter_shortname": "Min",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "v_min"
    }
   },
   {
    "box": {
     "annotation": "Ancho en semitonos del registro de esta voz. Las notas que caen fuera se pliegan por octavas hasta entrar. 0 colapsa la voz a una sola nota.",
     "id": "obj-21",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "patching_rect": [
      80.0,
      380.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      236.0,
      4.0,
      40.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        17
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "V#1 Span",
       "parameter_mmax": 127.0,
       "parameter_mmin": 0.0,
       "parameter_modmode": 4,
       "parameter_shortname": "Span",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "v_span"
    }
   },
   {
    "box": {
     "id": "obj-25",
     "maxclass": "newobj",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      420.0,
      90.0,
      22.0
     ],
     "text": "pak 40 17",
     "varname": "v_range_pak"
    }
   },
   {
    "box": {
     "id": "obj-26",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      460.0,
      170.0,
      22.0
     ],
     "text": "prepend setvoicerange #1",
     "varname": "v_range_prep"
    }
   },
   {
    "box": {
     "annotation": "Cada cuantas notas avanza un escalon el patron de octavas de esta voz.",
     "id": "obj-22",
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
      380.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      280.0,
      4.0,
      34.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "V#1 Ev.N",
       "parameter_mmax": 16.0,
       "parameter_mmin": 1.0,
       "parameter_modmode": 4,
       "parameter_shortname": "EvN",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "v_evn"
    }
   },
   {
    "box": {
     "annotation": "Hasta cuantas octavas se aleja el patron. Negativo baja en vez de subir. 0 deja la voz en su octava fija.",
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
      280.0,
      380.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      318.0,
      4.0,
      34.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "V#1 O.Rng",
       "parameter_mmax": 4.0,
       "parameter_mmin": -4.0,
       "parameter_modmode": 4,
       "parameter_shortname": "ORng",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "v_orange"
    }
   },
   {
    "box": {
     "annotation": "Cuantos saltos hay entre 0 y el rango. Menos pasos = saltos mas grandes y menos graduales.",
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
      340.0,
      380.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      356.0,
      4.0,
      34.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_initial": [
        16
       ],
       "parameter_initial_enable": 1,
       "parameter_longname": "V#1 Pasos",
       "parameter_mmax": 16.0,
       "parameter_mmin": 1.0,
       "parameter_modmode": 4,
       "parameter_shortname": "Pasos",
       "parameter_type": 1,
       "parameter_unitstyle": 0
      }
     },
     "varname": "v_osteps"
    }
   },
   {
    "box": {
     "id": "obj-27",
     "maxclass": "newobj",
     "numinlets": 4,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      220.0,
      420.0,
      150.0,
      22.0
     ],
     "text": "pak 1 0 16 0",
     "varname": "v_oct_pak"
    }
   },
   {
    "box": {
     "id": "obj-28",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      220.0,
      460.0,
      220.0,
      22.0
     ],
     "text": "prepend setvoiceoctavesimple #1",
     "varname": "v_oct_prep"
    }
   },
   {
    "box": {
     "annotation": "Cuantos GRADOS del set queda esta voz por encima de su propia lectura. 0,1,2,3 en cuatro voces da un acorde a cuatro partes; negativo la pone debajo. Solo actua con Indep encendido.",
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
      420.0,
      380.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      392.0,
      4.0,
      32.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_longname": "V#1 Grado",
       "parameter_shortname": "Grado",
       "parameter_type": 1,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_mmin": -8.0,
       "parameter_mmax": 8.0,
       "parameter_modmode": 4,
       "parameter_unitstyle": 0
      }
     },
     "varname": "v_grado"
    }
   },
   {
    "box": {
     "id": "obj-31",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      510.0,
      220.0,
      22.0
     ],
     "text": "prepend setvoicedegoffset #1",
     "varname": "v_grado_prep"
    }
   },
   {
    "box": {
     "annotation": "Divisor de reloj: esta voz suena una vez cada N pasos y su cursor solo avanza cuando suena. Con divisores distintos las voces se desfasan y vuelven a juntarse en su multiplo comun. Solo actua con Indep encendido.",
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
      480.0,
      380.0,
      44.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      426.0,
      4.0,
      32.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_longname": "V#1 Div",
       "parameter_shortname": "Div",
       "parameter_type": 1,
       "parameter_initial": [
        1
       ],
       "parameter_initial_enable": 1,
       "parameter_mmin": 1.0,
       "parameter_mmax": 16.0,
       "parameter_modmode": 4,
       "parameter_unitstyle": 0
      }
     },
     "varname": "v_div"
    }
   },
   {
    "box": {
     "id": "obj-33",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      260.0,
      510.0,
      220.0,
      22.0
     ],
     "text": "prepend setvoicediv #1",
     "varname": "v_div_prep"
    }
   },
   {
    "box": {
     "id": "obj-34",
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
     "comment": "registro: min y span que el motor impone a esta voz",
     "varname": "v_range_in"
    }
   },
   {
    "box": {
     "id": "obj-35",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "int",
      "int"
     ],
     "patching_rect": [
      90.0,
      70.0,
      70.0,
      22.0
     ],
     "text": "unpack 0 0",
     "varname": "v_range_unpack"
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
      "obj-13",
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
      "obj-2",
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
      "obj-3",
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
      "obj-4",
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
      "obj-5",
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
      "obj-7",
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
      "obj-8",
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
      "obj-14",
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
      "obj-9",
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
      "obj-14",
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
      "obj-11",
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
      "obj-14",
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
      "obj-15",
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
      "obj-12",
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
      "obj-14",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-25",
      0
     ],
     "source": [
      "obj-20",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-25",
      1
     ],
     "source": [
      "obj-21",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-26",
      0
     ],
     "source": [
      "obj-25",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-14",
      0
     ],
     "source": [
      "obj-26",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-27",
      0
     ],
     "source": [
      "obj-22",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-27",
      1
     ],
     "source": [
      "obj-23",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-27",
      2
     ],
     "source": [
      "obj-24",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-27",
      3
     ],
     "source": [
      "obj-4",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-28",
      0
     ],
     "source": [
      "obj-27",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-14",
      0
     ],
     "source": [
      "obj-28",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-20",
      0
     ],
     "source": [
      "obj-13",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-21",
      0
     ],
     "source": [
      "obj-13",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-22",
      0
     ],
     "source": [
      "obj-13",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-23",
      0
     ],
     "source": [
      "obj-13",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-24",
      0
     ],
     "source": [
      "obj-13",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-30",
      0
     ],
     "source": [
      "obj-13",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-32",
      0
     ],
     "source": [
      "obj-13",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-31",
      0
     ],
     "source": [
      "obj-30",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-14",
      0
     ],
     "source": [
      "obj-31",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-33",
      0
     ],
     "source": [
      "obj-32",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-14",
      0
     ],
     "source": [
      "obj-33",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-35",
      0
     ],
     "source": [
      "obj-34",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-20",
      0
     ],
     "source": [
      "obj-35",
      0
     ]
    }
   },
   {
    "patchline": {
     "destination": [
      "obj-21",
      0
     ],
     "source": [
      "obj-35",
      1
     ]
    }
   }
  ],
  "parameters": {
   "obj-2": [
    "V#1 On",
    "V#1 On",
    0
   ],
   "obj-3": [
    "V#1 Ext",
    "V#1 Ext",
    0
   ],
   "obj-4": [
    "V#1 Oct",
    "V#1 Oct",
    0
   ],
   "obj-5": [
    "V#1 Fase",
    "V#1 Fase",
    0
   ],
   "inherited_shortname": 1,
   "obj-20": [
    "V#1 Min",
    "V#1 Min",
    0
   ],
   "obj-21": [
    "V#1 Span",
    "V#1 Span",
    0
   ],
   "obj-22": [
    "V#1 Ev.N",
    "V#1 Ev.N",
    0
   ],
   "obj-23": [
    "V#1 O.Rng",
    "V#1 O.Rng",
    0
   ],
   "obj-24": [
    "V#1 Pasos",
    "V#1 Pasos",
    0
   ],
   "obj-30": [
    "V#1 Grado",
    "V#1 Grado",
    0
   ],
   "obj-32": [
    "V#1 Div",
    "V#1 Div",
    0
   ]
  },
  "dependency_cache": [],
  "autosave": 0
 }
}