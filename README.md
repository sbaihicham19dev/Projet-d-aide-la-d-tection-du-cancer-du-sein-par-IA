# 🩺 BCD — Breast Cancer Detection

Système de **détection du cancer du sein assisté par IA** sur mammographies DICOM, basé sur une architecture **microservices**, déployé **100 % on premise** (CPU uniquement, aucune donnée patient ne quitte l'infrastructure).

> ⚠️ **Avertissement** : ce projet est un prototype de recherche/académique. Il ne remplace pas le diagnostic d'un radiologue qualifié et n'est pas certifié comme dispositif médical.

---

## 📌 Fonctionnement en bref

Un radiologue uploade une mammographie DICOM. Le système l'analyse automatiquement via 8 microservices IA indépendants, fusionne les résultats, génère un texte clinique avec un LLM local, puis produit un **rapport PDF** accompagné d'une heatmap explicative (Grad-CAM).

```
Upload DICOM → Image Service → RabbitMQ → 8 services IA (parallèle)
            → Assembler → LLM narratif → Report Service → PDF
```

---

## 🧩 Les services

### Services Python (FastAPI)

| Service | Port | Tâche unique | Technologie |
|---|---|---|---|
| `detection-service` | 8011 | Cancer / Non-Cancer | ResNet50 |
| `classification-service` | 8012 | Bénin / Malin | EfficientNet-B4 |
| `segmentation-service` | 8013 | Masque de la lésion | U-Net |
| `birads-service` | 8014 | Score BI-RADS 0–6 | CNN + règles ACR |
| `localization-service` | 8015 | Quadrant + côté du sein | Géométrie (centroïde) |
| `tumorsize-service` | 8016 | Taille en cm | Bounding box × PixelSpacing |
| `stage-service` | 8017 | Stade TNM I–IV | Règles TNM AJCC |
| `visualization-service` | 8018 | Heatmap + export masque | Grad-CAM |
| `assembler-service` | 8019 | Fusion des 8 résultats | Redis + Pydantic |
| `llm-narrative-service` | 8020 | JSON → texte clinique | Ollama · Phi-3 Mini |
| `analytics-service` | 8021 | Métriques (ROC, AUC…) | Pandas · scikit-learn |

### Services Java (Spring Boot 3)

| Service | Port | Rôle |
|---|---|---|
| `gateway` | 8080 | Routage, JWT, rate limiting |
| `auth-service` | 8081 | Authentification, rôles RBAC |
| `patient-service` | 8082 | CRUD dossiers patients |
| `image-service` | 8083 | Upload DICOM, stockage MinIO, publication RabbitMQ |
| `report-service` | 8084 | Génération du PDF |

### Infrastructure

| Composant | Rôle |
|---|---|
| RabbitMQ | Bus de messages asynchrone (fanout) |
| MinIO | Stockage objet S3 (DICOM, masques, heatmaps) |
| PostgreSQL | Bases métier |
| Redis | Cache JWT + collecte des résultats de l'assembler |
| Ollama | Inférence LLM locale sur CPU |

---

## 📁 Structure du projet

```
bcd-microservices/
├── docker-compose.yml
├── .env.example
├── README.md
├── frontend/                  # Angular
├── gateway/                   # Spring Cloud Gateway
├── services-java/
│   ├── auth-service/
│   ├── patient-service/
│   ├── image-service/
│   └── report-service/
├── services-python/
│   ├── detection-service/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py          # FastAPI + Swagger (/docs)
│   │   │   ├── router.py        # Endpoints REST
│   │   │   ├── consumer.py      # Listener RabbitMQ
│   │   │   ├── predictor.py     # Inférence modèle
│   │   │   ├── schemas.py       # Modèles Pydantic
│   │   │   ├── publisher.py     # Publication du résultat
│   │   │   └── minio_client.py  # Lecture image DICOM
│   │   ├── models/              # Poids du modèle (.pt)
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── .env
│   ├── classification-service/
│   ├── segmentation-service/
│   ├── birads-service/
│   ├── localization-service/
│   ├── tumorsize-service/
│   ├── stage-service/
│   ├── visualization-service/
│   ├── assembler-service/
│   ├── llm-narrative-service/
│   ├── analytics-service/
│   └── shared/                  # Schémas communs, utilitaires DICOM
└── infrastructure/
    ├── rabbitmq/
    ├── postgres/
    ├── minio/
    └── nginx/
```

Chaque service Python suit exactement la même structure interne.

---

## 🚀 Démarrage rapide

### Prérequis

- Python 3.11+
- Docker Desktop (moteur démarré)
- [Ollama](https://ollama.com) (pour le service LLM)

### Tester un service seul (sans Docker, via Swagger)

```bash
cd services-python/detection-service

# Environnement virtuel
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

pip install -r requirements.txt

# Désactiver RabbitMQ pour tester uniquement via Swagger
set ENABLE_CONSUMER=false      # Windows CMD
# export ENABLE_CONSUMER=false # Linux / macOS

uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload
```

Ouvrir **http://localhost:8011/docs** → `POST /predict/` → uploader un fichier `.dcm`.

### Avec Docker

```bash
cd services-python/detection-service
docker build -t detection-service .
docker run -p 8011:8011 -e ENABLE_CONSUMER=false detection-service
```

### Lancer les tests

```bash
pytest tests/ -v
```

### Tout le système (à venir)

```bash
docker compose up --build
```

---

## 🧠 LLM local (Ollama, CPU)

Le LLM sert uniquement à **rédiger le texte clinique** du rapport à partir du JSON des résultats (one-shot, pas de chat).

```bash
ollama pull phi3:mini
```

---

## 📥 Modèles et datasets

Les poids des modèles ne sont **pas** versionnés dans le dépôt. Placer les fichiers `.pt` dans le dossier `models/` de chaque service.

Datasets publics utilisables pour le fine-tuning :

| Dataset | Format |
|---|---|
| CBIS-DDSM | DICOM |
| VinDr-Mammo | DICOM |
| RSNA Breast Cancer Detection | DICOM |
| INbreast | DICOM |
| MIAS | PGM |

> En l'absence de fichier de poids, le `detection-service` démarre en **mode développement** avec des poids aléatoires (utile uniquement pour tester le pipeline, pas pour la précision).

---

## 🗺️ Roadmap

- [x] Architecture C4 (niveaux 1 à 4)
- [x] `detection-service` (FastAPI, Swagger, consumer, tests)
- [ ] `classification-service`
- [ ] `segmentation-service`
- [ ] `birads-service`
- [ ] `localization-service`
- [ ] `tumorsize-service`
- [ ] `stage-service`
- [ ] `visualization-service`
- [ ] `assembler-service`
- [ ] `llm-narrative-service`
- [ ] `analytics-service`
- [ ] Services Java (Auth, Patient, Image, Report)
- [ ] Frontend Angular
- [ ] `docker-compose.yml` global
- [ ] Fine-tuning des modèles sur CBIS-DDSM

---

## 🔒 Sécurité et confidentialité

- Traitement 100 % local : aucune API externe, aucune donnée patient envoyée à l'extérieur
- Authentification JWT et contrôle d'accès par rôles (RBAC)
- Ne jamais commiter de données patients, de fichiers DICOM réels ni de secrets (`.env`)

---

## 🛠️ Stack technique

**Backend IA** : Python 3.11 · FastAPI · PyTorch · pydicom · Pydantic · aio-pika
**Backend métier** : Java · Spring Boot 3 · Spring Cloud Gateway
**Frontend** : Angular · TypeScript
**Infra** : Docker · RabbitMQ · MinIO · PostgreSQL · Redis · Ollama
