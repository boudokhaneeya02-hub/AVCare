# Suivi AVK — Application de suivi des patients sous anticoagulants

Application web (Django) pour le suivi de patients sous traitement AVK
(antivitamine K), en particulier après un AVC : fiche patient, rendez-vous,
historique INR/doses, et aide à la lecture de l'INR.

**Important — périmètre médical.** L'application fournit une **aide à la
lecture** de la valeur d'INR par rapport à la cible définie par le médecin.
Elle n'émet et n'automatise **aucune décision de traitement**. Toute
modification de dose reste sous la responsabilité du médecin. Voir
`consultations/inr_logic.py` pour le détail de cette logique.

---

## 1. Fonctionnalités

- **Comptes médecins** (multi-comptes, email + mot de passe). Chaque médecin
  ne voit que ses propres patients — isolation stricte vérifiée par tests.
- **Interface adaptée au mobile** : tableaux, formulaires et navigation
  pensés pour une consultation rapide depuis le téléphone du médecin
  (pas de compte patient séparé — il s'agit de l'accès médecin existant,
  rendu confortable sur petit écran).
- **Fiche patient complète** : identité, antécédents, **indication du
  traitement AVK** (fibrillation atriale, embolie pulmonaire, thrombose
  veineuse profonde, AVC ischémique/hémorragique, AIT, prothèse mécanique
  aortique ou mitrale, autre), date de l'événement médical, molécule AVK
  (Sintrom 4 mg / acénocoumarol par défaut, configurable).
- **Paramètres biologiques** par patient : urée, créatinine, ionogramme,
  TP, INR (bilan biologique), hémoglobine, plaquettes, avec date du bilan.
- **Cible INR configurable par patient**, avec gestion de l'exception
  "prothèse cardiaque mécanique" (cible relevée, ex. 2,5–3,5) — pré-cochée
  automatiquement si l'indication choisie est une prothèse aortique ou
  mitrale, mais toujours modifiable par le médecin.
- **Rendez-vous** : planification manuelle ou proposition automatique du
  prochain contrôle selon la fréquence de suivi du patient (15 jours / mois).
- **Consultations** : saisie de l'INR, de la dose (en comprimés Sintrom 4 mg
  et équivalent en mg), commentaire médical, observance, et **événements
  associés** :
  - événement hémorragique (oui/non + liste à cocher : AVC hémorragique,
    hémorragie digestive, hématurie, épistaxis, gingivorragie, hématome,
    hémoptysie, ménorragie, autre) ;
  - événement thrombotique/embolique (oui/non + liste à cocher : AVC
    ischémique, AIT, embolie pulmonaire, thrombose veineuse profonde,
    thrombose de prothèse valvulaire, ischémie artérielle, autre).
- **Historique et graphique d'évolution de l'INR** par patient.
- **Aide à la lecture de l'INR et alertes médicales**, affichées en temps
  réel à la saisie et conservées dans l'historique :
  - zone cible, sous-cible, sur-cible ;
  - alerte urgente si INR > 4, ou si un événement hémorragique est signalé ;
  - **alerte urgente spécifique de sous-dosage** chez les patients porteurs
    d'une prothèse mécanique (INR significativement sous la cible), car ce
    sous-dosage expose à un risque de thrombose de prothèse — traité avec
    la même sévérité qu'un risque hémorragique élevé.
- **Suggestion indicative de palier d'ajustement de dose**, affichée à côté
  du champ de saisie de la dose (jamais utilisée pour le pré-remplir) :
  variation usuelle de ±10 % (écart modéré à la cible) ou ±10 à 20 % (écart
  important, avec recommandation d'avis médical), ou maintien si l'INR est
  proche de la cible. Aucune suggestion n'est proposée en cas d'événement
  hémorragique signalé — la priorité est alors l'avis médical.
- **Traçabilité des changements de dose** : si la dose saisie à une
  consultation diffère de celle de la consultation précédente, un motif
  d'ajustement devient obligatoire et est conservé dans l'historique. La
  fiche de consultation affiche explicitement "dose ajustée" avec le motif
  renseigné par le médecin.

## 2. Installation locale (développement)

Prérequis : Python 3.10+.

```bash
# 1. Se placer dans le dossier du projet
cd anticoag_suivi

# 2. Créer un environnement virtuel (recommandé)
python3 -m venv venv
source venv/bin/activate      # sous Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Appliquer les migrations (crée la base SQLite db.sqlite3)
python manage.py migrate

# 5. (Optionnel) Créer un super-utilisateur pour accéder à /admin/
python manage.py createsuperuser

# 6. Lancer le serveur de développement
python manage.py runserver
```

L'application est accessible sur **http://127.0.0.1:8000/**.
Créez un compte médecin via "Créer un compte médecin" sur la page de connexion.

## 3. Structure du projet

```
anticoag_suivi/
├── accounts/          # Comptes médecins (authentification)
├── patients/           # Fiches patients
├── consultations/      # Rendez-vous, consultations, logique INR
│   └── inr_logic.py    # Logique d'interprétation INR (aide à la lecture)
├── templates/           # Templates HTML (base + par app)
├── static/css/style.css # Feuille de style
└── anticoag_suivi/      # Configuration Django (settings, urls)
```

## 4. Passage en production

Cette version est livrée prête pour une démonstration / un test avec des
médecins. Avant un déploiement en production réelle (données patients
réelles, accès via Internet), prévoir au minimum :

- **Base de données** : remplacer SQLite par PostgreSQL (`DATABASES` dans
  `settings.py`).
- **Variables d'environnement** : définir `DJANGO_SECRET_KEY`,
  `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` avec le(s) nom(s) de domaine réels.
- **HTTPS obligatoire** (les données de santé doivent être chiffrées en
  transit) — `SECURE_SSL_REDIRECT`, certificat TLS.
- **Sauvegardes régulières** de la base de données.
- **Conformité réglementaire locale** sur l'hébergement de données de santé
  (selon la réglementation tunisienne applicable aux données médicales).
- Politique de mots de passe et de sessions adaptée à un usage clinique réel
  (verrouillage de compte après échecs, expiration de session déjà activée
  à 4h, journalisation des accès si requis).
- Un serveur de production (Gunicorn/uWSGI + Nginx) plutôt que
  `manage.py runserver`, qui est réservé au développement.

## 5. Limites assumées de cette version

- Pas de gestion de rôles secondaires (infirmier, secrétariat) — un seul
  type de compte : médecin.
- Pas de notification automatique (SMS/email) de rappel de rendez-vous.
- Pas d'export PDF du dossier patient (peut être ajouté ultérieurement).
- L'aide à la lecture INR est volontairement simple et n'intègre pas
  d'autres facteurs cliniques (interactions médicamenteuses, alimentation,
  fonction hépatique, etc.) : elle ne remplace pas le jugement médical.
- La suggestion de palier d'ajustement de dose applique une règle générique
  (±10 à ±20 % selon l'écart à la cible) qui ne tient pas compte de l'historique
  complet du patient, de sa sensibilité individuelle à l'AVK, ni d'éventuelles
  interactions médicamenteuses ou alimentaires. Elle est affichée à titre
  indicatif uniquement et ne préremplit jamais le champ de dose.
