#!/usr/bin/env python3
"""Met à jour news.json à partir de flux RSS. Aucune dépendance (bibliothèque standard).
Lancé chaque jour par GitHub Actions (voir .github/workflows/news.yml). Modifiez FEEDS pour changer les sources."""
import json, sys, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

def gnews(q):
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q, "hl": "fr", "gl": "FR", "ceid": "FR:fr"})

FEEDS = [
    gnews('Blaye OR Gauriac OR "Haute-Gironde" OR "Blayais" when:30d'),   # vie locale
    gnews('santé Gironde OR "Nouvelle-Aquitaine" prévention when:30d'),   # santé en région
]
MAX_ITEMS = 8
# Filtre de pertinence : on ne garde que les articles liés à la santé, et on écarte les sujets hors-sujet.
KEEP = ["santé","sante","médecin","medecin","hôpital","hopital","soin","pharmac","infirm","vaccin","prévention","prevention",
        "maison de santé","msp","cpts","urgences","cancer","diabète","diabete","dépistage","depistage","épidémie","epidemie",
        "grippe","covid","canicule","addiction","tabac","alcool","pandémie","pandemie","maladie","virus","bronchiolite","allergie","santé mentale","dépression","depression","vieillissement","handicap","médicament","medicament","clinique","ehpad","dentiste","soignant","secours","pompiers","sevrage","nutrition","obésité","obesite","sommeil","douleur","accident"," avc","sage-femme","psycho","patient","ars ","assurance maladie","désert médical","desert medical"]
BLOCK = ["capoeira","football","rugby","match","concert","festival","loto","vide-grenier","brocante","spectacle","tournoi","exposition"]
def relevant(title):
    t = title.lower()
    return any(k in t for k in KEEP) and not any(b in t for b in BLOCK)
OUT = "news.json"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (msp-estuaire news bot)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def parse(xml_bytes):
    root = ET.fromstring(xml_bytes)
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        src = it.find("source")
        source = (src.text or "").strip() if src is not None else ""
        # Google News ajoute " - Nom du média" à la fin du titre
        if source and title.endswith(" - " + source):
            title = title[: -len(source) - 3].strip()
        try:
            d = parsedate_to_datetime(it.findtext("pubDate"))
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
        except Exception:
            d = datetime.now(timezone.utc)
        if title and link.startswith("http"):
            yield {"title": title, "link": link, "source": source, "date": d.isoformat()}

def main():
    items, seen = [], set()
    for url in FEEDS:
        try:
            for it in parse(fetch(url)):
                key = it["title"].lower()
                if key not in seen and relevant(it["title"]):
                    seen.add(key); items.append(it)
        except Exception as e:
            print("Flux ignoré :", url[:70], e, file=sys.stderr)
    items.sort(key=lambda x: x["date"], reverse=True)
    items = items[:MAX_ITEMS]
    if not items:
        print("Aucun article récupéré : news.json n'est pas modifié.", file=sys.stderr); return
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    print(len(items), "articles écrits dans", OUT)

if __name__ == "__main__":
    main()
