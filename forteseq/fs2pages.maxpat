{
    "patcher": {
        "fileversion": 1,
        "appversion": {
            "major": 9,
            "minor": 1,
            "revision": 4,
            "architecture": "x64",
            "modernui": 1
        },
        "classnamespace": "box",
        "rect": [ 1570.0, 77.0, 1298.0, 609.0 ],
        "openinpresentation": 1,
        "default_fontsize": 10.0,
        "default_fontname": "Arial Bold",
        "gridsize": [ 8.0, 8.0 ],
        "boxes": [
            {
                "box": {
                    "comment": "init",
                    "id": "obj-1",
                    "index": 0,
                    "maxclass": "inlet",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 20.0, 30.0, 30.0 ]
                }
            },
            {
                "box": {
                    "comment": "eco (salida 4 del js)",
                    "id": "obj-2",
                    "index": 0,
                    "maxclass": "inlet",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 90.0, 20.0, 30.0, 30.0 ]
                }
            },
            {
                "box": {
                    "comment": "salida 1 del js",
                    "id": "obj-3",
                    "index": 0,
                    "maxclass": "inlet",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 160.0, 20.0, 30.0, 30.0 ]
                }
            },
            {
                "box": {
                    "comment": "salida 7 del js",
                    "id": "obj-4",
                    "index": 0,
                    "maxclass": "inlet",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 230.0, 20.0, 30.0, 30.0 ]
                }
            },
            {
                "box": {
                    "comment": "mensajes hacia [js forteseq2.js]",
                    "id": "obj-5",
                    "index": 0,
                    "maxclass": "outlet",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 90.0, 30.0, 30.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-6",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 270.0, 70.0, 20.0 ],
                    "text": "outputvalue",
                    "varname": "pg_init"
                }
            },
            {
                "box": {
                    "id": "obj-9",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 391.0, 28.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 5.0, 41.0, 28.0, 18.0 ],
                    "text": "Set",
                    "varname": "fs2_lbl_set"
                }
            },
            {
                "box": {
                    "annotation": "Elige el set de clases de altura del catalogo de Forte (1-351). Moverlo salta a ese set en el acto, aunque Lock este apagado.",
                    "id": "obj-12",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 20.0, 409.0, 48.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 0.0, 59.0, 48.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Set",
                            "parameter_mmax": 256.0,
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
                    "annotation": "Acordes: todas las notas del set suenan juntas. Arpegio: una nota por paso.",
                    "id": "obj-19",
                    "maxclass": "live.tab",
                    "num_lines_patching": 1,
                    "num_lines_presentation": 1,
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 100.0, 409.0, 110.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 54.0, 59.0, 110.0, 18.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "Acordes", "Arpegio" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Modo",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Modo",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
                        }
                    },
                    "varname": "fs2_mode"
                }
            },
            {
                "box": {
                    "id": "obj-20",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 108.0, 391.0, 40.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 59.0, 41.0, 40.0, 18.0 ],
                    "text": "Modo",
                    "varname": "fs2_lbl_modo"
                }
            },
            {
                "box": {
                    "id": "obj-31",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 276.0, 350.0, 38.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 14.0, 170.0, 34.0, 18.0 ],
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 276.0, 369.0, 38.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 14.0, 184.0, 34.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "n min",
                            "parameter_mmax": 12.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "n min",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_nmin"
                }
            },
            {
                "box": {
                    "id": "obj-35",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 318.0, 350.0, 38.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 52.0, 170.0, 36.0, 18.0 ],
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 318.0, 369.0, 38.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 52.0, 184.0, 34.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 12 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "n max",
                            "parameter_mmax": 12.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "n max",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 596.0, 660.0, 103.0, 20.0 ],
                    "text": "prepend setlockindex",
                    "varname": "fs2_set_prep"
                }
            },
            {
                "box": {
                    "id": "obj-40",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 116.0, 700.0, 100.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 212.0, 700.0, 97.0, 20.0 ],
                    "text": "prepend setcardmin",
                    "varname": "fs2_nmin_prep"
                }
            },
            {
                "box": {
                    "id": "obj-50",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 308.0, 740.0, 92.0, 20.0 ],
                    "text": "prepend setmode",
                    "varname": "fs2_mode_prep"
                }
            },
            {
                "box": {
                    "id": "obj-52",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 970.0, 70.0, 20.0 ],
                    "text": "outputvalue",
                    "varname": "pg_init[1]"
                }
            },
            {
                "box": {
                    "id": "obj-53",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 1050.0, 32.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 0.0, 150.0, 32.0, 18.0 ],
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 56.0, 1050.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 36.0, 150.0, 13.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask 1",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Mask 1",
                            "parameter_type": 2
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 71.0, 1050.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 49.0, 150.0, 13.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask 2",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Mask 2",
                            "parameter_type": 2
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 86.0, 1050.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 62.0, 150.0, 13.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask 3",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Mask 3",
                            "parameter_type": 2
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 101.0, 1050.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 75.0, 150.0, 13.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask 4",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Mask 4",
                            "parameter_type": 2
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 116.0, 1050.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 88.0, 150.0, 13.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask 5",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Mask 5",
                            "parameter_type": 2
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 131.0, 1050.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 101.0, 150.0, 13.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask 6",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Mask 6",
                            "parameter_type": 2
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 146.0, 1050.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 114.0, 150.0, 13.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask 7",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Mask 7",
                            "parameter_type": 2
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 161.0, 1050.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 127.0, 150.0, 13.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask 8",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Mask 8",
                            "parameter_type": 2
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 176.0, 1050.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 140.0, 150.0, 13.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask 9",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Mask 9",
                            "parameter_type": 2
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 191.0, 1050.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 153.0, 150.0, 13.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask 10",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Mask 10",
                            "parameter_type": 2
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 206.0, 1050.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 166.0, 150.0, 13.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask 11",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Mask 11",
                            "parameter_type": 2
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 221.0, 1050.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 179.0, 150.0, 13.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask 12",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Mask 12",
                            "parameter_type": 2
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
                    "num_lines_patching": 1,
                    "num_lines_presentation": 1,
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 242.0, 1050.0, 90.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 196.0, 150.0, 52.0, 18.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "Sub", "Con", "Int" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Modo Mask",
                            "parameter_mmax": 2,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Modo Mask",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 336.0, 1050.0, 30.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 214.0, 184.0, 26.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask k",
                            "parameter_mmax": 12.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Mask k",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 370.0, 1050.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 244.0, 184.0, 15.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Mask Fit",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Mask Fit",
                            "parameter_type": 2
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 1320.0, 110.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 116.0, 1320.0, 125.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 212.0, 1320.0, 92.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 308.0, 1320.0, 92.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 404.0, 1320.0, 93.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 1670.0, 70.0, 20.0 ],
                    "text": "outputvalue",
                    "varname": "pg_init[2]"
                }
            },
            {
                "box": {
                    "id": "obj-75",
                    "maxclass": "newobj",
                    "numinlets": 7,
                    "numoutlets": 7,
                    "outlettype": [ "", "", "", "", "", "", "" ],
                    "patching_rect": [ 90.0, 1670.0, 520.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 20.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ -2.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 1",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 1",
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
                    "patching_rect": [ 20.0, 1791.0, 52.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 0.0, 341.0, 52.0, 18.0 ],
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
                    "patching_rect": [ 20.0, 1853.0, 56.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 3.0, 389.0, 60.0, 18.0 ],
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
                    "patching_rect": [ 20.0, 1769.0, 52.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 0.0, 319.0, 52.0, 18.0 ],
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 20.0, 1831.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 6.0, 375.0, 44.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 4 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Ciclo Acentos",
                            "parameter_mmax": 16.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Ciclo Acentos",
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
                    "patching_rect": [ 20.0, 1813.0, 38.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 0.5, 357.0, 38.0, 18.0 ],
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 35.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 11.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 2",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 2",
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 50.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 24.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 3",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 3",
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 65.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 37.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 4",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 4",
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
                    "patching_rect": [ 76.0, 1750.0, 44.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 56.0, 300.0, 44.0, 18.0 ],
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 76.0, 1791.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 56.0, 341.0, 44.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 95 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Vel Min Acento",
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Vel Min Acento",
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 76.0, 1769.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 56.0, 319.0, 44.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 55 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Vel Min Normal",
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Vel Min Normal",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_vmin_n"
                }
            },
            {
                "box": {
                    "annotation": "Casilla 5 de la grilla de acentos. Encendida, ese paso del ciclo usa el grupo Acento en vez del Normal.",
                    "id": "obj-89",
                    "maxclass": "live.toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 80.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 50.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 5",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 5",
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 84.0, 1831.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 58.0, 375.0, 15.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Ciclo igual a n",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Ciclo igual a n",
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
                    "patching_rect": [ 84.0, 1813.0, 62.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 40.5, 357.0, 62.0, 18.0 ],
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 95.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 63.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 6",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 6",
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 110.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 76.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 7",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 7",
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 124.0, 1769.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 104.0, 319.0, 44.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 80 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Vel Max Normal",
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Vel Max Normal",
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 124.0, 1791.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 104.0, 341.0, 44.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 115 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Vel Max Acento",
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Vel Max Acento",
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
                    "patching_rect": [ 124.0, 1750.0, 44.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 104.0, 300.0, 44.0, 18.0 ],
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 125.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 89.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 8",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 8",
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 140.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 102.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 9",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 9",
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 148.0, 1831.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 85.0, 375.0, 15.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Euclid",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Euclid",
                            "parameter_type": 2
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
                    "patching_rect": [ 148.0, 1813.0, 32.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 85.0, 357.0, 32.0, 18.0 ],
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 155.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 115.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 10",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 10",
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 170.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 128.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 11",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 11",
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
                    "patching_rect": [ 172.0, 1750.0, 44.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 152.0, 300.0, 44.0, 18.0 ],
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 172.0, 1769.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 152.0, 319.0, 44.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 16 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Figura Normal",
                            "parameter_mmax": 32.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Figura Normal",
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 172.0, 1791.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 152.0, 341.0, 44.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 4 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Figura Acento",
                            "parameter_mmax": 32.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Figura Acento",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_fig_a"
                }
            },
            {
                "box": {
                    "id": "obj-107",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 184.0, 1813.0, 34.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 121.0, 357.0, 34.0, 18.0 ],
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 184.0, 1831.0, 34.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 121.0, 375.0, 34.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 4 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Pulsos",
                            "parameter_mmax": 16.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Pulsos",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 185.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 141.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 12",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 12",
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 200.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 154.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 13",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 13",
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 215.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 167.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 14",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 14",
                            "parameter_type": 2
                        }
                    },
                    "varname": "fs2_acc14"
                }
            },
            {
                "box": {
                    "annotation": "Desde que casilla arranca el patron. El mismo E(k,n) girado son ritmos distintos: es la diferencia entre la clave y su reverso.",
                    "id": "obj-115",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 222.0, 1831.0, 30.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 159.0, 375.0, 30.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Giro",
                            "parameter_mmax": 15.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Giro",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "patching_rect": [ 222.0, 1813.0, 26.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 159.0, 357.0, 26.0, 18.0 ],
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 230.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 180.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 15",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 15",
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 245.0, 1873.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 193.0, 405.0, 17.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Acento 16",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Acento 16",
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 308.0, 2140.0, 101.0, 20.0 ],
                    "text": "prepend setaccenttie",
                    "varname": "fs2_tie_prep"
                }
            },
            {
                "box": {
                    "id": "obj-121",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 500.0, 2140.0, 110.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 596.0, 2140.0, 92.0, 20.0 ],
                    "text": "prepend seteuclid",
                    "varname": "fs2_euc_prep"
                }
            },
            {
                "box": {
                    "id": "obj-124",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 2180.0, 127.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 116.0, 2180.0, 92.0, 20.0 ],
                    "text": "prepend seteuclidk",
                    "varname": "fs2_puls_prep"
                }
            },
            {
                "box": {
                    "id": "obj-128",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 404.0, 2180.0, 124.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 500.0, 2180.0, 124.0, 20.0 ],
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
                    "outlettype": [ "int", "int", "int", "int", "int", "int", "int", "int", "int", "int", "int", "int", "int", "int", "int", "int" ],
                    "patching_rect": [ 596.0, 2180.0, 174.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 692.0, 2180.0, 158.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 2220.0, 127.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 116.0, 2220.0, 114.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 212.0, 2220.0, 99.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 308.0, 2220.0, 110.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 692.0, 2214.0, 132.0, 20.0 ],
                    "text": "prepend setaccentgrid",
                    "varname": "pg_accent_prep"
                }
            },
            {
                "box": {
                    "id": "obj-137",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 2370.0, 70.0, 20.0 ],
                    "text": "outputvalue",
                    "varname": "pg_init[3]"
                }
            },
            {
                "box": {
                    "id": "obj-138",
                    "maxclass": "newobj",
                    "numinlets": 11,
                    "numoutlets": 11,
                    "outlettype": [ "", "", "", "", "", "", "", "", "", "", "" ],
                    "patching_rect": [ 90.0, 2370.0, 520.0, 20.0 ],
                    "text": "route drum drumbase harmrate rootseq voicing voicelead fav favonly vecmin vecmax",
                    "varname": "pg_echo[1]"
                }
            },
            {
                "box": {
                    "annotation": "Como se reparte el acorde en modo Acordes. Extendido es el de siempre: las notas abiertas parejo sobre cuatro octavas. Cerrado las apila dentro de una. Drop 2 baja una octava la segunda voz desde arriba y Drop 3 la tercera, que es de donde sale el sonido de seccion de vientos; Drop 2+4 baja las dos. Abierto alterna una si una no. Un drop que no cabe en el acorde vuelve al cerrado en vez de hundir el bajo.",
                    "id": "obj-139",
                    "maxclass": "live.menu",
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 20.0, 2499.0, 140.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 146.0, 19.0, 62.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "Extendido", "Cerrado", "Drop 2", "Drop 3", "Drop 2+4", "Abierto" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Voicing",
                            "parameter_mmax": 5,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Voicing",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
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
                    "patching_rect": [ 20.0, 2481.0, 50.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 146.0, 2.0, 62.0, 18.0 ],
                    "text": "Voicing",
                    "varname": "fs2_lbl_voic"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-141",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 2440.0, 33.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 122.0, 522.0, 34.0, 16.0 ],
                    "text": "Drum",
                    "varname": "fs2_lbl_drum"
                }
            },
            {
                "box": {
                    "annotation": "Cada clase de altura pasa a ser un pad de Drum Rack en vez de una nota: el set elige QUE tambores suenan y la lectura elige cuando. Mientras esta encendido, nada de lo que mueve una nota en vertical se aplica -- octavas, Oct global y el rango de cada voz quedan de adorno, porque un rack no tiene registros: sus filas son instrumentos distintos, y plegar al rango caeria en otro tambor, no en el mismo mas grave. La Raiz si cuenta: corre el set entero por el rack.",
                    "id": "obj-144",
                    "maxclass": "live.toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 20.0, 2459.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 122.0, 536.0, 15.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Drum",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Drum",
                            "parameter_type": 2
                        }
                    },
                    "varname": "fs2_drum"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-145",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 50.0, 2440.0, 26.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 158.0, 522.0, 32.0, 16.0 ],
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 50.0, 2459.0, 38.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 158.0, 536.0, 36.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 36 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Pad",
                            "parameter_mmax": 115.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Pad",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_pad"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-147",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 90.0, 2440.0, 37.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 196.0, 522.0, 40.0, 16.0 ],
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 90.0, 2459.0, 38.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 196.0, 536.0, 38.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Ritmo Arm",
                            "parameter_mmax": 64.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Ritmo Arm",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "patching_rect": [ 130.0, 2440.0, 32.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 45.0, 82.0, 32.0, 18.0 ],
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
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 130.0, 2459.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 47.0, 100.0, 15.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Conduccion",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Conduccion",
                            "parameter_type": 2
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
                    "patching_rect": [ 170.0, 2440.0, 64.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 9.0, 200.0, 90.0, 18.0 ],
                    "text": "Vector min",
                    "varname": "fs2_lbl_vmin"
                }
            },
            {
                "box": {
                    "annotation": "Cuantos intervalos de semitono (segunda menor) puede tener el set COMO MAXIMO; 12 no prohibe nada y 0 prohibe el intervalo entero -- ic1 max 0 es 'sin semitonos'. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
                    "id": "obj-153",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 170.0, 2499.0, 26.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 9.0, 246.0, 26.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 12 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "IC1 Max",
                            "parameter_mmax": 12.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "IC1 Max",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "patching_rect": [ 170.0, 2481.0, 64.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 9.0, 232.0, 90.0, 18.0 ],
                    "text": "Vector max",
                    "varname": "fs2_lbl_vmax"
                }
            },
            {
                "box": {
                    "annotation": "Cuantos intervalos de semitono (segunda menor) tiene que tener el set COMO MINIMO para pasar el filtro; 0 no exige nada. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
                    "id": "obj-157",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 170.0, 2459.0, 26.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 9.0, 214.0, 26.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "IC1 Min",
                            "parameter_mmax": 12.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "IC1 Min",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 197.0, 2499.0, 26.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 37.0, 246.0, 26.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 12 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "IC2 Max",
                            "parameter_mmax": 12.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "IC2 Max",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 197.0, 2459.0, 26.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 37.0, 214.0, 26.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "IC2 Min",
                            "parameter_mmax": 12.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "IC2 Min",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_vmn2"
                }
            },
            {
                "box": {
                    "annotation": "Cuantos intervalos de tercera menor puede tener el set COMO MAXIMO; 12 no prohibe nada y 0 prohibe el intervalo entero -- ic1 max 0 es 'sin semitonos'. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
                    "id": "obj-162",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 224.0, 2499.0, 26.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 65.0, 246.0, 26.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 12 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "IC3 Max",
                            "parameter_mmax": 12.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "IC3 Max",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 224.0, 2459.0, 26.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 65.0, 214.0, 26.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "IC3 Min",
                            "parameter_mmax": 12.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "IC3 Min",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_vmn3"
                }
            },
            {
                "box": {
                    "id": "obj-165",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 240.0, 2541.0, 66.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 3.0, 927.0, 60.0, 20.0 ],
                    "text": "limpiar",
                    "varname": "fs2_favclr_ui"
                }
            },
            {
                "box": {
                    "annotation": "Cuantos intervalos de tercera mayor puede tener el set COMO MAXIMO; 12 no prohibe nada y 0 prohibe el intervalo entero -- ic1 max 0 es 'sin semitonos'. El vector intervalico del display se lee de izquierda a derecha, ic1 a ic6: <001110> dice cuantos intervalos de cada clase tiene el set. No cambia al transportar, asi que esta condicion es la unica del filtro que el ajuste de mascara no puede esquivar: un set tiene esos intervalos o no los tiene, caiga donde caiga.",
                    "id": "obj-166",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 251.0, 2499.0, 26.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 93.0, 246.0, 26.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 12 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "IC4 Max",
                            "parameter_mmax": 12.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "IC4 Max",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 251.0, 2459.0, 26.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 93.0, 214.0, 26.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "IC4 Min",
                            "parameter_mmax": 12.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "IC4 Min",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 278.0, 2499.0, 26.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 121.0, 246.0, 26.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 12 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "IC5 Max",
                            "parameter_mmax": 12.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "IC5 Max",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 278.0, 2459.0, 26.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 121.0, 214.0, 26.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "IC5 Min",
                            "parameter_mmax": 12.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "IC5 Min",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 305.0, 2459.0, 26.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 149.0, 214.0, 26.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "IC6 Min",
                            "parameter_mmax": 12.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "IC6 Min",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 305.0, 2499.0, 26.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 149.0, 246.0, 26.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 12 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "IC6 Max",
                            "parameter_mmax": 12.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "IC6 Max",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 116.0, 2790.0, 101.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 212.0, 2790.0, 101.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 308.0, 2790.0, 104.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 404.0, 2790.0, 106.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 500.0, 2790.0, 101.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 596.0, 2790.0, 104.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 692.0, 2790.0, 104.0, 20.0 ],
                    "text": "prepend setvecmax 3",
                    "varname": "fs2_vmx3_prep"
                }
            },
            {
                "box": {
                    "id": "obj-180",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 6,
                    "outlettype": [ "int", "int", "int", "int", "int", "int" ],
                    "patching_rect": [ 116.0, 2830.0, 92.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 212.0, 2830.0, 104.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 308.0, 2830.0, 104.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 404.0, 2830.0, 92.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 500.0, 2830.0, 104.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 596.0, 2830.0, 104.0, 20.0 ],
                    "text": "prepend setvecmax 4",
                    "varname": "fs2_vmx4_prep"
                }
            },
            {
                "box": {
                    "id": "obj-188",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 116.0, 2870.0, 101.0, 20.0 ],
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
                    "outlettype": [ "int", "int", "int", "int", "int", "int" ],
                    "patching_rect": [ 212.0, 2870.0, 92.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 308.0, 2870.0, 101.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 404.0, 2870.0, 101.0, 20.0 ],
                    "text": "prepend setvecmin 6",
                    "varname": "fs2_vmn6_prep"
                }
            },
            {
                "box": {
                    "id": "obj-193",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 596.0, 2870.0, 101.0, 20.0 ],
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
                    "outlettype": [ "" ],
                    "patching_rect": [ 692.0, 2870.0, 92.0, 20.0 ],
                    "text": "prepend setvoicing",
                    "varname": "fs2_voic_prep"
                }
            },
            {
                "box": {
                    "id": "obj-196",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 116.0, 2910.0, 92.0, 20.0 ],
                    "text": "clearfavs",
                    "varname": "fs2_favclr"
                }
            },
            {
                "box": {
                    "comment": "el divisor de Sub, hacia el reloj",
                    "id": "obj-197",
                    "index": 0,
                    "maxclass": "outlet",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 90.0, 90.0, 30.0, 30.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-198",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 3000.0, 70.0, 20.0 ],
                    "text": "outputvalue",
                    "varname": "tp_init"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-201",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 84.0, 3040.0, 40.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 122.0, 452.0, 38.0, 16.0 ],
                    "text": "Swing",
                    "varname": "tp_lbl_swing"
                }
            },
            {
                "box": {
                    "annotation": "50 es recto. 66 es tresillo, el pulso par cae a dos tercios del camino. 75 es un balanceo con puntillo. Solo se mueve en sub-ticks enteros, asi que cuanto mas alto el Sub, mas fino el swing.",
                    "id": "obj-202",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 84.0, 3060.0, 40.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 122.0, 466.0, 38.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 50 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Swing",
                            "parameter_mmax": 75.0,
                            "parameter_mmin": 50.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Swing",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_swing"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-205",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 188.0, 3040.0, 38.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 164.0, 452.0, 36.0, 16.0 ],
                    "text": "Rasg",
                    "varname": "tp_lbl_rasg"
                }
            },
            {
                "box": {
                    "annotation": "Sub-ticks entre una nota y la siguiente de un mismo acorde. Con 0 el acorde se ataca junto. Ojo: se mide en sub-ticks, asi que en Sub 1 un rasgueo de 2 reparte el acorde en dos pasos enteros.",
                    "id": "obj-206",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 188.0, 3060.0, 38.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 164.0, 466.0, 36.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Rasg",
                            "parameter_mmax": 8.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Rasg",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_rasg"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-207",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 236.0, 3040.0, 150.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 204.0, 452.0, 60.0, 16.0 ],
                    "text": "Dir R",
                    "varname": "tp_lbl_dirrasg"
                }
            },
            {
                "box": {
                    "annotation": "Desde que nota se abre el acorde. Alterna cambia de sentido en cada paso.",
                    "id": "obj-208",
                    "maxclass": "live.tab",
                    "num_lines_patching": 1,
                    "num_lines_presentation": 1,
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 236.0, 3060.0, 150.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 204.0, 466.0, 80.0, 18.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "Arriba", "Abajo", "Azar", "Alt" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Dir Rasg",
                            "parameter_mmax": 3,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Dir Rasg",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
                        }
                    },
                    "varname": "fs2_dirrasg"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-209",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 3081.0, 38.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 122.0, 488.0, 38.0, 16.0 ],
                    "text": "Rat N",
                    "varname": "tp_lbl_ratn"
                }
            },
            {
                "box": {
                    "annotation": "Cuantas veces se repite una nota del grupo normal dentro de su paso. Necesita Sub mayor que 1: las repeticiones se reparten en los sub-ticks del paso.",
                    "id": "obj-210",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 20.0, 3101.0, 38.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 122.0, 502.0, 38.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Rat N",
                            "parameter_mmax": 4.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Rat N",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_ratn"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-211",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 68.0, 3081.0, 38.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 160.0, 488.0, 38.0, 16.0 ],
                    "text": "Rat A",
                    "varname": "tp_lbl_rata"
                }
            },
            {
                "box": {
                    "annotation": "Lo mismo para el grupo acento. Como la reja de 16 celdas decide que paso es acento, el redoble cae en las celdas que dibujaste y no en todas.",
                    "id": "obj-212",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 68.0, 3101.0, 38.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 160.0, 502.0, 38.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Rat A",
                            "parameter_mmax": 4.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Rat A",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_rata"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-213",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 116.0, 3081.0, 40.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 198.0, 488.0, 38.0, 16.0 ],
                    "text": "Prob",
                    "varname": "tp_lbl_ratprob"
                }
            },
            {
                "box": {
                    "annotation": "Cada cuanto el ratchet realmente dispara. En 100 siempre; en 30 uno de cada tres.",
                    "id": "obj-214",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 116.0, 3101.0, 40.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 198.0, 502.0, 38.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 100 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Prob Rat",
                            "parameter_mmax": 100.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Prob Rat",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_ratprob"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-215",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 168.0, 3081.0, 40.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 238.0, 488.0, 40.0, 16.0 ],
                    "text": "Caida",
                    "varname": "tp_lbl_ratcaida"
                }
            },
            {
                "box": {
                    "annotation": "Cuanta velocidad pierde el redoble entre la primera repeticion y la ultima.",
                    "id": "obj-216",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 168.0, 3101.0, 40.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 238.0, 502.0, 38.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Caida",
                            "parameter_mmax": 100.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Caida",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_ratcaida"
                }
            },
            {
                "box": {
                    "id": "obj-218",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 3200.0, 140.0, 20.0 ],
                    "text": "prepend setswing"
                }
            },
            {
                "box": {
                    "id": "obj-220",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 320.0, 3200.0, 140.0, 20.0 ],
                    "text": "prepend setstrum"
                }
            },
            {
                "box": {
                    "id": "obj-221",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 470.0, 3200.0, 140.0, 20.0 ],
                    "text": "prepend setstrumdir"
                }
            },
            {
                "box": {
                    "id": "obj-222",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 3230.0, 140.0, 20.0 ],
                    "text": "prepend setratchet 0"
                }
            },
            {
                "box": {
                    "id": "obj-223",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 170.0, 3230.0, 140.0, 20.0 ],
                    "text": "prepend setratchet 1"
                }
            },
            {
                "box": {
                    "id": "obj-224",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 320.0, 3230.0, 140.0, 20.0 ],
                    "text": "prepend setratchetprob"
                }
            },
            {
                "box": {
                    "id": "obj-225",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 470.0, 3230.0, 140.0, 20.0 ],
                    "text": "prepend setratchetdecay"
                }
            },
            {
                "box": {
                    "id": "obj-235",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 3700.0, 70.0, 20.0 ],
                    "text": "outputvalue",
                    "varname": "rt_init"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-236",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 60.0, 3740.0, 44.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 22.0, 463.0, 28.0, 16.0 ],
                    "text": "Larg"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-237",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 120.0, 3740.0, 44.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 54.0, 463.0, 28.0, 16.0 ],
                    "text": "Puls"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-238",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 180.0, 3740.0, 44.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 86.0, 463.0, 28.0, 16.0 ],
                    "text": "Gir"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-239",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 3802.0, 30.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 2.0, 477.0, 20.0, 16.0 ],
                    "text": "V1"
                }
            },
            {
                "box": {
                    "annotation": "Largo del patron de esta voz, en pasos. En 0 no hay patron y la voz suena en cada paso que le toca, que es lo que hacia antes de que esto existiera. Los largos que no comparten divisor son el punto: 3 contra 5 contra 7 contra 8 recien vuelve a alinearse a los 840 pasos, y hasta ahi cada paso es una combinacion distinta de quien habla.",
                    "id": "obj-240",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 60.0, 3802.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 22.0, 477.0, 28.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "V1 Larg",
                            "parameter_mmax": 16.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "V1 Larg",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "rt_v1_larg"
                }
            },
            {
                "box": {
                    "id": "obj-241",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 180.0, 3930.0, 220.0, 20.0 ],
                    "text": "prepend setvoiceeuclen 1"
                }
            },
            {
                "box": {
                    "annotation": "Cuantos golpes se reparten en esos pasos, lo mas parejo que el largo permita. E(3,8) es el tresillo cubano y E(5,8) el cinquillo. Con Puls en 0 la voz calla; con Puls igual o mayor que Larg suena en todos los pasos.",
                    "id": "obj-242",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 120.0, 3802.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 54.0, 477.0, 28.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "V1 Puls",
                            "parameter_mmax": 16.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "V1 Puls",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "rt_v1_puls"
                }
            },
            {
                "box": {
                    "id": "obj-243",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 420.0, 3930.0, 220.0, 20.0 ],
                    "text": "prepend setvoiceeuck 1"
                }
            },
            {
                "box": {
                    "annotation": "Desde que celda arranca el patron. Es lo que separa dos voces que llevan el mismo ritmo: el mismo E(3,8) girado 2 no cae nunca junto al sin girar.",
                    "id": "obj-244",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 180.0, 3802.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 86.0, 477.0, 28.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "V1 Gir",
                            "parameter_mmax": 15.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "V1 Gir",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "rt_v1_gir"
                }
            },
            {
                "box": {
                    "id": "obj-245",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 660.0, 3930.0, 220.0, 20.0 ],
                    "text": "prepend setvoiceeucrot 1"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-246",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 3824.0, 30.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 2.0, 501.0, 20.0, 16.0 ],
                    "text": "V2"
                }
            },
            {
                "box": {
                    "annotation": "Largo del patron de esta voz, en pasos. En 0 no hay patron y la voz suena en cada paso que le toca, que es lo que hacia antes de que esto existiera. Los largos que no comparten divisor son el punto: 3 contra 5 contra 7 contra 8 recien vuelve a alinearse a los 840 pasos, y hasta ahi cada paso es una combinacion distinta de quien habla.",
                    "id": "obj-247",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 60.0, 3824.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 22.0, 501.0, 28.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "V2 Larg",
                            "parameter_mmax": 16.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "V2 Larg",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "rt_v2_larg"
                }
            },
            {
                "box": {
                    "id": "obj-248",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 180.0, 3960.0, 220.0, 20.0 ],
                    "text": "prepend setvoiceeuclen 2"
                }
            },
            {
                "box": {
                    "annotation": "Cuantos golpes se reparten en esos pasos, lo mas parejo que el largo permita. E(3,8) es el tresillo cubano y E(5,8) el cinquillo. Con Puls en 0 la voz calla; con Puls igual o mayor que Larg suena en todos los pasos.",
                    "id": "obj-249",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 120.0, 3824.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 54.0, 501.0, 28.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "V2 Puls",
                            "parameter_mmax": 16.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "V2 Puls",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "rt_v2_puls"
                }
            },
            {
                "box": {
                    "id": "obj-250",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 420.0, 3960.0, 220.0, 20.0 ],
                    "text": "prepend setvoiceeuck 2"
                }
            },
            {
                "box": {
                    "annotation": "Desde que celda arranca el patron. Es lo que separa dos voces que llevan el mismo ritmo: el mismo E(3,8) girado 2 no cae nunca junto al sin girar.",
                    "id": "obj-251",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 180.0, 3824.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 86.0, 501.0, 28.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "V2 Gir",
                            "parameter_mmax": 15.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "V2 Gir",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "rt_v2_gir"
                }
            },
            {
                "box": {
                    "id": "obj-252",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 660.0, 3960.0, 220.0, 20.0 ],
                    "text": "prepend setvoiceeucrot 2"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-253",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 3846.0, 30.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 2.0, 525.0, 20.0, 16.0 ],
                    "text": "V3"
                }
            },
            {
                "box": {
                    "annotation": "Largo del patron de esta voz, en pasos. En 0 no hay patron y la voz suena en cada paso que le toca, que es lo que hacia antes de que esto existiera. Los largos que no comparten divisor son el punto: 3 contra 5 contra 7 contra 8 recien vuelve a alinearse a los 840 pasos, y hasta ahi cada paso es una combinacion distinta de quien habla.",
                    "id": "obj-254",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 60.0, 3846.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 22.0, 525.0, 28.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "V3 Larg",
                            "parameter_mmax": 16.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "V3 Larg",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "rt_v3_larg"
                }
            },
            {
                "box": {
                    "id": "obj-255",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 180.0, 3990.0, 220.0, 20.0 ],
                    "text": "prepend setvoiceeuclen 3"
                }
            },
            {
                "box": {
                    "annotation": "Cuantos golpes se reparten en esos pasos, lo mas parejo que el largo permita. E(3,8) es el tresillo cubano y E(5,8) el cinquillo. Con Puls en 0 la voz calla; con Puls igual o mayor que Larg suena en todos los pasos.",
                    "id": "obj-256",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 120.0, 3846.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 54.0, 525.0, 28.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "V3 Puls",
                            "parameter_mmax": 16.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "V3 Puls",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "rt_v3_puls"
                }
            },
            {
                "box": {
                    "id": "obj-257",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 420.0, 3990.0, 220.0, 20.0 ],
                    "text": "prepend setvoiceeuck 3"
                }
            },
            {
                "box": {
                    "annotation": "Desde que celda arranca el patron. Es lo que separa dos voces que llevan el mismo ritmo: el mismo E(3,8) girado 2 no cae nunca junto al sin girar.",
                    "id": "obj-258",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 180.0, 3846.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 86.0, 525.0, 28.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "V3 Gir",
                            "parameter_mmax": 15.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "V3 Gir",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "rt_v3_gir"
                }
            },
            {
                "box": {
                    "id": "obj-259",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 660.0, 3990.0, 220.0, 20.0 ],
                    "text": "prepend setvoiceeucrot 3"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-260",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 3868.0, 30.0, 16.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 2.0, 549.0, 20.0, 16.0 ],
                    "text": "V4"
                }
            },
            {
                "box": {
                    "annotation": "Largo del patron de esta voz, en pasos. En 0 no hay patron y la voz suena en cada paso que le toca, que es lo que hacia antes de que esto existiera. Los largos que no comparten divisor son el punto: 3 contra 5 contra 7 contra 8 recien vuelve a alinearse a los 840 pasos, y hasta ahi cada paso es una combinacion distinta de quien habla.",
                    "id": "obj-261",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 60.0, 3868.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 22.0, 549.0, 28.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "V4 Larg",
                            "parameter_mmax": 16.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "V4 Larg",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "rt_v4_larg"
                }
            },
            {
                "box": {
                    "id": "obj-262",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 180.0, 4020.0, 220.0, 20.0 ],
                    "text": "prepend setvoiceeuclen 4"
                }
            },
            {
                "box": {
                    "annotation": "Cuantos golpes se reparten en esos pasos, lo mas parejo que el largo permita. E(3,8) es el tresillo cubano y E(5,8) el cinquillo. Con Puls en 0 la voz calla; con Puls igual o mayor que Larg suena en todos los pasos.",
                    "id": "obj-263",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 120.0, 3868.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 54.0, 549.0, 28.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "V4 Puls",
                            "parameter_mmax": 16.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "V4 Puls",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "rt_v4_puls"
                }
            },
            {
                "box": {
                    "id": "obj-264",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 420.0, 4020.0, 220.0, 20.0 ],
                    "text": "prepend setvoiceeuck 4"
                }
            },
            {
                "box": {
                    "annotation": "Desde que celda arranca el patron. Es lo que separa dos voces que llevan el mismo ritmo: el mismo E(3,8) girado 2 no cae nunca junto al sin girar.",
                    "id": "obj-265",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 180.0, 3868.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 86.0, 549.0, 28.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "V4 Gir",
                            "parameter_mmax": 15.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "V4 Gir",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "rt_v4_gir"
                }
            },
            {
                "box": {
                    "id": "obj-266",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 660.0, 4020.0, 220.0, 20.0 ],
                    "text": "prepend setvoiceeucrot 4"
                }
            },
            {
                "box": {
                    "id": "obj-267",
                    "linecount": 9,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 600.0, 3740.0, 292.0, 110.0 ],
                    "text": "Cada voz lleva su propio E(Puls, Larg). La reja de acentos decide con cuanta fuerza habla una voz; esto decide si habla. Una celda apagada es una compuerta, no una pausa: el cursor de la voz igual avanza, asi que la voz guarda su lugar en la armonia en vez de tocar una melodia mas lenta. Con Indep encendido el patron se lee contra los pasos que el divisor le entrega a la voz, no contra el reloj, para que un divisor y un patron no puedan caer en celdas distintas y callarla para siempre.",
                    "varname": "rt_nota"
                }
            },
            {
                "box": {
                    "id": "obj-268",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 4400.0, 70.0, 20.0 ],
                    "text": "outputvalue",
                    "varname": "cm_init"
                }
            },
            {
                "box": {
                    "id": "obj-281",
                    "linecount": 4,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 4570.0, 512.0, 52.0 ],
                    "text": "Las tres reglas se pisan en este orden: Prog manda sobre Tension, y Tension sobre el recorrido normal del catalogo. Enlace se aplica a las dos ultimas pero nunca a Prog. Ninguna de las tres hace nada mientras la armonia no se mueva, asi que se escuchan sobre todo con Ritmo Arm. -- en la pagina Musical -- o con pasadas cortas.",
                    "varname": "cm_nota"
                }
            },
            {
                "box": {
                    "id": "obj-282",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 5100.0, 70.0, 20.0 ],
                    "text": "outputvalue",
                    "varname": "es_init"
                }
            },
            {
                "box": {
                    "id": "obj-283",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 5140.0, 70.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 6.0, 767.0, 70.0, 18.0 ],
                    "text": "Escuchar"
                }
            },
            {
                "box": {
                    "annotation": "Off: el device no escucha. Sigue: mientras sostengas notas, la armonia es la clase que estas tocando, en el tono en que la tocaste, y la secuencia se queda quieta; al soltar vuelve exactamente donde estaba. Latch: la agarra y se queda con ella, y la secuencia sigue desde ahi. Cualquier acorde sirve: el catalogo tiene las 351 clases Tn, que por doce transposiciones son los 4095 conjuntos posibles, asi que identificar es una busqueda que no puede fallar.",
                    "id": "obj-284",
                    "maxclass": "live.tab",
                    "num_lines_patching": 1,
                    "num_lines_presentation": 1,
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 20.0, 5160.0, 160.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 6.0, 781.0, 100.0, 18.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "Off", "Sigue", "Latch" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Escuchar",
                            "parameter_mmax": 2,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Escuchar",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
                        }
                    },
                    "varname": "fs2_escuchar"
                }
            },
            {
                "box": {
                    "id": "obj-285",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 5220.0, 150.0, 20.0 ],
                    "text": "prepend setlisten"
                }
            },
            {
                "box": {
                    "id": "obj-286",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 196.0, 5140.0, 50.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 116.0, 767.0, 40.0, 18.0 ],
                    "text": "Emitir"
                }
            },
            {
                "box": {
                    "annotation": "Difunde por que clase va este device, en su bus. Solo viaja CUAL set: la raiz, la octava, el voicing y el registro quedan de cada uno, porque dos motores en registros o tonos distintos sobre una misma armonia es justamente para lo que sirven dos.",
                    "id": "obj-287",
                    "maxclass": "live.toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 196.0, 5160.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 116.0, 781.0, 15.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Emitir",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Emitir",
                            "parameter_type": 2
                        }
                    },
                    "varname": "fs2_emitir"
                }
            },
            {
                "box": {
                    "id": "obj-288",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 372.0, 5220.0, 150.0, 20.0 ],
                    "text": "prepend setbroadcast"
                }
            },
            {
                "box": {
                    "id": "obj-289",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 252.0, 5140.0, 50.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 162.0, 767.0, 40.0, 18.0 ],
                    "text": "Seguir"
                }
            },
            {
                "box": {
                    "annotation": "Toma la armonia del bus en vez de elegirla. Con esto encendido el reloj de este device ya no mueve el catalogo: manda el que difunde. Un motor que sigue nunca difunde, asi que no hay lazo posible.",
                    "id": "obj-290",
                    "maxclass": "live.toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 252.0, 5160.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 162.0, 781.0, 15.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Seguir",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Seguir",
                            "parameter_type": 2
                        }
                    },
                    "varname": "fs2_seguir"
                }
            },
            {
                "box": {
                    "id": "obj-291",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 484.0, 5220.0, 150.0, 20.0 ],
                    "text": "prepend setfollow"
                }
            },
            {
                "box": {
                    "annotation": "Suelta la mano a la fuerza. Los note-off no siempre llegan -- cambiaste de modo con el acorde apretado, o rearmaste la pista -- y sin esto el device se queda creyendo que seguis tocando.",
                    "id": "obj-292",
                    "maxclass": "live.text",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 320.0, 5160.0, 56.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 199.0, 780.0, 56.0, 18.0 ],
                    "text": "Panic",
                    "varname": "fs2_lpanic"
                }
            },
            {
                "box": {
                    "id": "obj-293",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "bang", "" ],
                    "patching_rect": [ 320.0, 5190.0, 50.0, 20.0 ],
                    "text": "sel 1"
                }
            },
            {
                "box": {
                    "id": "obj-294",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 320.0, 5220.0, 90.0, 20.0 ],
                    "text": "listenpanic"
                }
            },
            {
                "box": {
                    "id": "obj-295",
                    "linecount": 3,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 5270.0, 512.0, 41.0 ],
                    "text": "Escuchar manda sobre todo lo de la pagina Camino: una mano en el teclado ES la armonia. Seguir tambien. Emitir y Seguir usan el mismo Bus que las notas, asi que dos motores en el bus 1 comparten armonia y dos en buses distintos se ignoran.",
                    "varname": "es_nota"
                }
            },
            {
                "box": {
                    "id": "obj-296",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 5800.0, 70.0, 20.0 ],
                    "text": "outputvalue",
                    "varname": "md_init"
                }
            },
            {
                "box": {
                    "id": "obj-297",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 44.0, 5840.0, 72.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 22.0, 601.0, 54.0, 18.0 ],
                    "text": "Forma"
                }
            },
            {
                "box": {
                    "id": "obj-298",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 120.0, 5840.0, 42.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 82.0, 601.0, 32.0, 18.0 ],
                    "text": "Ciclo"
                }
            },
            {
                "box": {
                    "id": "obj-299",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 166.0, 5840.0, 46.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 118.0, 601.0, 32.0, 18.0 ],
                    "text": "Prof"
                }
            },
            {
                "box": {
                    "id": "obj-300",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 216.0, 5840.0, 42.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 154.0, 601.0, 32.0, 18.0 ],
                    "text": "Fase"
                }
            },
            {
                "box": {
                    "id": "obj-301",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 262.0, 5840.0, 80.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 190.0, 601.0, 62.0, 18.0 ],
                    "text": "Dest"
                }
            },
            {
                "box": {
                    "id": "obj-302",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 5880.0, 24.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 0.0, 620.0, 22.0, 18.0 ],
                    "text": "M1"
                }
            },
            {
                "box": {
                    "annotation": "La curva que recorre el modulador. Seno y Triang barren; Diente vuelve de golpe al empezar cada ciclo; Cuadr salta entre los dos extremos y no pasa por el medio; Azar saca un valor nuevo por ciclo y lo sostiene; Paseo se mueve un poco desde donde ya estaba, asi que se aleja de a poco en vez de saltar, y rebota en los bordes en lugar de quedarse pegado a ellos.",
                    "id": "obj-303",
                    "maxclass": "live.menu",
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 44.0, 5880.0, 72.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 22.0, 619.0, 54.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "Seno", "Triang", "Diente", "Cuadr", "Azar", "Paseo" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M1 Forma",
                            "parameter_mmax": 5,
                            "parameter_modmode": 0,
                            "parameter_shortname": "M1 Forma",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
                        }
                    },
                    "varname": "md_m1_forma"
                }
            },
            {
                "box": {
                    "id": "obj-304",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 6050.0, 190.0, 20.0 ],
                    "text": "prepend setmodshape 1"
                }
            },
            {
                "box": {
                    "annotation": "Cuantos PASOS dura un ciclo, no cuantos milisegundos. Ocho pasos son ocho pasos a cualquier tempo y siempre caen en la reja, mientras que un LFO en hertz se corre contra ella. Para Azar y Paseo es cuanto sostiene cada valor. Ciclos que no se dividen entre si -- 8 contra 5 -- tardan 40 pasos en volver a coincidir, que es como se consigue que la modulacion no se oiga como un bucle.",
                    "id": "obj-305",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 120.0, 5880.0, 42.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 82.0, 621.0, 32.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 8 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M1 Ciclo",
                            "parameter_mmax": 64.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "M1 Ciclo",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "md_m1_ciclo"
                }
            },
            {
                "box": {
                    "id": "obj-306",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 220.0, 6050.0, 190.0, 20.0 ],
                    "text": "prepend setmodcycle 1"
                }
            },
            {
                "box": {
                    "annotation": "Cuanto abre el barrido, y hacia donde. Todas las formas son bipolares, asi que el dial del destino queda en el CENTRO del barrido: en 0 el destino vale exactamente lo que dice su dial, y subir la profundidad lo abre parejo hacia los dos lados. Una profundidad negativa da vuelta la forma, que es como se enfrentan dos moduladores puestos en el mismo destino.",
                    "id": "obj-307",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 166.0, 5880.0, 46.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 118.0, 621.0, 32.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M1 Prof",
                            "parameter_mmax": 100.0,
                            "parameter_mmin": -100.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "M1 Prof",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "md_m1_prof"
                }
            },
            {
                "box": {
                    "id": "obj-308",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 420.0, 6050.0, 190.0, 20.0 ],
                    "text": "prepend setmoddepth 1"
                }
            },
            {
                "box": {
                    "annotation": "Desde que punto del ciclo arranca, en porcentaje. Es lo unico que separa a dos moduladores con la misma forma y el mismo ciclo: en 25 quedan en cuadratura, en 50 opuestos. Para Azar y Paseo corre tambien el momento en que sacan el valor nuevo, asi que dos de ellos dejan de saltar juntos.",
                    "id": "obj-309",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 216.0, 5880.0, 42.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 154.0, 621.0, 32.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M1 Fase",
                            "parameter_mmax": 100.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "M1 Fase",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "md_m1_fase"
                }
            },
            {
                "box": {
                    "id": "obj-310",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 620.0, 6050.0, 190.0, 20.0 ],
                    "text": "prepend setmodphase 1"
                }
            },
            {
                "box": {
                    "annotation": "Que mueve este modulador. Ninguno escribe el parametro: el dial sigue diciendo lo que vos pusiste y el modulador suma encima al momento de leerlo, asi que apagarlo devuelve el numero exacto que estas viendo. Silencio y Ratchet arrancan en la punta de su rango, asi que conviene bajar el dial a mitad de camino antes de modularlos o la mitad del barrido se pierde contra el tope. Grado corre el grado que se lee del set: se escucha en Arpegio y con Indep, no en Acordes. Swing, Rasgueo y Ratchet necesitan Sub 2 o mas para tener donde caer.",
                    "id": "obj-311",
                    "maxclass": "live.menu",
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 262.0, 5880.0, 80.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 190.0, 619.0, 42.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "-", "Raiz", "Octava", "Vel", "Largo", "Silencio", "Swing", "Rasgueo", "Ratchet", "Grado", "Human", "Caida" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M1 Dest",
                            "parameter_mmax": 11,
                            "parameter_modmode": 0,
                            "parameter_shortname": "M1 Dest",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
                        }
                    },
                    "varname": "md_m1_dest"
                }
            },
            {
                "box": {
                    "id": "obj-312",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 820.0, 6050.0, 190.0, 20.0 ],
                    "text": "prepend setmoddest 1"
                }
            },
            {
                "box": {
                    "id": "obj-313",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 5906.0, 24.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 0.0, 643.0, 22.0, 18.0 ],
                    "text": "M2"
                }
            },
            {
                "box": {
                    "annotation": "La curva que recorre el modulador. Seno y Triang barren; Diente vuelve de golpe al empezar cada ciclo; Cuadr salta entre los dos extremos y no pasa por el medio; Azar saca un valor nuevo por ciclo y lo sostiene; Paseo se mueve un poco desde donde ya estaba, asi que se aleja de a poco en vez de saltar, y rebota en los bordes en lugar de quedarse pegado a ellos.",
                    "id": "obj-314",
                    "maxclass": "live.menu",
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 44.0, 5906.0, 72.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 22.0, 642.0, 54.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "Seno", "Triang", "Diente", "Cuadr", "Azar", "Paseo" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M2 Forma",
                            "parameter_mmax": 5,
                            "parameter_modmode": 0,
                            "parameter_shortname": "M2 Forma",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
                        }
                    },
                    "varname": "md_m2_forma"
                }
            },
            {
                "box": {
                    "id": "obj-315",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 6080.0, 190.0, 20.0 ],
                    "text": "prepend setmodshape 2"
                }
            },
            {
                "box": {
                    "annotation": "Cuantos PASOS dura un ciclo, no cuantos milisegundos. Ocho pasos son ocho pasos a cualquier tempo y siempre caen en la reja, mientras que un LFO en hertz se corre contra ella. Para Azar y Paseo es cuanto sostiene cada valor. Ciclos que no se dividen entre si -- 8 contra 5 -- tardan 40 pasos en volver a coincidir, que es como se consigue que la modulacion no se oiga como un bucle.",
                    "id": "obj-316",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 120.0, 5906.0, 42.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 82.0, 644.0, 32.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 8 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M2 Ciclo",
                            "parameter_mmax": 64.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "M2 Ciclo",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "md_m2_ciclo"
                }
            },
            {
                "box": {
                    "id": "obj-317",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 220.0, 6080.0, 190.0, 20.0 ],
                    "text": "prepend setmodcycle 2"
                }
            },
            {
                "box": {
                    "annotation": "Cuanto abre el barrido, y hacia donde. Todas las formas son bipolares, asi que el dial del destino queda en el CENTRO del barrido: en 0 el destino vale exactamente lo que dice su dial, y subir la profundidad lo abre parejo hacia los dos lados. Una profundidad negativa da vuelta la forma, que es como se enfrentan dos moduladores puestos en el mismo destino.",
                    "id": "obj-318",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 166.0, 5906.0, 46.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 118.0, 644.0, 32.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M2 Prof",
                            "parameter_mmax": 100.0,
                            "parameter_mmin": -100.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "M2 Prof",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "md_m2_prof"
                }
            },
            {
                "box": {
                    "id": "obj-319",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 420.0, 6080.0, 190.0, 20.0 ],
                    "text": "prepend setmoddepth 2"
                }
            },
            {
                "box": {
                    "annotation": "Desde que punto del ciclo arranca, en porcentaje. Es lo unico que separa a dos moduladores con la misma forma y el mismo ciclo: en 25 quedan en cuadratura, en 50 opuestos. Para Azar y Paseo corre tambien el momento en que sacan el valor nuevo, asi que dos de ellos dejan de saltar juntos.",
                    "id": "obj-320",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 216.0, 5906.0, 42.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 154.0, 644.0, 32.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M2 Fase",
                            "parameter_mmax": 100.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "M2 Fase",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "md_m2_fase"
                }
            },
            {
                "box": {
                    "id": "obj-321",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 620.0, 6080.0, 190.0, 20.0 ],
                    "text": "prepend setmodphase 2"
                }
            },
            {
                "box": {
                    "annotation": "Que mueve este modulador. Ninguno escribe el parametro: el dial sigue diciendo lo que vos pusiste y el modulador suma encima al momento de leerlo, asi que apagarlo devuelve el numero exacto que estas viendo. Silencio y Ratchet arrancan en la punta de su rango, asi que conviene bajar el dial a mitad de camino antes de modularlos o la mitad del barrido se pierde contra el tope. Grado corre el grado que se lee del set: se escucha en Arpegio y con Indep, no en Acordes. Swing, Rasgueo y Ratchet necesitan Sub 2 o mas para tener donde caer.",
                    "id": "obj-322",
                    "maxclass": "live.menu",
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 262.0, 5906.0, 80.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 190.0, 642.0, 42.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "-", "Raiz", "Octava", "Vel", "Largo", "Silencio", "Swing", "Rasgueo", "Ratchet", "Grado", "Human", "Caida" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M2 Dest",
                            "parameter_mmax": 11,
                            "parameter_modmode": 0,
                            "parameter_shortname": "M2 Dest",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
                        }
                    },
                    "varname": "md_m2_dest"
                }
            },
            {
                "box": {
                    "id": "obj-323",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 820.0, 6080.0, 190.0, 20.0 ],
                    "text": "prepend setmoddest 2"
                }
            },
            {
                "box": {
                    "id": "obj-324",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 5932.0, 24.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 0.0, 666.0, 22.0, 18.0 ],
                    "text": "M3"
                }
            },
            {
                "box": {
                    "annotation": "La curva que recorre el modulador. Seno y Triang barren; Diente vuelve de golpe al empezar cada ciclo; Cuadr salta entre los dos extremos y no pasa por el medio; Azar saca un valor nuevo por ciclo y lo sostiene; Paseo se mueve un poco desde donde ya estaba, asi que se aleja de a poco en vez de saltar, y rebota en los bordes en lugar de quedarse pegado a ellos.",
                    "id": "obj-325",
                    "maxclass": "live.menu",
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 44.0, 5932.0, 72.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 22.0, 665.0, 54.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "Seno", "Triang", "Diente", "Cuadr", "Azar", "Paseo" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M3 Forma",
                            "parameter_mmax": 5,
                            "parameter_modmode": 0,
                            "parameter_shortname": "M3 Forma",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
                        }
                    },
                    "varname": "md_m3_forma"
                }
            },
            {
                "box": {
                    "id": "obj-326",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 6110.0, 190.0, 20.0 ],
                    "text": "prepend setmodshape 3"
                }
            },
            {
                "box": {
                    "annotation": "Cuantos PASOS dura un ciclo, no cuantos milisegundos. Ocho pasos son ocho pasos a cualquier tempo y siempre caen en la reja, mientras que un LFO en hertz se corre contra ella. Para Azar y Paseo es cuanto sostiene cada valor. Ciclos que no se dividen entre si -- 8 contra 5 -- tardan 40 pasos en volver a coincidir, que es como se consigue que la modulacion no se oiga como un bucle.",
                    "id": "obj-327",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 120.0, 5932.0, 42.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 82.0, 667.0, 32.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 8 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M3 Ciclo",
                            "parameter_mmax": 64.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "M3 Ciclo",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "md_m3_ciclo"
                }
            },
            {
                "box": {
                    "id": "obj-328",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 220.0, 6110.0, 190.0, 20.0 ],
                    "text": "prepend setmodcycle 3"
                }
            },
            {
                "box": {
                    "annotation": "Cuanto abre el barrido, y hacia donde. Todas las formas son bipolares, asi que el dial del destino queda en el CENTRO del barrido: en 0 el destino vale exactamente lo que dice su dial, y subir la profundidad lo abre parejo hacia los dos lados. Una profundidad negativa da vuelta la forma, que es como se enfrentan dos moduladores puestos en el mismo destino.",
                    "id": "obj-329",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 166.0, 5932.0, 46.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 118.0, 667.0, 32.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M3 Prof",
                            "parameter_mmax": 100.0,
                            "parameter_mmin": -100.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "M3 Prof",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "md_m3_prof"
                }
            },
            {
                "box": {
                    "id": "obj-330",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 420.0, 6110.0, 190.0, 20.0 ],
                    "text": "prepend setmoddepth 3"
                }
            },
            {
                "box": {
                    "annotation": "Desde que punto del ciclo arranca, en porcentaje. Es lo unico que separa a dos moduladores con la misma forma y el mismo ciclo: en 25 quedan en cuadratura, en 50 opuestos. Para Azar y Paseo corre tambien el momento en que sacan el valor nuevo, asi que dos de ellos dejan de saltar juntos.",
                    "id": "obj-331",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 216.0, 5932.0, 42.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 154.0, 667.0, 32.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M3 Fase",
                            "parameter_mmax": 100.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "M3 Fase",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "md_m3_fase"
                }
            },
            {
                "box": {
                    "id": "obj-332",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 620.0, 6110.0, 190.0, 20.0 ],
                    "text": "prepend setmodphase 3"
                }
            },
            {
                "box": {
                    "annotation": "Que mueve este modulador. Ninguno escribe el parametro: el dial sigue diciendo lo que vos pusiste y el modulador suma encima al momento de leerlo, asi que apagarlo devuelve el numero exacto que estas viendo. Silencio y Ratchet arrancan en la punta de su rango, asi que conviene bajar el dial a mitad de camino antes de modularlos o la mitad del barrido se pierde contra el tope. Grado corre el grado que se lee del set: se escucha en Arpegio y con Indep, no en Acordes. Swing, Rasgueo y Ratchet necesitan Sub 2 o mas para tener donde caer.",
                    "id": "obj-333",
                    "maxclass": "live.menu",
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 262.0, 5932.0, 80.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 190.0, 665.0, 42.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "-", "Raiz", "Octava", "Vel", "Largo", "Silencio", "Swing", "Rasgueo", "Ratchet", "Grado", "Human", "Caida" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M3 Dest",
                            "parameter_mmax": 11,
                            "parameter_modmode": 0,
                            "parameter_shortname": "M3 Dest",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
                        }
                    },
                    "varname": "md_m3_dest"
                }
            },
            {
                "box": {
                    "id": "obj-334",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 820.0, 6110.0, 190.0, 20.0 ],
                    "text": "prepend setmoddest 3"
                }
            },
            {
                "box": {
                    "id": "obj-335",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 5958.0, 24.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 0.0, 689.0, 22.0, 18.0 ],
                    "text": "M4"
                }
            },
            {
                "box": {
                    "annotation": "La curva que recorre el modulador. Seno y Triang barren; Diente vuelve de golpe al empezar cada ciclo; Cuadr salta entre los dos extremos y no pasa por el medio; Azar saca un valor nuevo por ciclo y lo sostiene; Paseo se mueve un poco desde donde ya estaba, asi que se aleja de a poco en vez de saltar, y rebota en los bordes en lugar de quedarse pegado a ellos.",
                    "id": "obj-336",
                    "maxclass": "live.menu",
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 44.0, 5958.0, 72.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 22.0, 688.0, 54.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "Seno", "Triang", "Diente", "Cuadr", "Azar", "Paseo" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M4 Forma",
                            "parameter_mmax": 5,
                            "parameter_modmode": 0,
                            "parameter_shortname": "M4 Forma",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
                        }
                    },
                    "varname": "md_m4_forma"
                }
            },
            {
                "box": {
                    "id": "obj-337",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 6140.0, 190.0, 20.0 ],
                    "text": "prepend setmodshape 4"
                }
            },
            {
                "box": {
                    "annotation": "Cuantos PASOS dura un ciclo, no cuantos milisegundos. Ocho pasos son ocho pasos a cualquier tempo y siempre caen en la reja, mientras que un LFO en hertz se corre contra ella. Para Azar y Paseo es cuanto sostiene cada valor. Ciclos que no se dividen entre si -- 8 contra 5 -- tardan 40 pasos en volver a coincidir, que es como se consigue que la modulacion no se oiga como un bucle.",
                    "id": "obj-338",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 120.0, 5958.0, 42.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 82.0, 690.0, 32.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 8 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M4 Ciclo",
                            "parameter_mmax": 64.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "M4 Ciclo",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "md_m4_ciclo"
                }
            },
            {
                "box": {
                    "id": "obj-339",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 220.0, 6140.0, 190.0, 20.0 ],
                    "text": "prepend setmodcycle 4"
                }
            },
            {
                "box": {
                    "annotation": "Cuanto abre el barrido, y hacia donde. Todas las formas son bipolares, asi que el dial del destino queda en el CENTRO del barrido: en 0 el destino vale exactamente lo que dice su dial, y subir la profundidad lo abre parejo hacia los dos lados. Una profundidad negativa da vuelta la forma, que es como se enfrentan dos moduladores puestos en el mismo destino.",
                    "id": "obj-340",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 166.0, 5958.0, 46.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 118.0, 690.0, 32.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M4 Prof",
                            "parameter_mmax": 100.0,
                            "parameter_mmin": -100.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "M4 Prof",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "md_m4_prof"
                }
            },
            {
                "box": {
                    "id": "obj-341",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 420.0, 6140.0, 190.0, 20.0 ],
                    "text": "prepend setmoddepth 4"
                }
            },
            {
                "box": {
                    "annotation": "Desde que punto del ciclo arranca, en porcentaje. Es lo unico que separa a dos moduladores con la misma forma y el mismo ciclo: en 25 quedan en cuadratura, en 50 opuestos. Para Azar y Paseo corre tambien el momento en que sacan el valor nuevo, asi que dos de ellos dejan de saltar juntos.",
                    "id": "obj-342",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 216.0, 5958.0, 42.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 154.0, 690.0, 32.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M4 Fase",
                            "parameter_mmax": 100.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "M4 Fase",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "md_m4_fase"
                }
            },
            {
                "box": {
                    "id": "obj-343",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 620.0, 6140.0, 190.0, 20.0 ],
                    "text": "prepend setmodphase 4"
                }
            },
            {
                "box": {
                    "annotation": "Que mueve este modulador. Ninguno escribe el parametro: el dial sigue diciendo lo que vos pusiste y el modulador suma encima al momento de leerlo, asi que apagarlo devuelve el numero exacto que estas viendo. Silencio y Ratchet arrancan en la punta de su rango, asi que conviene bajar el dial a mitad de camino antes de modularlos o la mitad del barrido se pierde contra el tope. Grado corre el grado que se lee del set: se escucha en Arpegio y con Indep, no en Acordes. Swing, Rasgueo y Ratchet necesitan Sub 2 o mas para tener donde caer.",
                    "id": "obj-344",
                    "maxclass": "live.menu",
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 262.0, 5958.0, 80.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 190.0, 688.0, 42.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "-", "Raiz", "Octava", "Vel", "Largo", "Silencio", "Swing", "Rasgueo", "Ratchet", "Grado", "Human", "Caida" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "M4 Dest",
                            "parameter_mmax": 11,
                            "parameter_modmode": 0,
                            "parameter_shortname": "M4 Dest",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
                        }
                    },
                    "varname": "md_m4_dest"
                }
            },
            {
                "box": {
                    "id": "obj-345",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 820.0, 6140.0, 190.0, 20.0 ],
                    "text": "prepend setmoddest 4"
                }
            },
            {
                "box": {
                    "id": "obj-346",
                    "linecount": 8,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 900.0, 5840.0, 188.0, 98.0 ],
                    "text": "Cuatro moduladores, uno por fila. Dos apuntados al mismo destino se suman. Ninguno escribe el parametro: el dial sigue diciendo lo tuyo y esto suma encima al leer, asi que Prof en 0 devuelve el numero exacto. Avanzan por paso, no por reloj: con la secuencia detenida no se mueven.",
                    "varname": "md_nota"
                }
            },
            {
                "box": {
                    "id": "obj-347",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 6500.0, 70.0, 20.0 ],
                    "text": "outputvalue",
                    "varname": "pr_init"
                }
            },
            {
                "box": {
                    "id": "obj-348",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 6540.0, 44.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 6.0, 799.0, 44.0, 18.0 ],
                    "text": "Slot"
                }
            },
            {
                "box": {
                    "annotation": "En cual de los veinte slots trabajan Guardar, Cargar y Borrar. El slot mismo no entra en ningun preset: si entrara, cargar uno te moveria el slot y el click siguiente iria a parar a otro lado.",
                    "id": "obj-349",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 20.0, 6570.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 6.0, 813.0, 44.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 1 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Slot",
                            "parameter_mmax": 20.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Slot",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "pr_slot"
                }
            },
            {
                "box": {
                    "id": "obj-350",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 20.0, 6610.0, 150.0, 20.0 ],
                    "text": "prepend setpresetslot"
                }
            },
            {
                "box": {
                    "annotation": "Lee el valor de todos los parametros del device y los escribe en el slot y en el archivo, en el acto. Quedan afuera Run, Bus, Trig, Pagina y Slot. Run es el transporte, y un preset que arranca o para la secuencia es un preset que no podes escuchar; Bus es una direccion y no un sonido; los otros son donde estas mirando y el boton que estas por apretar.",
                    "id": "obj-351",
                    "maxclass": "live.text",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 200.0, 6570.0, 64.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 60.0, 813.0, 64.0, 18.0 ],
                    "text": "Guardar",
                    "varname": "pr_save"
                }
            },
            {
                "box": {
                    "id": "obj-352",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "bang", "" ],
                    "patching_rect": [ 200.0, 6610.0, 50.0, 20.0 ],
                    "text": "sel 1"
                }
            },
            {
                "box": {
                    "id": "obj-353",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 200.0, 6645.0, 110.0, 20.0 ],
                    "text": "storepreset"
                }
            },
            {
                "box": {
                    "annotation": "Pone esos valores de vuelta y despues le pide a los controles que hablen. Esa segunda mitad es todo el truco: escribir un parametro por la API de Live cambia lo que el control MUESTRA pero no dispara su salida, asi que el motor no se enteraria de nada. Es el mismo camino que corre solo cuando abris el set. Un slot guardado por una version anterior carga igual: los nombres que este device ya no tiene se saltean, y el resto entra.",
                    "id": "obj-354",
                    "maxclass": "live.text",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 400.0, 6570.0, 64.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 130.0, 813.0, 64.0, 18.0 ],
                    "text": "Cargar",
                    "varname": "pr_load"
                }
            },
            {
                "box": {
                    "id": "obj-355",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "bang", "" ],
                    "patching_rect": [ 400.0, 6610.0, 50.0, 20.0 ],
                    "text": "sel 1"
                }
            },
            {
                "box": {
                    "id": "obj-356",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 400.0, 6645.0, 110.0, 20.0 ],
                    "text": "recallpreset"
                }
            },
            {
                "box": {
                    "annotation": "Vacia el slot y reescribe el archivo.",
                    "id": "obj-357",
                    "maxclass": "live.text",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 600.0, 6570.0, 64.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 200.0, 813.0, 64.0, 18.0 ],
                    "text": "Borrar",
                    "varname": "pr_clear"
                }
            },
            {
                "box": {
                    "id": "obj-358",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "bang", "" ],
                    "patching_rect": [ 600.0, 6610.0, 50.0, 20.0 ],
                    "text": "sel 1"
                }
            },
            {
                "box": {
                    "id": "obj-359",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 600.0, 6645.0, 110.0, 20.0 ],
                    "text": "clearpreset"
                }
            },
            {
                "box": {
                    "id": "obj-360",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 6690.0, 54.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 6.0, 833.0, 54.0, 18.0 ],
                    "text": "Llenos"
                }
            },
            {
                "box": {
                    "annotation": "Que slots tienen algo. Un guion es un slot vacio.",
                    "fontsize": 7.0,
                    "id": "obj-361",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 120.0, 6730.0, 202.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 62.0, 833.0, 202.0, 15.0 ],
                    "text": "- - - - - - - -",
                    "varname": "pr_list"
                }
            },
            {
                "box": {
                    "id": "obj-362",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "", "" ],
                    "patching_rect": [ 120.0, 6690.0, 130.0, 20.0 ],
                    "text": "route presetslots",
                    "varname": "pr_echo"
                }
            },
            {
                "box": {
                    "id": "obj-363",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 120.0, 6710.0, 90.0, 20.0 ],
                    "text": "prepend set"
                }
            },
            {
                "box": {
                    "id": "obj-364",
                    "linecount": 6,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 700.0, 6540.0, 258.0, 75.0 ],
                    "text": "Los veinte slots viven en forteseq2_presets.txt, al lado del .amxd, y no adentro del set de Live. Eso los hace tuyos y no de la cancion: los mismos veinte te siguen a cualquier set, igual que los favoritos, y varias instancias del device comparten el archivo. Se escribe en cada Guardar y en cada Borrar, y se lee al cargar el device.",
                    "varname": "pr_nota"
                }
            },
            {
                "box": {
                    "comment": "salida 5 del js (monitor por voz)",
                    "id": "obj-365",
                    "index": 0,
                    "maxclass": "inlet",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 300.0, 20.0, 30.0, 30.0 ]
                }
            },
            {
                "box": {
                    "annotation": "Que porcentaje de las 12 celdas de Mascara enciende Azar Mascara -- minimo 1 celda, para no vaciar el filtro de mascara sin querer.",
                    "id": "obj-372",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 380.0, 4500.0, 40.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 171.0, 184.0, 40.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 50 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Azar % Mask",
                            "parameter_mmax": 100.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Azar % Mask",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_randmaskpct"
                }
            },
            {
                "box": {
                    "id": "obj-373",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 380.0, 4540.0, 150.0, 20.0 ],
                    "text": "prepend setrandmaskpct"
                }
            },
            {
                "box": {
                    "id": "obj-374",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 380.0, 4580.0, 79.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 95.0, 184.0, 79.0, 20.0 ],
                    "text": "randomizemask"
                }
            },
            {
                "box": {
                    "annotation": "Que porcentaje de las celdas dentro del Ciclo Acentos actual enciende Azar Acentos -- las celdas fuera del ciclo se apagan.",
                    "id": "obj-375",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 380.0, 4660.0, 40.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 196.0, 375.0, 40.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 50 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Azar % Acentos",
                            "parameter_mmax": 100.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Azar % Acentos",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2_randaccentpct"
                }
            },
            {
                "box": {
                    "id": "obj-376",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 380.0, 4700.0, 150.0, 20.0 ],
                    "text": "prepend setrandaccentpct"
                }
            },
            {
                "box": {
                    "id": "obj-378",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 20.0, 6900.0, 54.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 6.0, 851.0, 54.0, 18.0 ],
                    "text": "Nombre",
                    "varname": "pr_name_lbl"
                }
            },
            {
                "box": {
                    "annotation": "El nombre del slot que Slot esta apuntando ahora mismo, si tiene uno. Los presets de fabrica (Azar Presets, mas abajo) ya vienen con nombre; guardar uno propio no pone nombre salvo que el slot ya tuviera uno de antes, que se conserva.",
                    "id": "obj-379",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 120.0, 6930.0, 200.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 62.0, 851.0, 200.0, 18.0 ],
                    "text": "-",
                    "varname": "pr_name"
                }
            },
            {
                "box": {
                    "id": "obj-380",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "", "" ],
                    "patching_rect": [ 120.0, 6960.0, 120.0, 20.0 ],
                    "text": "route presetname",
                    "varname": "pr_name_echo"
                }
            },
            {
                "box": {
                    "id": "obj-381",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 120.0, 6990.0, 90.0, 20.0 ],
                    "text": "prepend set"
                }
            },
            {
                "box": {
                    "id": "obj-385",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 116.0, 1400.0, 40.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 6.0, 19.0, 20.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Enlace Tonos",
                            "parameter_mmax": 6.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Enl Ton",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2p_enlace"
                }
            },
            {
                "box": {
                    "id": "obj-386",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 116.0, 1424.0, 150.0, 20.0 ],
                    "text": "prepend setlink"
                }
            },
            {
                "box": {
                    "id": "obj-393",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 116.0, 1380.0, 40.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 6.0, 0.0, 23.0, 18.0 ],
                    "text": "Enl"
                }
            },
            {
                "box": {
                    "id": "obj-387",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 140.0, 1400.0, 40.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 30.0, 19.0, 20.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Tension",
                            "parameter_mmax": 16.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Tension",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2p_tension"
                }
            },
            {
                "box": {
                    "id": "obj-388",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 140.0, 1424.0, 150.0, 20.0 ],
                    "text": "prepend settension"
                }
            },
            {
                "box": {
                    "id": "obj-394",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 140.0, 1380.0, 40.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 30.0, 0.0, 25.0, 18.0 ],
                    "text": "Tns"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-389",
                    "maxclass": "live.menu",
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 164.0, 1400.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 54.0, 19.0, 44.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "Sube", "Baja", "Arco" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Curva Tension",
                            "parameter_mmax": 2,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Curva Tn",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
                        }
                    },
                    "varname": "fs2p_curva"
                }
            },
            {
                "box": {
                    "id": "obj-390",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 164.0, 1424.0, 150.0, 20.0 ],
                    "text": "prepend settenshape"
                }
            },
            {
                "box": {
                    "id": "obj-395",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 164.0, 1380.0, 40.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 54.0, 0.0, 24.0, 18.0 ],
                    "text": "Crv"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-391",
                    "maxclass": "live.menu",
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 212.0, 1400.0, 44.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 102.0, 19.0, 42.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "Huron", "McKay" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Modelo Tension",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "TensMod",
                            "parameter_type": 2,
                            "parameter_unitstyle": 9
                        }
                    },
                    "varname": "fs2p_tensmodel"
                }
            },
            {
                "box": {
                    "id": "obj-392",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 212.0, 1424.0, 150.0, 20.0 ],
                    "text": "prepend settensmodel"
                }
            },
            {
                "box": {
                    "id": "obj-396",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 212.0, 1380.0, 40.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 102.0, 0.0, 28.0, 18.0 ],
                    "text": "Mod"
                }
            },
            {
                "box": {
                    "annotation": "De cuantos grados es el salto en la lectura Coprimo. El motor lo corrige al valor coprimo mas cercano al pedido, que es lo unico que garantiza pasar por todos los grados antes de repetir. En un set de 7 notas, 2 es una cadena de terceras.",
                    "id": "obj-400",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 290.0, 1400.0, 38.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 165.0, 59.0, 38.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 2 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Salto Coprimo",
                            "parameter_mmax": 11.0,
                            "parameter_mmin": 1.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "SaltoCop",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2p_salto"
                }
            },
            {
                "box": {
                    "id": "obj-401",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 290.0, 1428.0, 150.0, 20.0 ],
                    "text": "prepend setcoprime"
                }
            },
            {
                "box": {
                    "id": "obj-402",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 290.0, 1380.0, 60.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 171.0, 41.0, 40.0, 18.0 ],
                    "text": "Salto"
                }
            },
            {
                "box": {
                    "annotation": "Gira el set actual: que nota lo empieza. En Acordes elige la inversion (C-E-G, E-G-C, G-C-E, ...); en Arpegio se suma a la rotacion automatica de \"Rotar x Cambio\" en vez de pelearla. Envuelve por la cardinalidad del set que suena -- en una triada, 3 vale lo mismo que 0. En Acordes, Conduccion sigue ganando cuando esta prendida, igual que ya gana sobre \"Rotar x Cambio\".",
                    "id": "obj-403",
                    "maxclass": "live.numbox",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "float" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 274.0, 1400.0, 38.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 86.0, 100.0, 38.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Rotacion",
                            "parameter_mmax": 11.0,
                            "parameter_modmode": 4,
                            "parameter_shortname": "Rotacion",
                            "parameter_type": 1,
                            "parameter_unitstyle": 0
                        }
                    },
                    "varname": "fs2p_rotacion"
                }
            },
            {
                "box": {
                    "id": "obj-404",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 274.0, 1428.0, 150.0, 20.0 ],
                    "text": "prepend setrotation"
                }
            },
            {
                "box": {
                    "id": "obj-405",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 274.0, 1380.0, 60.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 86.0, 82.0, 48.0, 18.0 ],
                    "text": "Rotacion"
                }
            },
            {
                "box": {
                    "annotation": "Cada cuanto rota la forma del set. Apagado: una vez por pasada completa del catalogo. Encendido: en cada cambio de set.",
                    "id": "obj-406",
                    "maxclass": "live.toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 104.0, 1400.0, 15.0, 15.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 9.0, 100.0, 15.0, 15.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_enum": [ "off", "on" ],
                            "parameter_initial": [ 0 ],
                            "parameter_initial_enable": 1,
                            "parameter_longname": "Rotar x Cambio",
                            "parameter_mmax": 1,
                            "parameter_modmode": 0,
                            "parameter_shortname": "Rot",
                            "parameter_type": 2
                        }
                    },
                    "varname": "fs2p_rotarx"
                }
            },
            {
                "box": {
                    "id": "obj-407",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 104.0, 1428.0, 150.0, 20.0 ],
                    "text": "prepend setshape"
                }
            },
            {
                "box": {
                    "id": "obj-408",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 104.0, 1380.0, 60.0, 18.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 9.0, 82.0, 28.0, 18.0 ],
                    "text": "RxC"
                }
            },
            {
                "box": {
                    "fontsize": 8.0,
                    "id": "obj-745",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 900.0, 4740.0, 86.0, 18.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 212.0, 393.0, 49.0, 27.0 ],
                    "text": "randomizeaccents"
                }
            }
        ],
        "lines": [
            {
                "patchline": {
                    "destination": [ "obj-137", 0 ],
                    "order": 6,
                    "source": [ "obj-1", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-198", 0 ],
                    "order": 5,
                    "source": [ "obj-1", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-235", 0 ],
                    "order": 4,
                    "source": [ "obj-1", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-268", 0 ],
                    "order": 3,
                    "source": [ "obj-1", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-282", 0 ],
                    "order": 2,
                    "source": [ "obj-1", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-296", 0 ],
                    "order": 1,
                    "source": [ "obj-1", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-347", 0 ],
                    "order": 0,
                    "source": [ "obj-1", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-52", 0 ],
                    "order": 8,
                    "source": [ "obj-1", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-6", 0 ],
                    "order": 9,
                    "source": [ "obj-1", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-74", 0 ],
                    "order": 7,
                    "source": [ "obj-1", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 9 ],
                    "source": [ "obj-101", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 10 ],
                    "source": [ "obj-102", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-121", 0 ],
                    "source": [ "obj-104", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-135", 0 ],
                    "source": [ "obj-105", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-125", 0 ],
                    "source": [ "obj-108", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 11 ],
                    "source": [ "obj-109", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 12 ],
                    "source": [ "obj-110", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 13 ],
                    "source": [ "obj-111", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-134", 0 ],
                    "source": [ "obj-115", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 14 ],
                    "source": [ "obj-117", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 15 ],
                    "source": [ "obj-118", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-119", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-37", 0 ],
                    "source": [ "obj-12", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-121", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-122", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-124", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-125", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-128", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-129", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-101", 0 ],
                    "source": [ "obj-130", 9 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-102", 0 ],
                    "source": [ "obj-130", 10 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-109", 0 ],
                    "source": [ "obj-130", 11 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-110", 0 ],
                    "source": [ "obj-130", 12 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-111", 0 ],
                    "source": [ "obj-130", 13 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-117", 0 ],
                    "source": [ "obj-130", 14 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-118", 0 ],
                    "source": [ "obj-130", 15 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-76", 0 ],
                    "source": [ "obj-130", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-82", 0 ],
                    "source": [ "obj-130", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-83", 0 ],
                    "source": [ "obj-130", 2 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-84", 0 ],
                    "source": [ "obj-130", 3 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-89", 0 ],
                    "source": [ "obj-130", 4 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-92", 0 ],
                    "source": [ "obj-130", 5 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-93", 0 ],
                    "source": [ "obj-130", 6 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-97", 0 ],
                    "source": [ "obj-130", 7 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-98", 0 ],
                    "source": [ "obj-130", 8 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-136", 0 ],
                    "source": [ "obj-131", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-132", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-133", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-134", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-135", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-136", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-139", 0 ],
                    "order": 15,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-144", 0 ],
                    "order": 16,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-146", 0 ],
                    "order": 14,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-148", 0 ],
                    "order": 13,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-150", 0 ],
                    "order": 12,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-153", 0 ],
                    "order": 10,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-157", 0 ],
                    "order": 11,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-158", 0 ],
                    "order": 8,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-159", 0 ],
                    "order": 9,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-162", 0 ],
                    "order": 6,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-163", 0 ],
                    "order": 7,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-166", 0 ],
                    "order": 4,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-167", 0 ],
                    "order": 5,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-168", 0 ],
                    "order": 2,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-169", 0 ],
                    "order": 3,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-170", 0 ],
                    "order": 1,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-171", 0 ],
                    "order": 0,
                    "source": [ "obj-137", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-139", 0 ],
                    "source": [ "obj-138", 4 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-144", 0 ],
                    "source": [ "obj-138", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-146", 0 ],
                    "source": [ "obj-138", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-148", 0 ],
                    "source": [ "obj-138", 2 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-150", 0 ],
                    "source": [ "obj-138", 5 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-180", 0 ],
                    "source": [ "obj-138", 9 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-189", 0 ],
                    "source": [ "obj-138", 8 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-194", 0 ],
                    "source": [ "obj-139", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-183", 0 ],
                    "source": [ "obj-144", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-175", 0 ],
                    "source": [ "obj-146", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-188", 0 ],
                    "source": [ "obj-148", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-174", 0 ],
                    "source": [ "obj-150", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-181", 0 ],
                    "source": [ "obj-153", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-193", 0 ],
                    "source": [ "obj-157", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-177", 0 ],
                    "source": [ "obj-158", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-190", 0 ],
                    "source": [ "obj-159", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-178", 0 ],
                    "source": [ "obj-162", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-173", 0 ],
                    "source": [ "obj-163", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-196", 0 ],
                    "source": [ "obj-165", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-185", 0 ],
                    "source": [ "obj-166", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-176", 0 ],
                    "source": [ "obj-167", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-182", 0 ],
                    "source": [ "obj-168", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-172", 0 ],
                    "source": [ "obj-169", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-191", 0 ],
                    "source": [ "obj-170", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-184", 0 ],
                    "source": [ "obj-171", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-172", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-173", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-174", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-175", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-176", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-177", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-178", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-153", 0 ],
                    "source": [ "obj-180", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-158", 0 ],
                    "source": [ "obj-180", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-162", 0 ],
                    "source": [ "obj-180", 2 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-166", 0 ],
                    "source": [ "obj-180", 3 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-168", 0 ],
                    "source": [ "obj-180", 4 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-171", 0 ],
                    "source": [ "obj-180", 5 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-181", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-182", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-183", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-184", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-185", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-188", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-157", 0 ],
                    "source": [ "obj-189", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-159", 0 ],
                    "source": [ "obj-189", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-163", 0 ],
                    "source": [ "obj-189", 2 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-167", 0 ],
                    "source": [ "obj-189", 3 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-169", 0 ],
                    "source": [ "obj-189", 4 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-170", 0 ],
                    "source": [ "obj-189", 5 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-50", 0 ],
                    "source": [ "obj-19", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-190", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-191", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-193", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-194", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-196", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-202", 0 ],
                    "order": 4,
                    "source": [ "obj-198", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-206", 0 ],
                    "order": 1,
                    "source": [ "obj-198", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-208", 0 ],
                    "order": 0,
                    "source": [ "obj-198", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-210", 0 ],
                    "order": 6,
                    "source": [ "obj-198", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-212", 0 ],
                    "order": 5,
                    "source": [ "obj-198", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-214", 0 ],
                    "order": 3,
                    "source": [ "obj-198", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-216", 0 ],
                    "order": 2,
                    "source": [ "obj-198", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-138", 0 ],
                    "order": 2,
                    "source": [ "obj-2", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-362", 0 ],
                    "order": 1,
                    "source": [ "obj-2", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-380", 0 ],
                    "order": 0,
                    "source": [ "obj-2", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-75", 0 ],
                    "order": 3,
                    "source": [ "obj-2", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-218", 0 ],
                    "source": [ "obj-202", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-220", 0 ],
                    "source": [ "obj-206", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-221", 0 ],
                    "source": [ "obj-208", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-222", 0 ],
                    "source": [ "obj-210", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-223", 0 ],
                    "source": [ "obj-212", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-224", 0 ],
                    "source": [ "obj-214", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-225", 0 ],
                    "source": [ "obj-216", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-218", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-220", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-221", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-222", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-223", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-224", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-225", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-240", 0 ],
                    "order": 11,
                    "source": [ "obj-235", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-242", 0 ],
                    "order": 7,
                    "source": [ "obj-235", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-244", 0 ],
                    "order": 3,
                    "source": [ "obj-235", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-247", 0 ],
                    "order": 10,
                    "source": [ "obj-235", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-249", 0 ],
                    "order": 6,
                    "source": [ "obj-235", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-251", 0 ],
                    "order": 2,
                    "source": [ "obj-235", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-254", 0 ],
                    "order": 9,
                    "source": [ "obj-235", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-256", 0 ],
                    "order": 5,
                    "source": [ "obj-235", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-258", 0 ],
                    "order": 1,
                    "source": [ "obj-235", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-261", 0 ],
                    "order": 8,
                    "source": [ "obj-235", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-263", 0 ],
                    "order": 4,
                    "source": [ "obj-235", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-265", 0 ],
                    "order": 0,
                    "source": [ "obj-235", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-241", 0 ],
                    "source": [ "obj-240", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-241", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-243", 0 ],
                    "source": [ "obj-242", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-243", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-245", 0 ],
                    "source": [ "obj-244", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-245", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-248", 0 ],
                    "source": [ "obj-247", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-248", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-250", 0 ],
                    "source": [ "obj-249", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-250", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-252", 0 ],
                    "source": [ "obj-251", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-252", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-255", 0 ],
                    "source": [ "obj-254", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-255", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-257", 0 ],
                    "source": [ "obj-256", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-257", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-259", 0 ],
                    "source": [ "obj-258", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-259", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-262", 0 ],
                    "source": [ "obj-261", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-262", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-264", 0 ],
                    "source": [ "obj-263", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-264", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-266", 0 ],
                    "source": [ "obj-265", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-266", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-284", 0 ],
                    "order": 2,
                    "source": [ "obj-282", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-287", 0 ],
                    "order": 1,
                    "source": [ "obj-282", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-290", 0 ],
                    "order": 0,
                    "source": [ "obj-282", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-285", 0 ],
                    "source": [ "obj-284", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-285", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-288", 0 ],
                    "source": [ "obj-287", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-288", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-291", 0 ],
                    "source": [ "obj-290", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-291", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-293", 0 ],
                    "source": [ "obj-292", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-294", 0 ],
                    "source": [ "obj-293", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-294", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-303", 0 ],
                    "order": 19,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-305", 0 ],
                    "order": 15,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-307", 0 ],
                    "order": 11,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-309", 0 ],
                    "order": 7,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-311", 0 ],
                    "order": 3,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-314", 0 ],
                    "order": 18,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-316", 0 ],
                    "order": 14,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-318", 0 ],
                    "order": 10,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-320", 0 ],
                    "order": 6,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-322", 0 ],
                    "order": 2,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-325", 0 ],
                    "order": 17,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-327", 0 ],
                    "order": 13,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-329", 0 ],
                    "order": 9,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-331", 0 ],
                    "order": 5,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-333", 0 ],
                    "order": 1,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-336", 0 ],
                    "order": 16,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-338", 0 ],
                    "order": 12,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-340", 0 ],
                    "order": 8,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-342", 0 ],
                    "order": 4,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-344", 0 ],
                    "order": 0,
                    "source": [ "obj-296", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-304", 0 ],
                    "source": [ "obj-303", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-304", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-306", 0 ],
                    "source": [ "obj-305", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-306", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-308", 0 ],
                    "source": [ "obj-307", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-308", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-310", 0 ],
                    "source": [ "obj-309", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-310", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-312", 0 ],
                    "source": [ "obj-311", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-312", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-315", 0 ],
                    "source": [ "obj-314", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-315", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-317", 0 ],
                    "source": [ "obj-316", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-317", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-319", 0 ],
                    "source": [ "obj-318", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-319", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-41", 0 ],
                    "source": [ "obj-32", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-321", 0 ],
                    "source": [ "obj-320", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-321", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-323", 0 ],
                    "source": [ "obj-322", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-323", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-326", 0 ],
                    "source": [ "obj-325", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-326", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-328", 0 ],
                    "source": [ "obj-327", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-328", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-330", 0 ],
                    "source": [ "obj-329", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-330", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-332", 0 ],
                    "source": [ "obj-331", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-332", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-334", 0 ],
                    "source": [ "obj-333", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-334", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-337", 0 ],
                    "source": [ "obj-336", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-337", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-339", 0 ],
                    "source": [ "obj-338", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-339", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-341", 0 ],
                    "source": [ "obj-340", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-341", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-343", 0 ],
                    "source": [ "obj-342", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-343", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-345", 0 ],
                    "source": [ "obj-344", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-345", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-349", 0 ],
                    "source": [ "obj-347", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-350", 0 ],
                    "source": [ "obj-349", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-350", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-352", 0 ],
                    "source": [ "obj-351", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-353", 0 ],
                    "source": [ "obj-352", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-353", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-355", 0 ],
                    "source": [ "obj-354", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-356", 0 ],
                    "source": [ "obj-355", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-356", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-358", 0 ],
                    "source": [ "obj-357", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-359", 0 ],
                    "source": [ "obj-358", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-359", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-40", 0 ],
                    "source": [ "obj-36", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-363", 0 ],
                    "source": [ "obj-362", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-361", 0 ],
                    "source": [ "obj-363", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-37", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-373", 0 ],
                    "source": [ "obj-372", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-373", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-374", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-376", 0 ],
                    "source": [ "obj-375", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-376", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-381", 0 ],
                    "source": [ "obj-380", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-379", 0 ],
                    "source": [ "obj-381", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-386", 0 ],
                    "source": [ "obj-385", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-386", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-388", 0 ],
                    "source": [ "obj-387", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-388", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-390", 0 ],
                    "source": [ "obj-389", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-390", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-392", 0 ],
                    "source": [ "obj-391", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-392", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-40", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-401", 0 ],
                    "source": [ "obj-400", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-401", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-404", 0 ],
                    "source": [ "obj-403", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-404", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-407", 0 ],
                    "source": [ "obj-406", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-407", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-41", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-50", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-54", 0 ],
                    "order": 14,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-55", 0 ],
                    "order": 13,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-56", 0 ],
                    "order": 12,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-57", 0 ],
                    "order": 11,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-58", 0 ],
                    "order": 10,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-59", 0 ],
                    "order": 9,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-60", 0 ],
                    "order": 8,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-61", 0 ],
                    "order": 7,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-62", 0 ],
                    "order": 6,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-63", 0 ],
                    "order": 5,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-64", 0 ],
                    "order": 4,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-65", 0 ],
                    "order": 3,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-66", 0 ],
                    "order": 2,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-67", 0 ],
                    "order": 1,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-68", 0 ],
                    "order": 0,
                    "source": [ "obj-52", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-70", 0 ],
                    "source": [ "obj-54", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-70", 1 ],
                    "source": [ "obj-55", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-70", 2 ],
                    "source": [ "obj-56", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-70", 3 ],
                    "source": [ "obj-57", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-70", 4 ],
                    "source": [ "obj-58", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-70", 5 ],
                    "source": [ "obj-59", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-12", 0 ],
                    "order": 10,
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-19", 0 ],
                    "order": 9,
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-32", 0 ],
                    "order": 2,
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-36", 0 ],
                    "order": 0,
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-385", 0 ],
                    "order": 7,
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-387", 0 ],
                    "order": 6,
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-389", 0 ],
                    "order": 5,
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-391", 0 ],
                    "order": 4,
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-400", 0 ],
                    "order": 1,
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-403", 0 ],
                    "order": 3,
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-406", 0 ],
                    "order": 8,
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-70", 6 ],
                    "source": [ "obj-60", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-70", 7 ],
                    "source": [ "obj-61", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-70", 8 ],
                    "source": [ "obj-62", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-70", 9 ],
                    "source": [ "obj-63", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-70", 10 ],
                    "source": [ "obj-64", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-70", 11 ],
                    "source": [ "obj-65", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-69", 0 ],
                    "source": [ "obj-66", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-71", 0 ],
                    "source": [ "obj-67", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-73", 0 ],
                    "source": [ "obj-68", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-69", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-72", 0 ],
                    "source": [ "obj-70", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-71", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-72", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-73", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-101", 0 ],
                    "order": 10,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-102", 0 ],
                    "order": 9,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-104", 0 ],
                    "order": 8,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-105", 0 ],
                    "order": 7,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-108", 0 ],
                    "order": 6,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-109", 0 ],
                    "order": 5,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-110", 0 ],
                    "order": 4,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-111", 0 ],
                    "order": 3,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-115", 0 ],
                    "order": 2,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-117", 0 ],
                    "order": 1,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-118", 0 ],
                    "order": 0,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-76", 0 ],
                    "order": 25,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-80", 0 ],
                    "order": 26,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-82", 0 ],
                    "order": 24,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-83", 0 ],
                    "order": 23,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-84", 0 ],
                    "order": 22,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-86", 0 ],
                    "order": 20,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-87", 0 ],
                    "order": 21,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-89", 0 ],
                    "order": 19,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-90", 0 ],
                    "order": 18,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-92", 0 ],
                    "order": 17,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-93", 0 ],
                    "order": 16,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-94", 0 ],
                    "order": 15,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-95", 0 ],
                    "order": 14,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-97", 0 ],
                    "order": 13,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-98", 0 ],
                    "order": 12,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-99", 0 ],
                    "order": 11,
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-5", 0 ],
                    "source": [ "obj-745", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-108", 0 ],
                    "source": [ "obj-75", 4 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-115", 0 ],
                    "source": [ "obj-75", 5 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-130", 0 ],
                    "source": [ "obj-75", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-99", 0 ],
                    "source": [ "obj-75", 3 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 0 ],
                    "source": [ "obj-76", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-133", 0 ],
                    "source": [ "obj-80", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 1 ],
                    "source": [ "obj-82", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 2 ],
                    "source": [ "obj-83", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 3 ],
                    "source": [ "obj-84", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-128", 0 ],
                    "source": [ "obj-86", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-129", 0 ],
                    "source": [ "obj-87", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 4 ],
                    "source": [ "obj-89", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-119", 0 ],
                    "source": [ "obj-90", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 5 ],
                    "source": [ "obj-92", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 6 ],
                    "source": [ "obj-93", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-132", 0 ],
                    "source": [ "obj-94", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-124", 0 ],
                    "source": [ "obj-95", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 7 ],
                    "source": [ "obj-97", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-131", 8 ],
                    "source": [ "obj-98", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-122", 0 ],
                    "source": [ "obj-99", 0 ]
                }
            }
        ],
        "parameters": {
            "obj-101": [ "Acento 10", "Acento 10", 0 ],
            "obj-102": [ "Acento 11", "Acento 11", 0 ],
            "obj-104": [ "Figura Normal", "Figura Normal", 0 ],
            "obj-105": [ "Figura Acento", "Figura Acento", 0 ],
            "obj-108": [ "Pulsos", "Pulsos", 0 ],
            "obj-109": [ "Acento 12", "Acento 12", 0 ],
            "obj-110": [ "Acento 13", "Acento 13", 0 ],
            "obj-111": [ "Acento 14", "Acento 14", 0 ],
            "obj-115": [ "Giro", "Giro", 0 ],
            "obj-117": [ "Acento 15", "Acento 15", 0 ],
            "obj-118": [ "Acento 16", "Acento 16", 0 ],
            "obj-12": [ "Set", "Set", 0 ],
            "obj-139": [ "Voicing", "Voicing", 0 ],
            "obj-144": [ "Drum", "Drum", 0 ],
            "obj-146": [ "Pad", "Pad", 0 ],
            "obj-148": [ "Ritmo Arm", "Ritmo Arm", 0 ],
            "obj-150": [ "Conduccion", "Conduccion", 0 ],
            "obj-153": [ "IC1 Max", "IC1 Max", 0 ],
            "obj-157": [ "IC1 Min", "IC1 Min", 0 ],
            "obj-158": [ "IC2 Max", "IC2 Max", 0 ],
            "obj-159": [ "IC2 Min", "IC2 Min", 0 ],
            "obj-162": [ "IC3 Max", "IC3 Max", 0 ],
            "obj-163": [ "IC3 Min", "IC3 Min", 0 ],
            "obj-166": [ "IC4 Max", "IC4 Max", 0 ],
            "obj-167": [ "IC4 Min", "IC4 Min", 0 ],
            "obj-168": [ "IC5 Max", "IC5 Max", 0 ],
            "obj-169": [ "IC5 Min", "IC5 Min", 0 ],
            "obj-170": [ "IC6 Min", "IC6 Min", 0 ],
            "obj-171": [ "IC6 Max", "IC6 Max", 0 ],
            "obj-19": [ "Modo", "Modo", 0 ],
            "obj-202": [ "Swing", "Swing", 0 ],
            "obj-206": [ "Rasg", "Rasg", 0 ],
            "obj-208": [ "Dir Rasg", "Dir Rasg", 0 ],
            "obj-210": [ "Rat N", "Rat N", 0 ],
            "obj-212": [ "Rat A", "Rat A", 0 ],
            "obj-214": [ "Prob Rat", "Prob Rat", 0 ],
            "obj-216": [ "Caida", "Caida", 0 ],
            "obj-240": [ "V1 Larg", "V1 Larg", 0 ],
            "obj-242": [ "V1 Puls", "V1 Puls", 0 ],
            "obj-244": [ "V1 Gir", "V1 Gir", 0 ],
            "obj-247": [ "V2 Larg", "V2 Larg", 0 ],
            "obj-249": [ "V2 Puls", "V2 Puls", 0 ],
            "obj-251": [ "V2 Gir", "V2 Gir", 0 ],
            "obj-254": [ "V3 Larg", "V3 Larg", 0 ],
            "obj-256": [ "V3 Puls", "V3 Puls", 0 ],
            "obj-258": [ "V3 Gir", "V3 Gir", 0 ],
            "obj-261": [ "V4 Larg", "V4 Larg", 0 ],
            "obj-263": [ "V4 Puls", "V4 Puls", 0 ],
            "obj-265": [ "V4 Gir", "V4 Gir", 0 ],
            "obj-284": [ "Escuchar", "Escuchar", 0 ],
            "obj-287": [ "Emitir", "Emitir", 0 ],
            "obj-290": [ "Seguir", "Seguir", 0 ],
            "obj-303": [ "M1 Forma", "M1 Forma", 0 ],
            "obj-305": [ "M1 Ciclo", "M1 Ciclo", 0 ],
            "obj-307": [ "M1 Prof", "M1 Prof", 0 ],
            "obj-309": [ "M1 Fase", "M1 Fase", 0 ],
            "obj-311": [ "M1 Dest", "M1 Dest", 0 ],
            "obj-314": [ "M2 Forma", "M2 Forma", 0 ],
            "obj-316": [ "M2 Ciclo", "M2 Ciclo", 0 ],
            "obj-318": [ "M2 Prof", "M2 Prof", 0 ],
            "obj-32": [ "n min", "n min", 0 ],
            "obj-320": [ "M2 Fase", "M2 Fase", 0 ],
            "obj-322": [ "M2 Dest", "M2 Dest", 0 ],
            "obj-325": [ "M3 Forma", "M3 Forma", 0 ],
            "obj-327": [ "M3 Ciclo", "M3 Ciclo", 0 ],
            "obj-329": [ "M3 Prof", "M3 Prof", 0 ],
            "obj-331": [ "M3 Fase", "M3 Fase", 0 ],
            "obj-333": [ "M3 Dest", "M3 Dest", 0 ],
            "obj-336": [ "M4 Forma", "M4 Forma", 0 ],
            "obj-338": [ "M4 Ciclo", "M4 Ciclo", 0 ],
            "obj-340": [ "M4 Prof", "M4 Prof", 0 ],
            "obj-342": [ "M4 Fase", "M4 Fase", 0 ],
            "obj-344": [ "M4 Dest", "M4 Dest", 0 ],
            "obj-349": [ "Slot", "Slot", 0 ],
            "obj-36": [ "n max", "n max", 0 ],
            "obj-372": [ "Azar % Mask", "Azar % Mask", 0 ],
            "obj-375": [ "Azar % Acentos", "Azar % Acentos", 0 ],
            "obj-385": [ "Enlace Tonos", "Enl Ton", 0 ],
            "obj-387": [ "Tension", "Tension", 0 ],
            "obj-389": [ "Curva Tension", "Curva Tn", 0 ],
            "obj-391": [ "Modelo Tension", "TensMod", 0 ],
            "obj-400": [ "Salto Coprimo", "SaltoCop", 0 ],
            "obj-403": [ "Rotacion", "Rotacion", 0 ],
            "obj-406": [ "Rotar x Cambio", "Rot", 0 ],
            "obj-54": [ "Mask 1", "Mask 1", 0 ],
            "obj-55": [ "Mask 2", "Mask 2", 0 ],
            "obj-56": [ "Mask 3", "Mask 3", 0 ],
            "obj-57": [ "Mask 4", "Mask 4", 0 ],
            "obj-58": [ "Mask 5", "Mask 5", 0 ],
            "obj-59": [ "Mask 6", "Mask 6", 0 ],
            "obj-60": [ "Mask 7", "Mask 7", 0 ],
            "obj-61": [ "Mask 8", "Mask 8", 0 ],
            "obj-62": [ "Mask 9", "Mask 9", 0 ],
            "obj-63": [ "Mask 10", "Mask 10", 0 ],
            "obj-64": [ "Mask 11", "Mask 11", 0 ],
            "obj-65": [ "Mask 12", "Mask 12", 0 ],
            "obj-66": [ "Modo Mask", "Modo Mask", 0 ],
            "obj-67": [ "Mask k", "Mask k", 0 ],
            "obj-68": [ "Mask Fit", "Mask Fit", 0 ],
            "obj-76": [ "Acento 1", "Acento 1", 0 ],
            "obj-80": [ "Ciclo Acentos", "Ciclo Acentos", 0 ],
            "obj-82": [ "Acento 2", "Acento 2", 0 ],
            "obj-83": [ "Acento 3", "Acento 3", 0 ],
            "obj-84": [ "Acento 4", "Acento 4", 0 ],
            "obj-86": [ "Vel Min Acento", "Vel Min Acento", 0 ],
            "obj-87": [ "Vel Min Normal", "Vel Min Normal", 0 ],
            "obj-89": [ "Acento 5", "Acento 5", 0 ],
            "obj-90": [ "Ciclo igual a n", "Ciclo igual a n", 0 ],
            "obj-92": [ "Acento 6", "Acento 6", 0 ],
            "obj-93": [ "Acento 7", "Acento 7", 0 ],
            "obj-94": [ "Vel Max Normal", "Vel Max Normal", 0 ],
            "obj-95": [ "Vel Max Acento", "Vel Max Acento", 0 ],
            "obj-97": [ "Acento 8", "Acento 8", 0 ],
            "obj-98": [ "Acento 9", "Acento 9", 0 ],
            "obj-99": [ "Euclid", "Euclid", 0 ],
            "parameterbanks": {
                "0": {
                    "index": 0,
                    "name": "",
                    "parameters": [ "-", "-", "-", "-", "-", "-", "-", "-" ],
                    "buttons": [ "-", "-", "-", "-", "-", "-", "-", "-" ]
                }
            },
            "inherited_shortname": 1
        },
        "autosave": 0,
        "oscreceiveudpport": 0
    }
}