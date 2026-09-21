# Azure Data Lab – DP-900 Trainer

Eine interaktive Lern-Web-App zur Vorbereitung auf **Microsoft Azure Data Fundamentals (DP-900)**.

Die Anwendung wurde als Lern- und Portfolio-Projekt entwickelt. Sie verbindet eine individuell gestaltete Streamlit-Oberfläche mit Supabase für Authentifizierung und dauerhaft getrennten Lernfortschritt.

> **Hinweis:** Dieses Repository ist ein persönliches Projekt. Der Quellcode und die Inhalte dürfen nicht ohne ausdrückliche Genehmigung kopiert, verändert, weitergegeben oder anderweitig verwendet werden.

## Funktionen

- Registrierung und Login
- Persönlicher, dauerhaft gespeicherter Lernfortschritt
- Getrennte Daten pro Benutzer
- DP-900-Lernkarten
- Prüfungsfragen / Prüfungstraining
- Individuell gestaltetes Azure-Data-Lab-Dashboard
- Eigene Navigation und interaktive Lernbereiche
- Speicherung des Lernstands über Supabase
- Bereitstellung als Web-App über Streamlit Community Cloud

## Verwendete Technologien

| Technologie | Aufgabe |
| --- | --- |
| Python | Programmlogik |
| Streamlit | Web-App und Benutzeroberfläche |
| HTML / CSS | Individuelles Design |
| JSON | Lernkarten und Prüfungsfragen |
| Supabase | Authentifizierung und persistente Nutzerdaten |
| Git / GitHub | Versionsverwaltung und Quellcode-Repository |
| Streamlit Community Cloud | Deployment der Web-App |

## Architektur

```text
                    GitHub
                       |
                       v
            Streamlit Community Cloud
                       |
                       v
                    Benutzer
                       |
                       v
                 Streamlit-App
                       |
                       <---->
                    Supabase
```

**GitHub** enthält den Programmcode. **Streamlit Community Cloud** führt die Anwendung aus.  
Die **Streamlit-App** bildet Oberfläche und Programmlogik. **Supabase** übernimmt Benutzeranmeldung und dauerhaft gespeicherte Daten.

## Projektstruktur

```text
azure-dp900-trainer/
├── app.py
├── dashboard_background.jpeg
├── flashcards.json
├── exam_questions.json
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── .gitignore
```

### Wichtige Dateien

**`app.py`**  
Hauptdatei der Anwendung. Enthält Streamlit-Oberfläche, Navigation, Programmlogik und die Kommunikation mit Supabase.

**`flashcards.json`**  
Enthält die strukturierten Daten für die Lernkarten.

**`exam_questions.json`**  
Enthält die Fragen für das Prüfungstraining.

**`dashboard_background.jpeg`**  
Grafischer Hintergrund der Anwendung.

**`requirements.txt`**  
Enthält die Python-Pakete, die für den Betrieb der App benötigt werden.

## Lokaler Start

### 1. Repository herunterladen

```bash
git clone <URL-DES-EIGENEN-REPOSITORIES>
cd azure-dp900-trainer
```

### 2. Abhängigkeiten installieren

```bash
python3 -m pip install -r requirements.txt
```

### 3. Supabase-Secrets konfigurieren

Sensible Zugangsdaten gehören **nicht in den öffentlichen Quellcode**.

Für die lokale Entwicklung werden die benötigten Supabase-Werte über Streamlit Secrets bereitgestellt. Die Namen der Secrets müssen zu den in `app.py` verwendeten Bezeichnungen passen.

Beispielstruktur – nur Platzhalter, niemals echte Schlüssel committen:

```toml
SUPABASE_URL = "DEINE_SUPABASE_URL"
SUPABASE_KEY = "DEIN_SUPABASE_KEY"
```

### 4. App starten

```bash
streamlit run app.py
```

Anschließend öffnet Streamlit die Anwendung lokal im Browser.

## Deployment

Die veröffentlichte Anwendung wird über **Streamlit Community Cloud** betrieben.

Der grundsätzliche Ablauf:

```text
Code bearbeiten
      ↓
lokal testen
      ↓
Git / GitHub aktualisieren
      ↓
Streamlit Community Cloud
      ↓
aktualisierte Web-App
```

Die für Supabase benötigten Secrets werden in der Deployment-Umgebung hinterlegt und nicht öffentlich im GitHub-Repository gespeichert.

## Lernfortschritt

Während einer laufenden Streamlit-Sitzung werden bestimmte Zustände über `st.session_state` verwaltet.

Dauerhafte Daten werden dagegen in **Supabase** gespeichert. Dadurch kann ein Benutzer die App schließen und später mit seinem gespeicherten Lernstand fortfahren.

## Screenshots

Hier können später Screenshots der Anwendung ergänzt werden.

```markdown
![Dashboard](docs/images/dashboard.png)
![Lernkarten](docs/images/flashcards.png)
![Prüfung](docs/images/exam.png)
```

## Entwicklungsziel

Das Projekt entstand als praktische Ergänzung zum Lernen von Azure Data Fundamentals und zur Vertiefung von Python, Datenbanken, Cloud-Grundlagen und App-Entwicklung.

Dabei ging es nicht nur darum, DP-900-Inhalte darzustellen, sondern den kompletten Weg einer kleinen Webanwendung praktisch umzusetzen:

**Planung → Python → Streamlit → Daten → Backend → GitHub → Deployment**

## Status

Das Projekt befindet sich in aktiver Weiterentwicklung.

## Urheberrecht und Nutzung

**Copyright © 2026 Patricia Christiano. Alle Rechte vorbehalten.**

Dieses Projekt wird ausschließlich zur Ansicht und als persönliches Portfolio-/Lernprojekt veröffentlicht.

Ohne vorherige ausdrückliche schriftliche Genehmigung ist es insbesondere nicht gestattet, den Quellcode oder wesentliche Teile davon zu kopieren, zu verändern, weiterzuveröffentlichen, weiterzugeben, als eigenes Werk auszugeben oder für eigene Projekte zu verwenden.

Es wird bewusst **keine Open-Source-Lizenz** erteilt.
