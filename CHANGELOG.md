# Changelog

Alle wichtigen Änderungen am Projekt können in dieser Datei dokumentiert werden.

## [Unreleased]

### Geplant
- Weitere Verbesserungen der Lernbereiche
- Ausbau der DP-900-Inhalte
- Weitere Optimierungen der Benutzeroberfläche
- Zusätzliche Auswertungen des Lernfortschritts

## [2026-09] – Aktueller Entwicklungsstand

### Hinzugefügt
- Streamlit-basierte DP-900-Lern-App
- Individuelles Azure-Data-Lab-Design
- Registrierung und Login über Supabase
- Getrennter dauerhafter Lernfortschritt pro Benutzer
- Lernkarten über `flashcards.json`
- Prüfungsfragen über `exam_questions.json`
- Supabase-Tabelle `user_progress`
- Deployment über Streamlit Community Cloud

### Behoben
- Laden des Supabase-Lernfortschritts stabilisiert
- Problematische Einzelabfrage durch eine robuste Select-/Limit-Abfrage ersetzt
