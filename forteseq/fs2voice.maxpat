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
      4.0,
      44.0,
      14.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      4.0,
      3.0,
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
      160.0,
      44.0,
      32.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      22.0,
      3.0,
      30.0,
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
      196.0,
      44.0,
      28.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      86.0,
      3.0,
      26.0,
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
      128.0,
      44.0,
      28.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      56.0,
      3.0,
      26.0,
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
     "id": "obj-36",
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
     "comment": "grado: el motor escribe el grado de esta voz (boton Apilar)",
     "varname": "v_grado_in"
    }
   },
   {
    "box": {
     "id": "obj-37",
     "maxclass": "live.numbox",
     "numinlets": 1,
     "numoutlets": 2,
     "outlettype": [
      "",
      "float"
     ],
     "parameter_enable": 1,
     "varname": "v_desf",
     "annotation": "Corrimiento fijo de esta voz, en sub-ticks: cuanto sale tarde respecto del paso. Es lo que convierte cuatro voces tocando el mismo ritmo en un conjunto que no esta del todo junto. Distinto de Fase, que corre que celda de la reja lee la voz y no cuando suena. Necesita Sub mayor que 1.",
     "patching_rect": [
      228.0,
      44.0,
      30.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      116.0,
      3.0,
      28.0,
      15.0
     ],
     "saved_attribute_attributes": {
      "valueof": {
       "parameter_longname": "V#1 Desf",
       "parameter_shortname": "Desf",
       "parameter_type": 1,
       "parameter_initial": [
        0
       ],
       "parameter_initial_enable": 1,
       "parameter_mmin": 0.0,
       "parameter_mmax": 7.0,
       "parameter_modmode": 4,
       "parameter_unitstyle": 0
      }
     }
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
     "varname": "v_desf_prep",
     "patching_rect": [
      500.0,
      510.0,
      240.0,
      22.0
     ],
     "text": "prepend setvoicetimeoffset #1"
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
      "obj-30",
      0
     ],
     "source": [
      "obj-36",
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
      "obj-37",
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
      "obj-38",
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
      "obj-14",
      0
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
   "obj-5": [
    "V#1 Fase",
    "V#1 Fase",
    0
   ],
   "inherited_shortname": 1,
   "obj-30": [
    "V#1 Grado",
    "V#1 Grado",
    0
   ],
   "obj-32": [
    "V#1 Div",
    "V#1 Div",
    0
   ],
   "obj-37": [
    "V#1 Desf",
    "V#1 Desf",
    0
   ]
  },
  "dependency_cache": [],
  "autosave": 0
 }
}