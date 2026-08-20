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
     "id": "obj-63",
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
      70.0,
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
     "id": "obj-5",
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
      199.0,
      140.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      59.0,
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
     "id": "obj-6",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20.0,
      181.0,
      50.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      41.0,
      50.0,
      18.0
     ],
     "text": "Voicing",
     "varname": "fs2_lbl_voic"
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
      140.0,
      30.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      0.0,
      30.0,
      18.0
     ],
     "text": "Drum",
     "varname": "fs2_lbl_drum"
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
      223.0,
      54.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      83.0,
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
     "id": "obj-9",
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
      241.0,
      140.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      0.0,
      101.0,
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
      159.0,
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
     "id": "obj-11",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      50.0,
      140.0,
      26.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      30.0,
      0.0,
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
      50.0,
      159.0,
      38.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      30.0,
      19.0,
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
     "id": "obj-13",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      90.0,
      140.0,
      36.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      70.0,
      0.0,
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
     "id": "obj-14",
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
      159.0,
      38.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      70.0,
      19.0,
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
     "id": "obj-15",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      130.0,
      140.0,
      30.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      110.0,
      0.0,
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
     "id": "obj-16",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      130.0,
      159.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      110.0,
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
       "parameter_longname": "Conduccion",
       "parameter_shortname": "Cond"
      }
     },
     "varname": "fs2_cond"
    }
   },
   {
    "box": {
     "id": "obj-17",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      170.0,
      140.0,
      64.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
      0.0,
      64.0,
      18.0
     ],
     "text": "Vector min",
     "varname": "fs2_lbl_vmin"
    }
   },
   {
    "box": {
     "id": "obj-18",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      170.0,
      262.0,
      60.0,
      18.0
     ],
     "text": "apilar",
     "varname": "fs2_apilar",
     "presentation": 1,
     "presentation_rect": [
      150.0,
      122.0,
      60.0,
      18.0
     ]
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de semitono (segunda menor) puede tener el set COMO MAXIMO; 12 no prohibe nada y 0 prohibe el intervalo entero -- ic1 max 0 es 'sin semitonos'. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
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
      170.0,
      199.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
      59.0,
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
     "id": "obj-20",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      170.0,
      181.0,
      64.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
      41.0,
      64.0,
      18.0
     ],
     "text": "Vector max",
     "varname": "fs2_lbl_vmax"
    }
   },
   {
    "box": {
     "id": "obj-21",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      170.0,
      223.0,
      26.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
      83.0,
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
     "id": "obj-22",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      170.0,
      241.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
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
      170.0,
      159.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      150.0,
      19.0,
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
      197.0,
      199.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      177.0,
      59.0,
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
     "id": "obj-25",
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
      159.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      177.0,
      19.0,
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
     "id": "obj-26",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      205.0,
      223.0,
      32.0,
      18.0
     ],
     "presentation": 1,
     "presentation_rect": [
      185.0,
      83.0,
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
     "id": "obj-27",
     "maxclass": "live.toggle",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "parameter_enable": 1,
     "patching_rect": [
      205.0,
      241.0,
      15.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      185.0,
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
     "id": "obj-28",
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
      199.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      204.0,
      59.0,
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
     "id": "obj-29",
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
      159.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      204.0,
      19.0,
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
     "id": "obj-30",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      236.0,
      262.0,
      66.0,
      18.0
     ],
     "text": "unisono",
     "varname": "fs2_unisono",
     "presentation": 1,
     "presentation_rect": [
      216.0,
      122.0,
      66.0,
      18.0
     ]
    }
   },
   {
    "box": {
     "id": "obj-31",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      240.0,
      241.0,
      66.0,
      18.0
     ],
     "text": "limpiar",
     "varname": "fs2_favclr_ui",
     "presentation": 1,
     "presentation_rect": [
      220.0,
      101.0,
      66.0,
      18.0
     ]
    }
   },
   {
    "box": {
     "annotation": "Cuantos intervalos de tercera mayor puede tener el set COMO MAXIMO; 12 no prohibe nada y 0 prohibe el intervalo entero -- ic1 max 0 es 'sin semitonos'. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
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
      251.0,
      199.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      231.0,
      59.0,
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
      251.0,
      159.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      231.0,
      19.0,
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
      278.0,
      199.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      258.0,
      59.0,
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
     "id": "obj-35",
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
      159.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      258.0,
      19.0,
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
      305.0,
      159.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      285.0,
      19.0,
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
      305.0,
      199.0,
      26.0,
      15.0
     ],
     "presentation": 1,
     "presentation_rect": [
      285.0,
      59.0,
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
     "id": "obj-38",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      116.0,
      490.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmin 5",
     "varname": "fs2_vmn5_prep"
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
      490.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmin 3",
     "varname": "fs2_vmn3_prep"
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
      490.0,
      92.0,
      22.0
     ],
     "text": "prepend setvoicelead",
     "varname": "fs2_cond_prep"
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
      490.0,
      92.0,
      22.0
     ],
     "text": "prepend setdrumbase",
     "varname": "fs2_pad_prep"
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
      490.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmin 4",
     "varname": "fs2_vmn4_prep"
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
      490.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmax 2",
     "varname": "fs2_vmx2_prep"
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
      490.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmax 3",
     "varname": "fs2_vmx3_prep"
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
      530.0,
      92.0,
      22.0
     ],
     "text": "prepend setfavonly",
     "varname": "fs2_favonly_prep"
    }
   },
   {
    "box": {
     "id": "obj-46",
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
      530.0,
      92.0,
      22.0
     ],
     "text": "unpack 0 0 0 0 0 0",
     "varname": "fs2_vecmax_unp"
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
      530.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmax 1",
     "varname": "fs2_vmx1_prep"
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
      530.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmax 5",
     "varname": "fs2_vmx5_prep"
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
      530.0,
      92.0,
      22.0
     ],
     "text": "prepend setdrum",
     "varname": "fs2_drum_prep"
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
      530.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmax 6",
     "varname": "fs2_vmx6_prep"
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
      530.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmax 4",
     "varname": "fs2_vmx4_prep"
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
      530.0,
      92.0,
      22.0
     ],
     "text": "prepend setrootseq",
     "varname": "fs2_rseq_prep"
    }
   },
   {
    "box": {
     "id": "obj-53",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      20.0,
      570.0,
      92.0,
      22.0
     ],
     "text": "stackvoices 0",
     "varname": "fs2_unisono_msg"
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
      570.0,
      92.0,
      22.0
     ],
     "text": "prepend setharmrate",
     "varname": "fs2_rarm_prep"
    }
   },
   {
    "box": {
     "id": "obj-55",
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
      570.0,
      92.0,
      22.0
     ],
     "text": "unpack 0 0 0 0 0 0",
     "varname": "fs2_vecmin_unp"
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
      570.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmin 2",
     "varname": "fs2_vmn2_prep"
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
      570.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmin 6",
     "varname": "fs2_vmn6_prep"
    }
   },
   {
    "box": {
     "id": "obj-58",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      500.0,
      570.0,
      92.0,
      22.0
     ],
     "text": "stackvoices 1",
     "varname": "fs2_apilar_msg"
    }
   },
   {
    "box": {
     "id": "obj-59",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      596.0,
      570.0,
      92.0,
      22.0
     ],
     "text": "prepend setvecmin 1",
     "varname": "fs2_vmn1_prep"
    }
   },
   {
    "box": {
     "id": "obj-60",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      692.0,
      570.0,
      92.0,
      22.0
     ],
     "text": "prepend setvoicing",
     "varname": "fs2_voic_prep"
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
      610.0,
      92.0,
      22.0
     ],
     "text": "prepend setfav",
     "varname": "fs2_fav_prep"
    }
   },
   {
    "box": {
     "id": "obj-62",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "outlettype": [
      ""
     ],
     "patching_rect": [
      116.0,
      610.0,
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
      "obj-63",
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
      "obj-49",
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
      "obj-41",
      0
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
      "obj-54",
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
      "obj-40",
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
      "obj-9",
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
      "obj-31",
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
      "obj-23",
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
      "obj-19",
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
      "obj-25",
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
      "obj-24",
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
      "obj-29",
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
      "obj-28",
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
      "obj-32",
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
      "obj-35",
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
      "obj-34",
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
      "obj-36",
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
      "obj-37",
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
      "obj-22",
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
      "obj-27",
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
      "obj-55",
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
      "obj-55",
      1
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
      "obj-55",
      2
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
      "obj-55",
      3
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
      "obj-55",
      4
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
      "obj-55",
      5
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
      "obj-46",
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
      "obj-46",
      1
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
      "obj-46",
      2
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
      "obj-46",
      3
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
      "obj-46",
      4
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
      "obj-46",
      5
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
      "obj-58",
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
      "obj-53",
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
      "obj-41",
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
      "obj-59",
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
      "obj-60",
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
      "obj-29",
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
      "obj-32",
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
      "obj-35",
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
      "obj-36",
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
      "obj-27",
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
      "obj-10",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "obj-63",
      1
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
      "obj-63",
      2
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
      "obj-63",
      3
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
      "obj-63",
      4
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
      "obj-63",
      5
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
      "obj-63",
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
      "obj-63",
      7
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
      "obj-63",
      8
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
      "obj-63",
      9
     ],
     "destination": [
      "obj-46",
      0
     ]
    }
   }
  ],
  "parameters": {
   "obj-5": [
    "Voicing",
    "Voicing",
    0
   ],
   "obj-9": [
    "Sec Raiz",
    "Sec Raiz",
    0
   ],
   "obj-10": [
    "Drum",
    "Drum",
    0
   ],
   "obj-12": [
    "Pad",
    "Pad",
    0
   ],
   "obj-14": [
    "Ritmo Arm",
    "Ritmo Arm",
    0
   ],
   "obj-16": [
    "Conduccion",
    "Conduccion",
    0
   ],
   "obj-19": [
    "IC1 Max",
    "IC1 Max",
    0
   ],
   "obj-22": [
    "Fav",
    "Fav",
    0
   ],
   "obj-23": [
    "IC1 Min",
    "IC1 Min",
    0
   ],
   "obj-24": [
    "IC2 Max",
    "IC2 Max",
    0
   ],
   "obj-25": [
    "IC2 Min",
    "IC2 Min",
    0
   ],
   "obj-27": [
    "Solo Fav",
    "Solo Fav",
    0
   ],
   "obj-28": [
    "IC3 Max",
    "IC3 Max",
    0
   ],
   "obj-29": [
    "IC3 Min",
    "IC3 Min",
    0
   ],
   "obj-32": [
    "IC4 Max",
    "IC4 Max",
    0
   ],
   "obj-33": [
    "IC4 Min",
    "IC4 Min",
    0
   ],
   "obj-34": [
    "IC5 Max",
    "IC5 Max",
    0
   ],
   "obj-35": [
    "IC5 Min",
    "IC5 Min",
    0
   ],
   "obj-36": [
    "IC6 Min",
    "IC6 Min",
    0
   ],
   "obj-37": [
    "IC6 Max",
    "IC6 Max",
    0
   ]
  },
  "dependency_cache": [],
  "autosave": 0
 }
}