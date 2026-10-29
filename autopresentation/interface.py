"""Interface graphique Tkinter (entièrement en français, thème sombre façon Telegram)."""

import os
import queue
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

from . import NOM, VERSION, config, gemini
from .moteur import MoteurPresentation
from .powerpoint import THEME_DEFAUT, THEMES, ConstructeurPowerPoint
from .style import (ACCENT, FOND, PANNEAU, PANNEAU_CLAIR, POLICE, ROUGE, SEPARATEUR, TEXTE,
                    TEXTE_GRIS, VERT, Avatar, Bouton, InfoBulle, appliquer_theme)

ADRESSE_CLE = "https://aistudio.google.com/apikey"
SUJET_EXEMPLE = ("Exemple : La qualité des services dans une institution de microfinance : "
                 "accueil, attente aux guichets, crédits.")


def _generer(cle, modele, consigne, sur_attente):
    return gemini.generer_json(cle, modele, consigne, sur_attente=sur_attente)


class Application:
    def __init__(self, racine: tk.Tk, moteur: MoteurPresentation = None):
        self.racine = racine
        self.reglages = config.charger()
        self.moteur = moteur or MoteurPresentation(_generer, ConstructeurPowerPoint)
        self.nb_diapos = tk.IntVar(value=8)
        self.pause = tk.IntVar(value=1)
        self.theme = tk.StringVar(value=THEME_DEFAUT)
        self.lancer = tk.BooleanVar(value=True)
        self.auto = tk.IntVar(value=0)

        racine.title(f"{NOM} {VERSION}")
        racine.geometry("1060x700")
        racine.minsize(920, 620)
        self._construire()
        racine.protocol("WM_DELETE_WINDOW", self.quitter)
        self._maj_cle()
        self.racine.after(100, self._boucle)

    # --- Construction ---

    def _construire(self):
        appliquer_theme(self.racine)
        self.racine.columnconfigure(1, weight=1)
        self.racine.rowconfigure(0, weight=1)
        self._barre_laterale()
        self._zone_principale()

    def _titre(self, parent, texte):
        tk.Label(parent, text=texte, bg=PANNEAU, fg=ACCENT, font=(POLICE, 10, "bold"),
                 anchor="w").pack(fill="x", padx=16, pady=(14, 6))

    def _ligne(self, parent, titre):
        cadre = tk.Frame(parent, bg=PANNEAU)
        cadre.pack(fill="x", padx=16, pady=(0, 9))
        entete = tk.Frame(cadre, bg=PANNEAU)
        entete.pack(fill="x")
        tk.Label(entete, text=titre, bg=PANNEAU, fg=TEXTE_GRIS, font=(POLICE, 9), anchor="w",
                 wraplength=210, justify="left").pack(side="left")
        valeur = tk.Label(entete, text="", bg=PANNEAU, fg=TEXTE, font=(POLICE, 10, "bold"))
        valeur.pack(side="right")
        return cadre, valeur

    def _barre_laterale(self):
        barre = tk.Frame(self.racine, bg=PANNEAU, width=320)
        barre.grid(row=0, column=0, sticky="ns")
        barre.grid_propagate(False)
        barre.pack_propagate(False)

        entete = tk.Frame(barre, bg=PANNEAU)
        entete.pack(fill="x", padx=16, pady=(16, 4))
        Avatar(entete, "P").pack(side="left")
        textes = tk.Frame(entete, bg=PANNEAU)
        textes.pack(side="left", padx=12)
        tk.Label(textes, text=NOM, bg=PANNEAU, fg=TEXTE, font=(POLICE, 13, "bold"),
                 anchor="w").pack(anchor="w")
        self.lbl_cle = tk.Label(textes, text="", bg=PANNEAU, fg=TEXTE_GRIS, font=(POLICE, 9),
                                anchor="w")
        self.lbl_cle.pack(anchor="w")

        tk.Frame(barre, bg=SEPARATEUR, height=1).pack(fill="x", pady=(10, 0))
        self._titre(barre, "PARAMÈTRES")

        cadre, lbl = self._ligne(barre, "Nombre de diapositives")
        ttk.Scale(cadre, from_=3, to=20, variable=self.nb_diapos,
                  command=lambda v: self.nb_diapos.set(int(float(v)))).pack(fill="x", pady=(4, 0))
        lbl.configure(textvariable=self.nb_diapos)

        cadre, _ = self._ligne(barre, "Thème de couleurs")
        liste = ttk.Combobox(cadre, textvariable=self.theme, state="readonly", values=list(THEMES))
        liste.pack(fill="x", pady=(4, 0))

        cadre, lbl = self._ligne(barre, "Pause entre les diapositives (secondes)")
        ttk.Scale(cadre, from_=0, to=5, variable=self.pause,
                  command=lambda v: self.pause.set(int(float(v)))).pack(fill="x", pady=(4, 0))
        lbl.configure(textvariable=self.pause)
        InfoBulle(cadre, "Temps d'attente entre chaque diapositive pour les voir apparaître dans PowerPoint.")

        case = ttk.Checkbutton(barre, text="Lancer le diaporama à la fin", variable=self.lancer)
        case.pack(anchor="w", padx=16, pady=(2, 8))

        cadre, _ = self._ligne(barre, "Passage automatique des diapositives (secondes, 0 = manuel)")
        ttk.Spinbox(cadre, from_=0, to=120, textvariable=self.auto, width=8).pack(anchor="w", pady=(4, 0))

        bas = tk.Frame(barre, bg=PANNEAU)
        bas.pack(side="bottom", fill="x", padx=16, pady=(0, 14))
        Bouton(bas, "Quitter", self.quitter, style="danger", fond=PANNEAU, largeur=288).pack(pady=(0, 6))
        Bouton(bas, "À propos", self._a_propos, style="discret", fond=PANNEAU, largeur=288).pack(pady=(0, 6))
        Bouton(bas, "Paramètres (clé Gemini)", self._parametres, style="secondaire", fond=PANNEAU,
               largeur=288).pack()

    def _zone_principale(self):
        zone = tk.Frame(self.racine, bg=FOND)
        zone.grid(row=0, column=1, sticky="nsew")
        zone.columnconfigure(0, weight=1)
        zone.rowconfigure(1, weight=1)

        tk.Label(zone, text="Sujet de la présentation", bg=FOND, fg=TEXTE, anchor="w",
                 font=(POLICE, 13, "bold")).grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 4))

        cadre_texte = tk.Frame(zone, bg=PANNEAU_CLAIR)
        cadre_texte.grid(row=1, column=0, sticky="nsew", padx=24, pady=(4, 12))
        cadre_texte.columnconfigure(0, weight=1)
        cadre_texte.rowconfigure(0, weight=1)
        self.zone_sujet = tk.Text(cadre_texte, wrap="word", bg=PANNEAU_CLAIR, fg=TEXTE,
                                  insertbackground=TEXTE, relief="flat", font=(POLICE, 12),
                                  padx=14, pady=12, undo=True, borderwidth=0)
        self.zone_sujet.grid(row=0, column=0, sticky="nsew")
        defil = ttk.Scrollbar(cadre_texte, orient="vertical", command=self.zone_sujet.yview)
        defil.grid(row=0, column=1, sticky="ns")
        self.zone_sujet.configure(yscrollcommand=defil.set)
        self.zone_sujet.focus_set()

        tk.Label(zone, text=SUJET_EXEMPLE, bg=FOND, fg=TEXTE_GRIS, font=(POLICE, 9), anchor="w",
                 wraplength=640, justify="left").grid(row=2, column=0, sticky="ew", padx=24)

        etat = tk.Frame(zone, bg=FOND)
        etat.grid(row=3, column=0, sticky="ew", padx=24, pady=(12, 4))
        self.lbl_etat = tk.Label(etat, text="Prêt.", bg=FOND, fg=TEXTE_GRIS, font=(POLICE, 10),
                                 anchor="w", wraplength=640, justify="left")
        self.lbl_etat.pack(fill="x")
        self.progression = ttk.Progressbar(etat, style="Telegram.Horizontal.TProgressbar",
                                           maximum=100, mode="determinate")
        self.progression.pack(fill="x", pady=(6, 0))

        commandes = tk.Frame(zone, bg=FOND)
        commandes.grid(row=4, column=0, sticky="ew", padx=24, pady=(8, 20))
        self.btn_creer = Bouton(commandes, "Créer la présentation", self._creer, style="primaire",
                                fond=FOND, gras=True, hauteur=40)
        self.btn_creer.pack(side="left")
        self.btn_arret = Bouton(commandes, "Arrêter", self.moteur.arreter, style="danger", fond=FOND,
                                hauteur=40)
        self.btn_arret.pack(side="left", padx=10)
        self.btn_arret.state(["disabled"])

    # --- Actions ---

    def _maj_cle(self):
        if config.cle_effective(self.reglages):
            self.lbl_cle.configure(text="Clé Gemini : enregistrée", fg=VERT)
        else:
            self.lbl_cle.configure(text="Clé Gemini : manquante", fg=ROUGE)

    def _creer(self):
        sujet = self.zone_sujet.get("1.0", "end").strip()
        if not sujet:
            messagebox.showwarning(NOM, "Écrivez d'abord le sujet de la présentation.")
            return
        cle = config.cle_effective(self.reglages)
        if not cle:
            messagebox.showinfo(NOM, "Ajoutez d'abord votre clé Gemini gratuite dans les Paramètres.")
            self._parametres()
            return
        try:
            auto = max(0, int(self.auto.get()))
        except (tk.TclError, ValueError):
            auto = 0
        dossier = self.reglages.get("dossier_sortie") or config.dossier_sortie_defaut()
        if not os.path.isdir(dossier):
            dossier = config.dossier_sortie_defaut()
        demarre = self.moteur.demarrer({
            "sujet": sujet, "nb_diapos": int(self.nb_diapos.get()), "theme": self.theme.get(),
            "pause": int(self.pause.get()), "lancer": bool(self.lancer.get()), "auto": auto,
            "cle": cle, "modele": self.reglages.get("modele") or gemini.MODELE_DEFAUT,
            "dossier": dossier})
        if demarre:
            self._etat("Démarrage…", TEXTE_GRIS)
            self.progression["value"] = 0
            self.btn_creer.state(["disabled"])
            self.btn_arret.state(["!disabled"])

    def _etat(self, texte, couleur=TEXTE_GRIS):
        self.lbl_etat.configure(text=texte, fg=couleur)

    def _fin(self):
        self.btn_creer.state(["!disabled"])
        self.btn_arret.state(["disabled"])

    def _boucle(self):
        try:
            while True:
                type_message, valeur = self.moteur.file.get_nowait()
                if type_message == "etat":
                    self._etat(valeur)
                elif type_message == "progres":
                    self.progression["value"] = valeur
                elif type_message == "termine":
                    self._etat(f"Terminé. Fichier enregistré : {valeur}", VERT)
                    self._fin()
                elif type_message == "arrete":
                    self._etat("Création arrêtée. La présentation partielle reste ouverte dans PowerPoint.")
                    self._fin()
                elif type_message == "erreur":
                    self._etat(valeur, ROUGE)
                    self._fin()
                    messagebox.showerror(NOM, valeur)
        except queue.Empty:
            pass
        self.racine.after(100, self._boucle)

    def _parametres(self):
        fenetre = tk.Toplevel(self.racine)
        fenetre.title("Paramètres")
        fenetre.configure(bg=PANNEAU)
        fenetre.transient(self.racine)
        fenetre.resizable(False, False)
        fenetre.grab_set()

        def etiquette(texte, gris=False, **options):
            tk.Label(fenetre, text=texte, bg=PANNEAU, fg=TEXTE_GRIS if gris else TEXTE,
                     font=(POLICE, 9 if gris else 10), anchor="w", justify="left",
                     wraplength=440, **options).pack(fill="x", padx=20, pady=(10, 2))

        etiquette("Clé API Gemini")
        var_cle = tk.StringVar(value=self.reglages.get("cle", ""))
        champ = ttk.Entry(fenetre, textvariable=var_cle, show="•", width=56)
        champ.pack(padx=20, fill="x")
        var_voir = tk.BooleanVar(value=False)
        ttk.Checkbutton(fenetre, text="Afficher la clé", variable=var_voir,
                        command=lambda: champ.configure(show="" if var_voir.get() else "•")
                        ).pack(anchor="w", padx=20, pady=(4, 0))
        etiquette("La clé reste sur cet ordinateur (dossier de votre profil Windows). Elle n'est "
                  "jamais incluse dans le logiciel ni envoyée ailleurs qu'à Google.", gris=True)
        lien = tk.Label(fenetre, text="Obtenir une clé gratuite (Google AI Studio)", bg=PANNEAU,
                        fg=ACCENT, cursor="hand2", font=(POLICE, 9, "underline"))
        lien.pack(anchor="w", padx=20)
        lien.bind("<Button-1>", lambda _: webbrowser.open(ADRESSE_CLE))

        etiquette("Modèle Gemini")
        var_modele = tk.StringVar(value=self.reglages.get("modele") or gemini.MODELE_DEFAUT)
        ttk.Entry(fenetre, textvariable=var_modele, width=56).pack(padx=20, fill="x")
        etiquette("Si une erreur indique que le modèle est introuvable, copiez ici le nom d'un "
                  "modèle gratuit affiché dans Google AI Studio.", gris=True)

        etiquette("Dossier où enregistrer les présentations")
        ligne = tk.Frame(fenetre, bg=PANNEAU)
        ligne.pack(padx=20, fill="x")
        var_dossier = tk.StringVar(value=self.reglages.get("dossier_sortie") or config.dossier_sortie_defaut())
        ttk.Entry(ligne, textvariable=var_dossier, width=46).pack(side="left", fill="x", expand=True)
        Bouton(ligne, "Parcourir", lambda: var_dossier.set(
            filedialog.askdirectory(parent=fenetre, initialdir=var_dossier.get()) or var_dossier.get()),
            style="secondaire", fond=PANNEAU, hauteur=30).pack(side="left", padx=(8, 0))

        def enregistrer():
            self.reglages.update(cle=var_cle.get().strip(), modele=var_modele.get().strip(),
                                 dossier_sortie=var_dossier.get().strip())
            try:
                config.enregistrer(self.reglages)
            except OSError as exc:
                messagebox.showerror(NOM, f"Impossible d'enregistrer les paramètres : {exc}", parent=fenetre)
                return
            self._maj_cle()
            fenetre.destroy()

        boutons = tk.Frame(fenetre, bg=PANNEAU)
        boutons.pack(pady=16)
        Bouton(boutons, "Enregistrer", enregistrer, style="primaire", fond=PANNEAU, gras=True).pack(side="left")
        Bouton(boutons, "Annuler", fenetre.destroy, style="secondaire", fond=PANNEAU).pack(side="left", padx=8)

    def _a_propos(self):
        messagebox.showinfo(
            NOM, f"{NOM} {VERSION}\n\nCrée une présentation avec l'IA Gemini et la construit "
                 "directement dans Microsoft PowerPoint.\n\nLe sujet que vous écrivez est envoyé à "
                 "Google (API Gemini). N'y mettez pas d'informations confidentielles.\n"
                 "Aucun suivi, aucun compte.")

    def quitter(self):
        if self.moteur.en_cours() and not messagebox.askyesno(
                NOM, "Une création est en cours. Quitter quand même ?"):
            return
        self.moteur.arreter()
        self.racine.destroy()
