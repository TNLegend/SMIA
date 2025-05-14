# config/iso42001_requirements.py

ISO42001_REQUIREMENTS = [
    {
        "control_id": "A.2.2",
        "control_name": "Politique de l'IA",
        "description": "L’organisation doit documenter une politique de développement ou d’utilisation de systèmes d’IA.",
        "audit_questions": [
            {
                "question": "Existe-t-il une politique documentée en matière d’IA pour le développement ou l’utilisation ?",
                "evidence_refs": ["A22_evidence_1", "A22_evidence_3"]
            },
            {
                "question": "La direction a-t-elle officiellement approuvé la politique ?",
                "evidence_refs": ["A22_evidence_2"]
            },
            {
                "question": "La politique définit-elle les lignes directrices en matière de développement et d’utilisation de l’IA ?",
                "evidence_refs": ["A22_evidence_1", "A22_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A22_evidence_1", "description": "Document de politique d'IA approuvé"},
            {"id": "A22_evidence_2", "description": "Dossiers d'approbation de la direction"},
            {"id": "A22_evidence_3", "description": "Journaux d'examen et de révision des politiques"}
        ]
    },
    {
        "control_id": "A.2.3",
        "control_name": "Alignement avec d'autres politiques organisationnelles",
        "description": "L’organisation déterminera où d'autres politiques peuvent être affectées par ou s'appliquer aux objectifs en matière de systèmes d’IA.",
        "audit_questions": [
            {
                "question": "L’organisation a-t-elle identifié des politiques susceptibles d’être impactées ou applicables aux objectifs de l’IA ?",
                "evidence_refs": ["A23_evidence_1", "A23_evidence_2"]
            },
            {
                "question": "Existe-t-il un processus permettant d’évaluer et de documenter les interdépendances politiques liées à l’IA ?",
                "evidence_refs": ["A23_evidence_2"]
            },
            {
                "question": "Les politiques concernées ont-elles été revues et mises à jour pour s’aligner sur les objectifs de l’IA ?",
                "evidence_refs": ["A23_evidence_3", "A23_evidence_4"]
            },
            {
                "question": "Existe-t-il un mécanisme permettant de garantir un alignement continu entre les objectifs de l’IA et les autres politiques ?",
                "evidence_refs": ["A23_evidence_2", "A23_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A23_evidence_1", "description": "Documentation des politiques affectées identifiées"},
            {"id": "A23_evidence_2", "description": "Registres des évaluations d'impact des politiques"},
            {"id": "A23_evidence_3", "description": "Mises à jour de politiques approuvées reflétant les objectifs de l'IA"},
            {"id": "A23_evidence_4", "description": "Examen et approbation des dossiers de modifications de politique"}
        ]
    },
    {
        "control_id": "A.2.4",
        "control_name": "Révision de la politique d'IA",
        "description": "La politique d’IA doit être révisée à intervalles réguliers ou de manière complémentaire si nécessaire afin de garantir son adéquation, son actualité et son efficacité continues.",
        "audit_questions": [
            {
                "question": "La politique d’IA est-elle révisée à intervalles planifiés ?",
                "evidence_refs": ["A24_evidence_1", "A24_evidence_2"]
            },
            {
                "question": "Des examens supplémentaires sont-ils effectués quand des changements importants se produisent ?",
                "evidence_refs": ["A24_evidence_2", "A24_evidence_3"]
            },
            {
                "question": "Existe-t-il un processus documenté pour l’examen et la mise à jour des politiques ?",
                "evidence_refs": ["A24_evidence_2"]
            },
            {
                "question": "Les résultats des évaluations sont-ils approuvés par la direction ?",
                "evidence_refs": ["A24_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A24_evidence_1", "description": "Calendrier d'examen de la politique d'IA"},
            {"id": "A24_evidence_2", "description": "Journaux d'examen et de mise à jour des politiques"},
            {"id": "A24_evidence_3", "description": "Procès-verbaux de réunion ou rapports d'examen"},
            {"id": "A24_evidence_4", "description": "Dossiers d'approbation des révisions de politique"}
        ]
    },
    {
        "control_id": "A.3.2",
        "control_name": "Rôles et responsabilités de l'IA",
        "description": "Les rôles et responsabilités de l’IA doivent être définis et attribués en fonction des besoins de l’organisation.",
        "audit_questions": [
            {
                "question": "Les rôles et responsabilités en matière de développement, de déploiement et de gouvernance de l’IA ont-ils été formellement définis ?",
                "evidence_refs": ["A32_evidence_1"]
            },
            {
                "question": "Les responsabilités liées à l’IA sont-elles alignées sur les besoins et les objectifs de l’organisation ?",
                "evidence_refs": ["A32_evidence_1"]
            },
            {
                "question": "La direction a-t-elle approuvé et communiqué les rôles et responsabilités de l’IA au personnel concerné ?",
                "evidence_refs": ["A32_evidence_2", "A32_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A32_evidence_1", "description": "Rôles et responsabilités documentés de l'IA"},
            {"id": "A32_evidence_2", "description": "Dossiers d'approbation de la direction"},
            {"id": "A32_evidence_3", "description": "Registres de communication des attributions de rôles"}
        ]
    },
    {
        "control_id": "A.3.3",
        "control_name": "Signalement des préoccupations",
        "description": "L’organisation doit définir et mettre en place un processus pour signaler les préoccupations concernant le rôle de l'organisation par rapport à un système d'IA tout au long de son cycle de vie.",
        "audit_questions": [
            {
                "question": "Existe-t-il un processus documenté pour signaler les préoccupations concernant le rôle de l'organisation dans les systèmes d'IA ?",
                "evidence_refs": ["A33_evidence_1"]
            },
            {
                "question": "Le processus définit-il qui peut signaler, comment signaler et les délais de réponse ?",
                "evidence_refs": ["A33_evidence_1"]
            },
            {
                "question": "Des canaux de signalement (e-mail, portail, hotline) sont-ils établis et communiqués ?",
                "evidence_refs": ["A33_evidence_2", "A33_evidence_4"]
            },
            {
                "question": "Les problèmes liés à l’IA sont-ils suivis, examinés et résolus avec des actions documentées ?",
                "evidence_refs": ["A33_evidence_3"]
            },
            {
                "question": "L’organisation a-t-elle mené des séances de sensibilisation sur le processus de signalement ?",
                "evidence_refs": ["A33_evidence_5"]
            }
        ],
        "evidence_required": [
            {"id": "A33_evidence_1", "description": "Procédure approuvée de signalement des problèmes d'IA"},
            {"id": "A33_evidence_2", "description": "Liste des canaux de signalement disponibles"},
            {"id": "A33_evidence_3", "description": "Registres des rapports de préoccupations liées à l'IA et des mesures prises"},
            {"id": "A33_evidence_4", "description": "Journaux de communication informant les employés du processus"},
            {"id": "A33_evidence_5", "description": "Enregistrements des séances de formation ou de sensibilisation"}
        ]
    },
    {
        "control_id": "A.4.2",
        "control_name": "Documentation des ressources",
        "description": "L’organisation doit identifier et documenter les ressources pertinentes requises pour les activités à des étapes données du cycle de vie du système d’IA et d’autres activités liées à l’IA.",
        "audit_questions": [
            {
                "question": "L’organisation a-t-elle identifié et documenté les ressources nécessaires pour chaque étape du cycle de vie de l’IA ?",
                "evidence_refs": ["A42_evidence_1"]
            },
            {
                "question": "Les ressources humaines, techniques et financières sont-elles explicitement définies ?",
                "evidence_refs": ["A42_evidence_1"]
            },
            {
                "question": "Existe-t-il un processus d’examen périodique et de réaffectation des ressources liées à l’IA ?",
                "evidence_refs": ["A42_evidence_2"]
            },
            {
                "question": "La direction a-t-elle officiellement approuvé l’allocation des ressources pour les activités d’IA ?",
                "evidence_refs": ["A42_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A42_evidence_1", "description": "Exigences documentées en matière de ressources d'IA"},
            {"id": "A42_evidence_2", "description": "Registres d'examen et de mise à jour des ressources"},
            {"id": "A42_evidence_3", "description": "Dossiers d'approbation de l'allocation des ressources"}
        ]
    },
    {
        "control_id": "A.4.3",
        "control_name": "Ressources de données",
        "description": "Dans le cadre de l’identification des ressources, l’organisation doit documenter les informations sur les ressources de données utilisées pour le système d’IA.",
        "audit_questions": [
            {
                "question": "L’organisation a-t-elle documenté les ressources de données utilisées pour le système d’IA ?",
                "evidence_refs": ["A43_evidence_1"]
            },
            {
                "question": "La documentation inclut-elle les sources de données, les types et la propriété ?",
                "evidence_refs": ["A43_evidence_1"]
            },
            {
                "question": "Les enregistrements des ressources de données sont-ils périodiquement révisés et mis à jour ?",
                "evidence_refs": ["A43_evidence_2"]
            }
        ],
        "evidence_required": [
            {"id": "A43_evidence_1", "description": "Inventaire documenté des ressources de données d'IA"},
            {"id": "A43_evidence_2", "description": "Registres de révision et de mise à jour des sources de données"}
        ]
    },
    {
        "control_id": "A.4.4",
        "control_name": "Ressources d'outillage",
        "description": "Dans le cadre de l’identification des ressources, l’organisation doit documenter les informations sur les ressources d’outillage utilisées pour le système d’IA.",
        "audit_questions": [
            {
                "question": "L’organisation a-t-elle documenté les ressources d’outillage utilisées pour le système d’IA ?",
                "evidence_refs": ["A44_evidence_1"]
            },
            {
                "question": "La documentation inclut-t-elle les logiciels, frameworks, services cloud et matériel ?",
                "evidence_refs": ["A44_evidence_1"]
            },
            {
                "question": "Les ressources d’outillage sont-elles régulièrement révisées et mises à jour ?",
                "evidence_refs": ["A44_evidence_2"]
            }
        ],
        "evidence_required": [
            {"id": "A44_evidence_1", "description": "Liste documentée des ressources d'outils d'IA"},
            {"id": "A44_evidence_2", "description": "Registres d'examen et de mise à jour des ressources d'outillage"}
        ]
    },
    {
        "control_id": "A.4.5",
        "control_name": "Ressources système et informatiques",
        "description": "Dans le cadre de l’identification des ressources, l’organisation doit documenter les informations sur le système et les ressources informatiques utilisées pour le système d’IA.",
        "audit_questions": [
            {
                "question": "L’organisation a-t-elle documenté le système et les ressources informatiques utilisés pour le système d’IA ?",
                "evidence_refs": ["A45_evidence_1", "A45_evidence_2"]
            },
            {
                "question": "La documentation précise-t-elle le matériel, logiciels, services cloud et stockage ?",
                "evidence_refs": ["A45_evidence_1", "A45_evidence_2"]
            },
            {
                "question": "Les allocations de ressources sont-elles surveillées et mises à jour à mesure que le système évolue ?",
                "evidence_refs": ["A45_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A45_evidence_1", "description": "Système d'IA documenté et ressources informatiques"},
            {"id": "A45_evidence_2", "description": "Inventaire du matériel, logiciels et services cloud"},
            {"id": "A45_evidence_3", "description": "Registres de surveillance et de mise à jour des ressources"}
        ]
    },
    {
        "control_id": "A.4.6",
        "control_name": "Ressources humaines",
        "description": "Dans le cadre de l’identification des ressources, l’organisation doit documenter les informations sur les ressources humaines et leurs compétences utilisées pour le développement, le déploiement, l’exploitation, la maintenance, la gestion du changement, le transfert et le déclassement du système d’IA.",
        "audit_questions": [
            {
                "question": "L’organisation a-t-elle documenté les ressources humaines impliquées dans chaque étape du cycle de vie de l’IA ?",
                "evidence_refs": ["A46_evidence_1"]
            },
            {
                "question": "Les compétences requises pour ces rôles sont-elles clairement définies ?",
                "evidence_refs": ["A46_evidence_1", "A46_evidence_2"]
            },
            {
                "question": "Existe-t-il un processus de révision et de mise à jour des allocations humaines à mesure que l’IA évolue ?",
                "evidence_refs": ["A46_evidence_3"]
            },
            {
                "question": "La direction a-t-elle approuvé les ressources humaines affectées aux activités d’IA ?",
                "evidence_refs": ["A46_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A46_evidence_1", "description": "Allocation documentée des ressources humaines en IA"},
            {"id": "A46_evidence_2", "description": "Dossiers de compétences et qualifications requises"},
            {"id": "A46_evidence_3", "description": "Registres de révision et de mise à jour des ressources humaines"},
            {"id": "A46_evidence_4", "description": "Dossiers d'approbation du personnel affecté"}
        ]
    },
    {
        "control_id": "A.5.2",
        "control_name": "Processus d'évaluation de l'impact du système d'IA",
        "description": "L’organisation doit établir un processus pour évaluer les conséquences potentielles du système d’IA pour les individus, les groupes et la société tout au long de son cycle de vie.",
        "audit_questions": [
            {
                "question": "L’organisation a-t-elle établi un processus documenté pour évaluer les impacts du système d’IA ?",
                "evidence_refs": ["A52_evidence_1", "A52_evidence_2"]
            },
            {
                "question": "L’évaluation couvre-t-elle toutes les étapes du cycle de vie ?",
                "evidence_refs": ["A52_evidence_1", "A52_evidence_2"]
            },
            {
                "question": "Les impacts éthiques, juridiques et sociaux sont-ils pris en compte ?",
                "evidence_refs": ["A52_evidence_1", "A52_evidence_2"]
            },
            {
                "question": "Existe-t-il un processus de mise à jour de l’évaluation en fonction des changements du système ?",
                "evidence_refs": ["A52_evidence_3"]
            },
            {
                "question": "La direction a-t-elle approuvé le cadre d’évaluation ?",
                "evidence_refs": ["A52_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A52_evidence_1", "description": "Processus documenté d'évaluation de l'impact de l'IA"},
            {"id": "A52_evidence_2", "description": "Registres des évaluations d'impact réalisées"},
            {"id": "A52_evidence_3", "description": "Journaux de révision et de mise à jour"},
            {"id": "A52_evidence_4", "description": "Dossiers d'approbation du cadre d'évaluation"}
        ]
    },
    {
        "control_id": "A.5.3",
        "control_name": "Documentation des évaluations d'impact du système d'IA",
        "description": "L’organisation doit documenter les résultats des évaluations d’impact du système d’IA et conserver les résultats pendant une période définie.",
        "audit_questions": [
            {
                "question": "Les évaluations d’impact sont-elles documentées après chaque exercice ?",
                "evidence_refs": ["A53_evidence_1"]
            },
            {
                "question": "Une période de conservation des résultats est-elle définie et respectée ?",
                "evidence_refs": ["A53_evidence_2"]
            },
            {
                "question": "Les résultats sont-ils examinés et approuvés par les parties prenantes ?",
                "evidence_refs": ["A53_evidence_3"]
            },
            {
                "question": "Un stockage sécurisé et accessible est-il assuré ?",
                "evidence_refs": ["A53_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A53_evidence_1", "description": "Rapports d'évaluation d'impact documentés"},
            {"id": "A53_evidence_2", "description": "Politique de rétention des résultats"},
            {"id": "A53_evidence_3", "description": "Registres d'examen et d'approbation des évaluations"},
            {"id": "A53_evidence_4", "description": "Logs de stockage sécurisé des évaluations"}
        ]
    },
    {
        "control_id": "A.5.4",
        "control_name": "Évaluer l'impact du système d'IA sur les individus ou les groupes",
        "description": "L’organisation doit évaluer et documenter les impacts potentiels des systèmes d’IA sur les individus ou groupes tout au long du cycle de vie.",
        "audit_questions": [
            {
                "question": "Une évaluation des impacts sur les individus/groupes a-t-elle été réalisée ?",
                "evidence_refs": ["A54_evidence_1", "A54_evidence_3"]
            },
            {
                "question": "L’évaluation est-t-elle alignée sur le cycle de vie du système ?",
                "evidence_refs": ["A54_evidence_1"]
            },
            {
                "question": "Les risques éthiques, juridiques et sociétaux sont-ils pris en compte ?",
                "evidence_refs": ["A54_evidence_1", "A54_evidence_3"]
            },
            {
                "question": "Un processus de mise à jour des évaluations existe-t-il ?",
                "evidence_refs": ["A54_evidence_2"]
            }
        ],
        "evidence_required": [
            {"id": "A54_evidence_1", "description": "Rapport d'évaluation d'impact documenté"},
            {"id": "A54_evidence_2", "description": "Registres des revues et mises à jour des impacts"},
            {"id": "A54_evidence_3", "description": "Résultats des évaluations des risques liés à l'IA"}
        ]
    },
    {
        "control_id": "A.5.5",
        "control_name": "Évaluer les impacts sociétaux des systèmes d'IA",
        "description": "L’organisation doit évaluer et documenter les impacts sociétaux potentiels de ses systèmes d’IA tout au long de leur cycle de vie.",
        "audit_questions": [
            {
                "question": "Une évaluation des impacts sociétaux a-t-elle été réalisée et documentée ?",
                "evidence_refs": ["A55_evidence_1"]
            },
            {
                "question": "L’évaluation est-t-elle tenue à jour tout au long du cycle de vie ?",
                "evidence_refs": ["A55_evidence_2"]
            },
            {
                "question": "Les risques éthiques, juridiques et sociaux sont-ils couverts ?",
                "evidence_refs": ["A55_evidence_1"]
            },
            {
                "question": "Des mesures d’atténuation sont-elles définies pour les impacts négatifs ?",
                "evidence_refs": ["A55_evidence_3"]
            },
            {
                "question": "La direction a-t-elle approuvé l’évaluation sociétale ?",
                "evidence_refs": ["A55_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A55_evidence_1", "description": "Rapports d'évaluation de l'impact sociétal"},
            {"id": "A55_evidence_2", "description": "Registres des revues et mises à jour périodiques"},
            {"id": "A55_evidence_3", "description": "Plans d'atténuation des risques sociétaux"},
            {"id": "A55_evidence_4", "description": "Dossiers d'approbation de la direction"}
        ]
    },
    {
        "control_id": "A.6.1.2",
        "control_name": "Objectifs pour un développement responsable du système d'IA",
        "description": "L’organisation doit identifier et documenter les objectifs pour guider le développement responsable des systèmes d’IA et intégrer des mesures pour les atteindre.",
        "audit_questions": [
            {
                "question": "Des objectifs de développement responsable ont-ils été définis et documentés ?",
                "evidence_refs": ["A612_evidence_1"]
            },
            {
                "question": "Sont-ils alignés sur les exigences éthiques, légales et commerciales ?",
                "evidence_refs": ["A612_evidence_1"]
            },
            {
                "question": "Des mesures sont-elles intégrées dans le cycle de développement ?",
                "evidence_refs": ["A612_evidence_2"]
            },
            {
                "question": "Un processus de révision périodique des objectifs existe-t-il ?",
                "evidence_refs": ["A612_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A612_evidence_1", "description": "Objectifs de développement de l'IA documentés"},
            {"id": "A612_evidence_2", "description": "Processus du cycle de vie de l'IA avec mesures intégrées"},
            {"id": "A612_evidence_3", "description": "Registres de revue des objectifs et mises à jour"}
        ]
    },
    {
        "control_id": "A.6.1.3",
        "control_name": "Processus de conception et de développement responsables de systèmes d'IA",
        "description": "L’organisation doit définir et documenter les processus spécifiques pour la conception et le développement responsables du système d’IA.",
        "audit_questions": [
            {
                "question": "Des processus de conception et développement responsables de l’IA sont-ils définis et documentés ?",
                "evidence_refs": ["A613_evidence_1"]
            },
            {
                "question": "Ces processus intègrent-ils les considérations éthiques, juridiques et de sécurité ?",
                "evidence_refs": ["A613_evidence_1"]
            },
            {
                "question": "Un mécanisme formel d’examen et d’approbation existe-t-il ?",
                "evidence_refs": ["A613_evidence_2"]
            },
            {
                "question": "Les équipes de développement ont-elles été formées à ces processus ?",
                "evidence_refs": ["A613_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A613_evidence_1", "description": "Processus de conception et développement de l'IA documentés"},
            {"id": "A613_evidence_2", "description": "Registres d'examen et d'approbation des processus"},
            {"id": "A613_evidence_3", "description": "Dossiers de formation/sensibilisation pour les équipes d'IA"}
        ]
    },
    {
        "control_id": "A.6.2.2",
        "control_name": "Exigences et spécifications du système d'IA",
        "description": "L’organisation doit spécifier et documenter les exigences relatives aux nouveaux systèmes d’IA ou aux améliorations matérielles des systèmes existants.",
        "audit_questions": [
            {
                "question": "Les exigences des nouveaux systèmes et améliorations IA sont-elles documentées ?",
                "evidence_refs": ["A622_evidence_1"]
            },
            {
                "question": "Couvrent-elles fonctionnalité, sécurité, conformité et enjeux éthiques ?",
                "evidence_refs": ["A622_evidence_1"]
            },
            {
                "question": "Un processus d’approbation formel existe-t-il avant mise en œuvre ?",
                "evidence_refs": ["A622_evidence_2"]
            },
            {
                "question": "Les exigences sont-elles régulièrement révisées et mises à jour ?",
                "evidence_refs": ["A622_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A622_evidence_1", "description": "Exigences documentées du système d'IA"},
            {"id": "A622_evidence_2", "description": "Dossiers d'approbation pour systèmes IA nouveaux/améliorés"},
            {"id": "A622_evidence_3", "description": "Journaux de révision et mise à jour des exigences"}
        ]
    },
    {
        "control_id": "A.6.2.3",
        "control_name": "Documentation de la conception et du développement du système d'IA",
        "description": "L’organisation doit documenter la conception et le développement du système d’IA en fonction des objectifs organisationnels, des exigences documentées et des critères de spécification.",
        "audit_questions": [
            {
                "question": "Le processus de conception et développement IA est-il documenté ?",
                "evidence_refs": ["A623_evidence_1"]
            },
            {
                "question": "S’appuie-t-il sur les objectifs et exigences organisationnels ?",
                "evidence_refs": ["A623_evidence_1", "A623_evidence_2"]
            },
            {
                "question": "Des critères de spécification sont-ils inclus ?",
                "evidence_refs": ["A623_evidence_2"]
            },
            {
                "question": "Un processus de mise à jour de la documentation existe-t-il ?",
                "evidence_refs": ["A623_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A623_evidence_1", "description": "Processus documenté de conception et développement de l'IA"},
            {"id": "A623_evidence_2", "description": "Documents relatifs aux exigences et spécifications"},
            {"id": "A623_evidence_3", "description": "Registres de révision et mise à jour de la conception"}
        ]
    },
    {
        "control_id": "A.6.2.4",
        "control_name": "Vérification et validation du système d'IA",
        "description": "L’organisation doit définir et documenter les mesures de vérification et validation du système d’IA et spécifier les critères de leur utilisation.",
        "audit_questions": [
            {
                "question": "Des mesures de V&V pour les systèmes d’IA sont-elles définies et documentées ?",
                "evidence_refs": ["A624_evidence_1"]
            },
            {
                "question": "Les critères d’application des V&V sont-ils clairement définis ?",
                "evidence_refs": ["A624_evidence_2"]
            },
            {
                "question": "Un processus de révision des mesures V&V existe-t-il lors des changements ?",
                "evidence_refs": ["A624_evidence_3"]
            },
            {
                "question": "La direction a-t-elle approuvé le cadre V&V ?",
                "evidence_refs": ["A624_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A624_evidence_1", "description": "Mesures documentées de vérification et validation de l'IA"},
            {"id": "A624_evidence_2", "description": "Critères définis pour l'application de la V&V"},
            {"id": "A624_evidence_3", "description": "Registres de mise en œuvre et d'examen de la V&V"},
            {"id": "A624_evidence_4", "description": "Dossiers d'approbation du cadre V&V"}
        ]
    },
    {
        "control_id": "A.6.2.5",
        "control_name": "Déploiement du système d'IA",
        "description": "L’organisation doit documenter un plan de déploiement et s’assurer que les exigences appropriées sont respectées avant le déploiement.",
        "audit_questions": [
            {
                "question": "Un plan de déploiement IA documenté couvre-t-il toutes les étapes ?",
                "evidence_refs": ["A625_evidence_1", "A625_evidence_3"]
            },
            {
                "question": "Le plan définit-il les contrôles et exigences pré-déploiement ?",
                "evidence_refs": ["A625_evidence_1"]
            },
            {
                "question": "Un processus d’approbation de conformité avant déploiement existe-t-il ?",
                "evidence_refs": ["A625_evidence_1"]
            },
            {
                "question": "La direction a-t-elle approuvé le plan de déploiement ?",
                "evidence_refs": ["A625_evidence_2", "A625_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A625_evidence_1", "description": "Plan de déploiement documenté du système d'IA"},
            {"id": "A625_evidence_2", "description": "Dossiers d'approbation du plan de déploiement"},
            {"id": "A625_evidence_3", "description": "Journaux de révision et mise à jour du plan"}
        ]
    },
    {
        "control_id": "A.6.2.6",
        "control_name": "Fonctionnement et surveillance du système d'IA",
        "description": "L’organisation doit définir et documenter les éléments nécessaires au fonctionnement continu du système d’IA, incluant maintenance, surveillance et assistance.",
        "audit_questions": [
            {
                "question": "Les éléments essentiels au fonctionnement continu sont-ils documentés ?",
                "evidence_refs": ["A626_evidence_1", "A626_evidence_2"]
            },
            {
                "question": "La documentation couvre-t-elle maintenance, surveillance et assistance ?",
                "evidence_refs": ["A626_evidence_1", "A626_evidence_2"]
            },
            {
                "question": "Les procédures opérationnelles sont-elles revues et mises à jour régulièrement ?",
                "evidence_refs": ["A626_evidence_3"]
            },
            {
                "question": "La direction a-t-elle approuvé le cadre opérationnel ?",
                "evidence_refs": ["A626_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A626_evidence_1", "description": "Exigences opérationnelles documentées du système d'IA"},
            {"id": "A626_evidence_2", "description": "Journaux de maintenance et de surveillance"},
            {"id": "A626_evidence_3", "description": "Registres de révision et mise à jour opérationnelle"},
            {"id": "A626_evidence_4", "description": "Dossiers d'approbation du cadre opérationnel"}
        ]
    },
    {
        "control_id": "A.6.2.7",
        "control_name": "Documentation technique du système d'IA",
        "description": "L’organisation doit déterminer et fournir la documentation technique nécessaire pour chaque catégorie de parties intéressées (utilisateurs, partenaires, régulateurs).",
        "audit_questions": [
            {
                "question": "La documentation technique nécessaire est-elle identifiée pour chaque partie prenante ?",
                "evidence_refs": ["A627_evidence_1"]
            },
            {
                "question": "Couvre-t-elle utilisateurs, partenaires et autorités de contrôle ?",
                "evidence_refs": ["A627_evidence_1"]
            },
            {
                "question": "Un processus de mise à jour et conservation existe-t-il ?",
                "evidence_refs": ["A627_evidence_3"]
            },
            {
                "question": "Des méthodes de distribution aux parties concernées sont-elles définies ?",
                "evidence_refs": ["A627_evidence_2"]
            }
        ],
        "evidence_required": [
            {"id": "A627_evidence_1", "description": "Liste de la documentation technique par catégorie de public"},
            {"id": "A627_evidence_2", "description": "Registres de distribution de la documentation"},
            {"id": "A627_evidence_3", "description": "Journaux de mise à jour et maintenance"}
        ]
    },
    {
        "control_id": "A.6.2.8",
        "control_name": "Enregistrement des journaux d'événements par le système d'IA",
        "description": "L’organisation doit déterminer les phases du cycle de vie où la journalisation doit être activée, au minimum lors de l’utilisation du système d’IA.",
        "audit_questions": [
            {
                "question": "Les phases nécessitant journalisation sont-elles identifiées ?",
                "evidence_refs": ["A628_evidence_1"]
            },
            {
                "question": "Les journaux sont-ils activés lors de l’utilisation du système ?",
                "evidence_refs": ["A628_evidence_2"]
            },
            {
                "question": "Le processus de journalisation capture-t-il toutes les décisions et activités pertinentes ?",
                "evidence_refs": ["A628_evidence_1", "A628_evidence_2"]
            },
            {
                "question": "Un processus de conservation et gestion des journaux est-il documenté ?",
                "evidence_refs": ["A628_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A628_evidence_1", "description": "Exigences documentées en matière de journalisation IA"},
            {"id": "A628_evidence_2", "description": "Enregistrements de journaux pour la phase d'utilisation"},
            {"id": "A628_evidence_3", "description": "Politique de conservation et gestion des journaux"}
        ]
    },
    {
        "control_id": "A.7.2",
        "control_name": "Données pour le développement et l'amélioration du système d'IA",
        "description": "L’organisation doit définir, documenter et mettre en œuvre des processus de gestion des données liés au développement des systèmes d’IA.",
        "audit_questions": [
            {
                "question": "Des processus de gestion des données pour le développement IA sont-ils documentés ?",
                "evidence_refs": ["A72_evidence_1"]
            },
            {
                "question": "Couvrent-ils collecte, stockage, traitement et élimination des données ?",
                "evidence_refs": ["A72_evidence_1"]
            },
            {
                "question": "Les pratiques sont-elles conformes aux exigences réglementaires et de sécurité ?",
                "evidence_refs": ["A72_evidence_3"]
            },
            {
                "question": "Un mécanisme de surveillance du respect des processus existe-t-il ?",
                "evidence_refs": ["A72_evidence_2", "A72_evidence_3"]
            },
            {
                "question": "Les équipes IA sont-elles formées aux politiques de gestion des données ?",
                "evidence_refs": ["A72_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A72_evidence_1", "description": "Processus documentés de gestion des données d'IA"},
            {"id": "A72_evidence_2", "description": "Registres des pratiques de traitement (collecte, stockage, etc.)"},
            {"id": "A72_evidence_3", "description": "Rapports/journaux d'audit de conformité"},
            {"id": "A72_evidence_4", "description": "Dossiers de formation des équipes IA"}
        ]
    },
    {
        "control_id": "A.7.3",
        "control_name": "Acquisition de données",
        "description": "L’organisation doit déterminer et documenter les détails concernant l’acquisition et la sélection des données utilisées dans les systèmes d’IA.",
        "audit_questions": [
            {
                "question": "Les critères et processus d’acquisition et sélection des données sont-ils documentés ?",
                "evidence_refs": ["A73_evidence_1"]
            },
            {
                "question": "Les sources sont-elles vérifiées pour exactitude, fiabilité et conformité ?",
                "evidence_refs": ["A73_evidence_2"]
            },
            {
                "question": "L’organisation conserve-t-elle les enregistrements de provenance et justification de sélection ?",
                "evidence_refs": ["A73_evidence_3"]
            },
            {
                "question": "Un processus de mise à jour périodique des critères existe-t-il ?",
                "evidence_refs": ["A73_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A73_evidence_1", "description": "Critères d'acquisition et de sélection de données documentés"},
            {"id": "A73_evidence_2", "description": "Registres de vérification et d'approbation des sources"},
            {"id": "A73_evidence_3", "description": "Journaux de provenance des données et justifications"},
            {"id": "A73_evidence_4", "description": "Registres de mise à jour des critères de sélection"}
        ]
    },
    {
        "control_id": "A.7.4",
        "control_name": "Qualité des données pour les systèmes d'IA",
        "description": "L’organisation doit définir et documenter les exigences en matière de qualité des données et s’assurer que les données utilisées répondent à ces exigences.",
        "audit_questions": [
            {
                "question": "Les exigences de qualité des données sont-elles définies et documentées ?",
                "evidence_refs": ["A74_evidence_1"]
            },
            {
                "question": "Des critères d’exactitude, exhaustivité, cohérence et fiabilité sont-ils établis ?",
                "evidence_refs": ["A74_evidence_1"]
            },
            {
                "question": "Existe-t-il un processus de validation et surveillance de la qualité avant et pendant l’exploitation ?",
                "evidence_refs": ["A74_evidence_2"]
            },
            {
                "question": "Les contrôles qualité sont-ils revus et mis à jour selon les besoins du système ?",
                "evidence_refs": ["A74_evidence_2", "A74_evidence_3"]
            },
            {
                "question": "La direction a-t-elle approuvé les normes de qualité des données ?",
                "evidence_refs": ["A74_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A74_evidence_1", "description": "Exigences documentées en matière de qualité des données"},
            {"id": "A74_evidence_2", "description": "Registres des processus de validation et surveillance"},
            {"id": "A74_evidence_3", "description": "Rapports d’évaluation et corrections de la qualité des données"},
            {"id": "A74_evidence_4", "description": "Dossiers d'approbation des normes de qualité"}
        ]
    },
    {
        "control_id": "A.7.5",
        "control_name": "Provenance des données",
        "description": "L’organisation doit définir et documenter un processus d’enregistrement de la provenance des données utilisées dans ses systèmes d’IA tout au long de leur cycle de vie.",
        "audit_questions": [
            {
                "question": "Le processus de provenance des données est-il défini et documenté ?",
                "evidence_refs": ["A75_evidence_1"]
            },
            {
                "question": "Couvre-t-il origine, transformations et utilisation tout au long du cycle ?",
                "evidence_refs": ["A75_evidence_1"]
            },
            {
                "question": "Les enregistrements de provenance sont-ils conservés et mis à jour ?",
                "evidence_refs": ["A75_evidence_2", "A75_evidence_3"]
            },
            {
                "question": "Un mécanisme de vérification de l’intégrité des enregistrements existe-t-il ?",
                "evidence_refs": ["A75_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A75_evidence_1", "description": "Processus d'enregistrement de la provenance des données documenté"},
            {"id": "A75_evidence_2", "description": "Journaux/enregistrements de provenance des données"},
            {"id": "A75_evidence_3", "description": "Rapports d’examen et mises à jour périodiques"},
            {"id": "A75_evidence_4", "description": "Rapports de vérification de l’intégrité des données"}
        ]
    },
    {
        "control_id": "A.7.6",
        "control_name": "Préparation des données",
        "description": "L’organisation doit définir et documenter ses critères de sélection des méthodes de préparation des données et les méthodes à utiliser.",
        "audit_questions": [
            {
                "question": "Les critères de sélection des méthodes de préparation sont-ils définis et documentés ?",
                "evidence_refs": ["A76_evidence_1"]
            },
            {
                "question": "Les méthodes choisies sont-elles alignées sur les besoins du système d’IA ?",
                "evidence_refs": ["A76_evidence_1", "A76_evidence_2"]
            },
            {
                "question": "Un processus de mise à jour des critères existe-t-il selon l’évolution des besoins ?",
                "evidence_refs": ["A76_evidence_3"]
            },
            {
                "question": "La direction a-t-elle approuvé les critères de préparation des données ?",
                "evidence_refs": ["A76_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A76_evidence_1", "description": "Critères de préparation des données documentés"},
            {"id": "A76_evidence_2", "description": "Liste des méthodes de préparation approuvées"},
            {"id": "A76_evidence_3", "description": "Registres de révision et mise à jour des critères"},
            {"id": "A76_evidence_4", "description": "Dossiers d'approbation des normes de préparation"}
        ]
    },
    {
        "control_id": "A.8.2",
        "control_name": "Documentation système et informations pour les utilisateurs",
        "description": "L’organisation doit identifier et fournir les informations nécessaires aux utilisateurs du système d’IA.",
        "audit_questions": [
            {
                "question": "Les informations nécessaires aux utilisateurs sont-elles identifiées et documentées ?",
                "evidence_refs": ["A82_evidence_1"]
            },
            {
                "question": "Ces informations sont-elles clairement accessibles ?",
                "evidence_refs": ["A82_evidence_2"]
            },
            {
                "question": "L’organisation fournit-elle instructions, limites et risques potentiels ?",
                "evidence_refs": ["A82_evidence_1"]
            },
            {
                "question": "Un processus de mise à jour et communication des modifications existe-t-il ?",
                "evidence_refs": ["A82_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A82_evidence_1", "description": "Directives d'utilisation du système d'IA documentées"},
            {"id": "A82_evidence_2", "description": "Registres des informations fournies aux utilisateurs"},
            {"id": "A82_evidence_3", "description": "Journaux de communication des mises à jour"}
        ]
    },
    {
        "control_id": "A.8.3",
        "control_name": "Rapports externes",
        "description": "L’organisation doit fournir aux parties intéressées les moyens de signaler les impacts négatifs du système d’IA.",
        "audit_questions": [
            {
                "question": "Un mécanisme de signalement des impacts négatifs est-il en place ?",
                "evidence_refs": ["A83_evidence_1"]
            },
            {
                "question": "Les canaux (portail, e-mail, hotline) sont-ils accessibles et communiqués ?",
                "evidence_refs": ["A83_evidence_2", "A83_evidence_4"]
            },
            {
                "question": "Un processus traite-t-il et répond-it aux signalements ?",
                "evidence_refs": ["A83_evidence_1", "A83_evidence_3"]
            },
            {
                "question": "Les rapports et résolutions sont-ils documentés pour l’imputabilité ?",
                "evidence_refs": ["A83_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A83_evidence_1", "description": "Procédure approuvée de signalement des impacts négatifs documentée"},
            {"id": "A83_evidence_2", "description": "Liste des canaux de signalement disponibles"},
            {"id": "A83_evidence_3", "description": "Registres des cas signalés et mesures prises"},
            {"id": "A83_evidence_4", "description": "Journaux informant les parties prenantes du processus"}
        ]
    },
    {
        "control_id": "A.8.4",
        "control_name": "Communication des incidents",
        "description": "L’organisation doit déterminer et documenter un plan de communication des incidents aux utilisateurs du système d’IA.",
        "audit_questions": [
            {
                "question": "Un plan de communication des incidents IA est-il documenté ?",
                "evidence_refs": ["A84_evidence_1","A84_evidence_2", "A84_evidence_4"]
            },
            {
                "question": "Le plan détaille-t-il types d’incidents, délais et canaux de notification ?",
                "evidence_refs": ["A84_evidence_1","A84_evidence_2", "A84_evidence_4"]
            },
            {
                "question": "Les rôles et responsabilités pour notification sont-ils définis ?",
                "evidence_refs": ["A84_evidence_1"]
            },
            {
                "question": "Le plan est-il testé et revu périodiquement ?",
                "evidence_refs": ["A84_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A84_evidence_1", "description": "Plan de communication des incidents documenté"},
            {"id": "A84_evidence_2", "description": "Procédures de notification d'incident définies"},
            {"id": "A84_evidence_3", "description": "Registres des tests et mises à jour du plan"},
            {"id": "A84_evidence_4", "description": "Journaux d'incidents et notifications aux utilisateurs"}
        ]
    },
    {
        "control_id": "A.8.5",
        "control_name": "Informations pour les parties intéressées",
        "description": "L’organisation doit déterminer et documenter ses obligations en matière de communication d’informations sur le système d’IA aux parties intéressées.",
        "audit_questions": [
            {
                "question": "Les obligations de reporting IA aux parties sont-elles identifiées et documentées ?",
                "evidence_refs": ["A85_evidence_1"]
            },
            {
                "question": "Les exigences sont-elles conformes aux obligations légales, réglementaires et contractuelles ?",
                "evidence_refs": ["A85_evidence_2"]
            },
            {
                "question": "Un processus de révision et mise à jour des obligations existe-t-il ?",
                "evidence_refs": ["A85_evidence_1", "A85_evidence_3"]
            },
            {
                "question": "Les responsabilités en reporting sont-elles attribuées au sein de l’organisation ?",
                "evidence_refs": ["A85_evidence_1", "A85_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A85_evidence_1", "description": "Obligations de reporting documentées du système d'IA"},
            {"id": "A85_evidence_2", "description": "Dossiers de conformité réglementaire et contractuelle"},
            {"id": "A85_evidence_3", "description": "Registres de mise à jour des exigences de reporting"},
            {"id": "A85_evidence_4", "description": "Documentation des rôles et responsabilités de reporting"}
        ]
    },
    {
        "control_id": "A.9.2",
        "control_name": "Processus pour une utilisation responsable des systèmes d'IA",
        "description": "L’organisation doit définir et documenter les processus pour l’utilisation responsable des systèmes d’IA.",
        "audit_questions": [
            {
                "question": "Des processus d’utilisation responsable de l’IA sont-ils définis et documentés ?",
                "evidence_refs": ["A92_evidence_1"]
            },
            {
                "question": "Ces processus couvrent-t-ils éthique, équité, transparence et responsabilité ?",
                "evidence_refs": ["A92_evidence_1"]
            },
            {
                "question": "Des lignes directrices d’atténuation des risques sont-elles en place ?",
                "evidence_refs": ["A92_evidence_3"]
            },
            {
                "question": "La direction a-t-elle approuvé ces processus ?",
                "evidence_refs": ["A92_evidence_2"]
            },
            {
                "question": "Le personnel est-il formé à l’utilisation responsable de l’IA ?",
                "evidence_refs": ["A92_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A92_evidence_1", "description": "Processus documentés d'utilisation responsable de l'IA"},
            {"id": "A92_evidence_2", "description": "Dossiers d'approbation de la direction"},
            {"id": "A92_evidence_3", "description": "Directives d'atténuation des risques pour l'utilisation de l'IA"},
            {"id": "A92_evidence_4", "description": "Dossiers de formation et sensibilisation à l’éthique IA"}
        ]
    },
    {
        "control_id": "A.9.3",
        "control_name": "Objectifs pour une utilisation responsable du système d'IA",
        "description": "L’organisation doit identifier et documenter les objectifs pour guider l’utilisation responsable des systèmes d’IA.",
        "audit_questions": [
            {
                "question": "Les objectifs d’utilisation responsable de l’IA sont-ils définis et documentés ?",
                "evidence_refs": ["A93_evidence_1", "A93_evidence_2"]
            },
            {
                "question": "Sont-ils conformes aux exigences éthiques, légales et organisationnelles ?",
                "evidence_refs": ["A93_evidence_1"]
            },
            {
                "question": "Sont-ils communiqués aux parties prenantes ?",
                "evidence_refs": ["A93_evidence_3"]
            },
            {
                "question": "Un processus de révision et mise à jour existe-t-il ?",
                "evidence_refs": ["A93_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A93_evidence_1", "description": "Objectifs documentés en matière de responsabilité IA"},
            {"id": "A93_evidence_2", "description": "Dossiers d'approbation de la direction"},
            {"id": "A93_evidence_3", "description": "Journaux de communication des objectifs"},
            {"id": "A93_evidence_4", "description": "Registres de révision et mise à jour des objectifs"}
        ]
    },
    {
        "control_id": "A.9.4",
        "control_name": "Utilisation prévue du système d'IA",
        "description": "L’organisation doit s’assurer que le système d’IA est utilisé conformément aux utilisations prévues et à la documentation associée.",
        "audit_questions": [
            {
                "question": "Un processus garantit-il l’utilisation aux seules fins prévues ?",
                "evidence_refs": ["A94_evidence_1", "A94_evidence_2", "A94_evidence_4"]
            },
            {
                "question": "L’organisation conserve-t-elle des journaux d’utilisation et surveille-t-elle les écarts ?",
                "evidence_refs": ["A94_evidence_2", "A94_evidence_3"]
            },
            {
                "question": "Les utilisateurs disposent-ils de directives claires sur l’utilisation prévue ?",
                "evidence_refs": ["A94_evidence_1", "A94_evidence_4"]
            },
            {
                "question": "Existe-t-il un mécanisme pour détecter et traiter l’utilisation non autorisée ?",
                "evidence_refs": ["A94_evidence_2", "A94_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A94_evidence_1", "description": "Directives d'utilisation documentées de l'IA"},
            {"id": "A94_evidence_2", "description": "Journaux d'utilisation du système et rapports de surveillance"},
            {"id": "A94_evidence_3", "description": "Registres des incidents d'utilisation non autorisée et mesures prises"},
            {"id": "A94_evidence_4", "description": "Dossiers de formation/reconnaissance de l'utilisation prévue"}
        ]
    },
    {
        "control_id": "A.10.2",
        "control_name": "Répartition des responsabilités",
        "description": "L’organisation doit veiller à ce que les responsabilités au sein du cycle de vie du système d’IA soient réparties entre l’organisation, ses partenaires, ses fournisseurs, ses clients et les tiers.",
        "audit_questions": [
            {
                "question": "Les responsabilités pour chaque étape IA sont-elles documentées ?",
                "evidence_refs": ["A102_evidence_1"]
            },
            {
                "question": "Les rôles sont-ils clairement répartis entre parties internes et externes ?",
                "evidence_refs": ["A102_evidence_1", "A102_evidence_2"]
            },
            {
                "question": "Toutes les parties ont-elles accepté les responsabilités qui leur sont assignées ?",
                "evidence_refs": ["A102_evidence_2", "A102_evidence_4"]
            },
            {
                "question": "Un processus de révision des responsabilités existe-t-il avec l’évolution du système ?",
                "evidence_refs": ["A102_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A102_evidence_1", "description": "Matrice de responsabilité IA documentée"},
            {"id": "A102_evidence_2", "description": "Accords/contrats définissant les rôles IA"},
            {"id": "A102_evidence_3", "description": "Registres de revue et mise à jour périodique des responsabilités"},
            {"id": "A102_evidence_4", "description": "Communications ou confirmations des parties concernées"}
        ]
    },
    {
        "control_id": "A.10.3",
        "control_name": "Fournisseurs",
        "description": "L’organisation doit établir un processus pour garantir que l’utilisation des services, produits ou matériaux fournis par les fournisseurs est conforme à l’approche responsable de l’organisation en matière d’IA.",
        "audit_questions": [
            {
                "question": "Un processus d’évaluation de conformité IA des fournisseurs est-il documenté ?",
                "evidence_refs": ["A103_evidence_1"]
            },
            {
                "question": "Le processus vérifie-t-il l’adhérence aux principes d’IA responsables de l’organisation ?",
                "evidence_refs": ["A103_evidence_1", "A103_evidence_3"]
            },
            {
                "question": "Les accords fournisseurs incluent-ils des clauses IA responsables et de sécurité ?",
                "evidence_refs": ["A103_evidence_2"]
            },
            {
                "question": "Un mécanisme de surveillance et de réévaluation continue des fournisseurs existe-t-il ?",
                "evidence_refs": ["A103_evidence_3", "A103_evidence_4"]
            }
        ],
        "evidence_required": [
            {"id": "A103_evidence_1", "description": "Processus d'évaluation de la conformité IA des fournisseurs documenté"},
            {"id": "A103_evidence_2", "description": "Accords fournisseurs avec clauses IA responsables"},
            {"id": "A103_evidence_3", "description": "Registres d'évaluation et d'examen de conformité des fournisseurs"},
            {"id": "A103_evidence_4", "description": "Preuves de surveillance et réévaluation continues des fournisseurs"}
        ]
    },
    {
        "control_id": "A.10.4",
        "control_name": "Clients",
        "description": "L’organisation doit s’assurer que son approche responsable en matière d’IA prend en compte les attentes et les besoins de ses clients.",
        "audit_questions": [
            {
                "question": "Un processus d’évaluation des attentes des clients IA est-il documenté ?",
                "evidence_refs": ["A104_evidence_1"]
            },
            {
                "question": "Les exigences clients sont-elles intégrées à la conception et déploiement IA ?",
                "evidence_refs": ["A104_evidence_1", "A104_evidence_2"]
            },
            {
                "question": "Un mécanisme de collecte et intégration des retours clients existe-t-il ?",
                "evidence_refs": ["A104_evidence_2"]
            },
            {
                "question": "La direction a-t-elle approuvé l’approche de prise en compte des clients ?",
                "evidence_refs": ["A104_evidence_3"]
            }
        ],
        "evidence_required": [
            {"id": "A104_evidence_1", "description": "Processus d'évaluation des attentes des clients documenté"},
            {"id": "A104_evidence_2", "description": "Enregistrements des commentaires clients et ajustements IA"},
            {"id": "A104_evidence_3", "description": "Dossiers d'approbation de l'approche client-centrée IA"}
        ]
    }
]