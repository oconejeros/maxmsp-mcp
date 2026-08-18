{
 "patcher" : {
  "fileversion" : 1,
  "appversion" : {
   "major" : 9,
   "minor" : 0,
   "revision" : 7,
   "architecture" : "x64",
   "modernui" : 1
  },
  "classnamespace" : "box",
  "rect" : [
   100.0,
   100.0,
   960.0,
   420.0
  ],
  "openinpresentation" : 1,
  "default_fontsize" : 10.0,
  "default_fontname" : "Arial Bold",
  "gridsize" : [
   8.0,
   8.0
  ],
  "boxes" : [
   {
    "box" : {
     "id" : "obj-1",
     "maxclass" : "inlet",
     "numinlets" : 0,
     "numoutlets" : 1,
     "outlettype" : [
      ""
     ],
     "patching_rect" : [
      20.0,
      20.0,
      30.0,
      30.0
     ],
     "comment" : "init: re-emite el estado de los controles hacia el motor"
    }
   },
   {
    "box" : {
     "id" : "obj-13",
     "maxclass" : "message",
     "numinlets" : 2,
     "numoutlets" : 1,
     "outlettype" : [
      ""
     ],
     "patching_rect" : [
      20.0,
      70.0,
      70.0,
      22.0
     ],
     "text" : "outputvalue",
     "varname" : "v_init_msg"
    }
   },
   {
    "box" : {
     "id" : "obj-2",
     "maxclass" : "live.toggle",
     "numinlets" : 1,
     "numoutlets" : 1,
     "outlettype" : [
      ""
     ],
     "parameter_enable" : 1,
     "patching_rect" : [
      20.0,
      130.0,
      15.0,
      15.0
     ],
     "presentation" : 1,
     "presentation_rect" : [
      6.0,
      5.0,
      14.0,
      14.0
     ],
     "saved_attribute_attributes" : {
      "valueof" : {
       "parameter_longname" : "V#1 On",
       "parameter_shortname" : "On",
       "parameter_type" : 2,
       "parameter_initial" : [
        1
       ],
       "parameter_initial_enable" : 1,
       "parameter_enum" : [
        "off",
        "on"
       ],
       "parameter_mmax" : 1,
       "parameter_modmode" : 0
      }
     },
     "varname" : "v_on",
     "annotation" : "Enciende la voz #1. Una voz apagada esta muteada en el motor y no suena ni por el reloj ni por disparo externo."
    }
   },
   {
    "box" : {
     "id" : "obj-3",
     "maxclass" : "live.toggle",
     "numinlets" : 1,
     "numoutlets" : 1,
     "outlettype" : [
      ""
     ],
     "parameter_enable" : 1,
     "patching_rect" : [
      120.0,
      130.0,
      15.0,
      15.0
     ],
     "presentation" : 1,
     "presentation_rect" : [
      34.0,
      5.0,
      14.0,
      14.0
     ],
     "saved_attribute_attributes" : {
      "valueof" : {
       "parameter_longname" : "V#1 Ext",
       "parameter_shortname" : "Ext",
       "parameter_type" : 2,
       "parameter_initial" : [
        0
       ],
       "parameter_initial_enable" : 1,
       "parameter_enum" : [
        "off",
        "on"
       ],
       "parameter_mmax" : 1,
       "parameter_modmode" : 0
      }
     },
     "varname" : "v_ext",
     "annotation" : "Externa: el reloj compartido saltea esta voz y solo suena cuando un Hub en modo Enviar la dispara."
    }
   },
   {
    "box" : {
     "id" : "obj-4",
     "maxclass" : "live.numbox",
     "numinlets" : 1,
     "numoutlets" : 2,
     "outlettype" : [
      "",
      "float"
     ],
     "parameter_enable" : 1,
     "patching_rect" : [
      220.0,
      130.0,
      44.0,
      15.0
     ],
     "presentation" : 1,
     "presentation_rect" : [
      60.0,
      4.0,
      40.0,
      15.0
     ],
     "saved_attribute_attributes" : {
      "valueof" : {
       "parameter_longname" : "V#1 Oct",
       "parameter_shortname" : "Oct",
       "parameter_type" : 1,
       "parameter_initial" : [
        0
       ],
       "parameter_initial_enable" : 1,
       "parameter_mmin" : -4.0,
       "parameter_mmax" : 4.0,
       "parameter_modmode" : 4,
       "parameter_unitstyle" : 0
      }
     },
     "varname" : "v_oct",
     "annotation" : "Transposicion en octavas de esta voz, sobre el root y la octava maestra."
    }
   },
   {
    "box" : {
     "id" : "obj-5",
     "maxclass" : "live.numbox",
     "numinlets" : 1,
     "numoutlets" : 2,
     "outlettype" : [
      "",
      "float"
     ],
     "parameter_enable" : 1,
     "patching_rect" : [
      330.0,
      130.0,
      44.0,
      15.0
     ],
     "presentation" : 1,
     "presentation_rect" : [
      108.0,
      4.0,
      40.0,
      15.0
     ],
     "saved_attribute_attributes" : {
      "valueof" : {
       "parameter_longname" : "V#1 Fase",
       "parameter_shortname" : "Fase",
       "parameter_type" : 1,
       "parameter_initial" : [
        0
       ],
       "parameter_initial_enable" : 1,
       "parameter_mmin" : 0.0,
       "parameter_mmax" : 15.0,
       "parameter_modmode" : 4,
       "parameter_unitstyle" : 0
      }
     },
     "varname" : "v_fase",
     "annotation" : "Desplaza donde lee esta voz la grilla de acentos, para que no acentuen todas en el mismo punto."
    }
   },
   {
    "box" : {
     "id" : "obj-6",
     "maxclass" : "live.text",
     "numinlets" : 1,
     "numoutlets" : 2,
     "outlettype" : [
      "",
      ""
     ],
     "mode" : 1,
     "patching_rect" : [
      440.0,
      130.0,
      50.0,
      15.0
     ],
     "presentation" : 1,
     "presentation_rect" : [
      154.0,
      4.0,
      32.0,
      16.0
     ],
     "text" : "Trig",
     "varname" : "v_trig",
     "parameter_enable" : 0
    }
   },
   {
    "box" : {
     "id" : "obj-7",
     "maxclass" : "newobj",
     "numinlets" : 2,
     "numoutlets" : 1,
     "outlettype" : [
      "int"
     ],
     "patching_rect" : [
      20.0,
      180.0,
      40.0,
      22.0
     ],
     "text" : "== 0",
     "varname" : "v_on_inv"
    }
   },
   {
    "box" : {
     "id" : "obj-8",
     "maxclass" : "newobj",
     "numinlets" : 2,
     "numoutlets" : 1,
     "outlettype" : [
      ""
     ],
     "patching_rect" : [
      20.0,
      230.0,
      160.0,
      22.0
     ],
     "text" : "prepend setvoicemute #1",
     "varname" : "v_mute_prep"
    }
   },
   {
    "box" : {
     "id" : "obj-9",
     "maxclass" : "newobj",
     "numinlets" : 2,
     "numoutlets" : 1,
     "outlettype" : [
      ""
     ],
     "patching_rect" : [
      200.0,
      230.0,
      180.0,
      22.0
     ],
     "text" : "prepend setvoiceexternal #1",
     "varname" : "v_ext_prep"
    }
   },
   {
    "box" : {
     "id" : "obj-10",
     "maxclass" : "newobj",
     "numinlets" : 2,
     "numoutlets" : 1,
     "outlettype" : [
      ""
     ],
     "patching_rect" : [
      400.0,
      230.0,
      190.0,
      22.0
     ],
     "text" : "prepend setvoiceoctavelist #1",
     "varname" : "v_oct_prep"
    }
   },
   {
    "box" : {
     "id" : "obj-11",
     "maxclass" : "newobj",
     "numinlets" : 2,
     "numoutlets" : 1,
     "outlettype" : [
      ""
     ],
     "patching_rect" : [
      610.0,
      230.0,
      170.0,
      22.0
     ],
     "text" : "prepend setvoicephase #1",
     "varname" : "v_phase_prep"
    }
   },
   {
    "box" : {
     "id" : "obj-15",
     "maxclass" : "newobj",
     "numinlets" : 2,
     "numoutlets" : 2,
     "outlettype" : [
      "bang",
      ""
     ],
     "patching_rect" : [
      800.0,
      180.0,
      40.0,
      22.0
     ],
     "text" : "sel 1",
     "varname" : "v_trig_sel"
    }
   },
   {
    "box" : {
     "id" : "obj-12",
     "maxclass" : "message",
     "numinlets" : 2,
     "numoutlets" : 1,
     "outlettype" : [
      ""
     ],
     "patching_rect" : [
      800.0,
      230.0,
      110.0,
      22.0
     ],
     "text" : "triggervoice #1",
     "varname" : "v_trig_msg"
    }
   },
   {
    "box" : {
     "id" : "obj-14",
     "maxclass" : "outlet",
     "numinlets" : 1,
     "numoutlets" : 0,
     "patching_rect" : [
      20.0,
      300.0,
      30.0,
      30.0
     ],
     "comment" : "mensajes hacia [js forteseq2.js]"
    }
   },
   {
    "box" : {
     "id" : "obj-16",
     "maxclass" : "comment",
     "numinlets" : 1,
     "numoutlets" : 0,
     "patching_rect" : [
      20.0,
      360.0,
      560.0,
      20.0
     ],
     "text" : "Una tira por voz. El numero de voz llega como argumento #1 del bpatcher."
    }
   }
  ],
  "lines" : [
   {
    "patchline" : {
     "source" : [
      "obj-1",
      0
     ],
     "destination" : [
      "obj-13",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-13",
      0
     ],
     "destination" : [
      "obj-2",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-13",
      0
     ],
     "destination" : [
      "obj-3",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-13",
      0
     ],
     "destination" : [
      "obj-4",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-13",
      0
     ],
     "destination" : [
      "obj-5",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-2",
      0
     ],
     "destination" : [
      "obj-7",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-7",
      0
     ],
     "destination" : [
      "obj-8",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-8",
      0
     ],
     "destination" : [
      "obj-14",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-3",
      0
     ],
     "destination" : [
      "obj-9",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-9",
      0
     ],
     "destination" : [
      "obj-14",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-4",
      0
     ],
     "destination" : [
      "obj-10",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-10",
      0
     ],
     "destination" : [
      "obj-14",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-5",
      0
     ],
     "destination" : [
      "obj-11",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-11",
      0
     ],
     "destination" : [
      "obj-14",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-6",
      0
     ],
     "destination" : [
      "obj-15",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-15",
      0
     ],
     "destination" : [
      "obj-12",
      0
     ]
    }
   },
   {
    "patchline" : {
     "source" : [
      "obj-12",
      0
     ],
     "destination" : [
      "obj-14",
      0
     ]
    }
   }
  ],
  "parameters" : {
   "obj-2" : [
    "V#1 On",
    "V#1 On",
    0
   ],
   "obj-3" : [
    "V#1 Ext",
    "V#1 Ext",
    0
   ],
   "obj-4" : [
    "V#1 Oct",
    "V#1 Oct",
    0
   ],
   "obj-5" : [
    "V#1 Fase",
    "V#1 Fase",
    0
   ],
   "inherited_shortname" : 1
  },
  "dependency_cache" : [],
  "autosave" : 0
 }
}