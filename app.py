import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Mon Flair & Paris", page_icon="🎯", layout="centered"
)

# Connexion à Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)


def charger_donnees():
  try:
    df = conn.read(ttl=0)
    return df.dropna(how="all")
  except Exception:
    return pd.DataFrame(
        columns=[
            "id_ticket",
            "date",
            "type_pari",
            "affiche",
            "equipe_cible",
            "intitule",
            "cote_totale",
            "mise_totale",
            "statut",
            "gain_net",
        ]
    )


def sauvegarder_donnees(df):
  conn.update(data=df)


df_paris = charger_donnees()

# Variable de session pour stocker le panier de sélections en cours
if "panier_selections" not in st.session_state:
  st.session_state["panier_selections"] = []

st.title("🎯 Suivi de Paris & Intuition")

tab1, tab2, tab3 = st.tabs(
    ["➕ Nouveau Pari", "📋 Mes Paris", "📊 Mon Flair par Équipe"]
)

# --- TAB 1 : ENREGISTRER UN TICKET (SIMPLE OU COMBINÉ) ---
with tab1:
  st.subheader("1. Ajouter une sélection au ticket")

  col_date, col_comp = st.columns(2)
  with col_date:
    date_match = st.date_input("Date du match")
  with col_comp:
    competition = st.text_input("Compétition (ex: Ligue 1, NBA)")

  col_eq1, col_eq2 = st.columns(2)
  with col_eq1:
    eq_dom = st.text_input("Équipe Domicile").strip().upper()
  with col_eq2:
    eq_ext = st.text_input("Équipe Extérieur").strip().upper()

  options_cible = ["MATCH NUL"]
  if eq_dom:
    options_cible.insert(0, eq_dom)
  if eq_ext:
    options_cible.append(eq_ext)

  equipe_cible = st.selectbox("Issue / Équipe ciblée", options=options_cible)
  intitule = st.text_input(
      "Intitulé précis du pari (ex: Victoire, Les 2 équipes marquent)"
  )
  cote_sel = st.number_input(
      "Cote de cette sélection", min_value=1.01, step=0.05, value=1.50
  )

  if st.button("➕ Ajouter au ticket"):
    if not (competition and eq_dom and eq_ext and intitule):
      st.warning("Remplis toutes les informations du match.")
    else:
      st.session_state["panier_selections"].append({
          "date": str(date_match),
          "competition": competition,
          "affiche": f"{eq_dom} vs {eq_ext}",
          "equipe_cible": equipe_cible,
          "intitule": intitule,
          "cote": float(cote_sel),
      })
      st.success("Sélection ajoutée au ticket !")
      st.rerun()

  st.markdown("---")
  st.subheader("2. Ticket en cours")

  panier = st.session_state["panier_selections"]

  if not panier:
    st.info("Aucune sélection dans le ticket pour le moment.")
  else:
    # Affichage des sélections du ticket
    cote_totale = 1.0
    for idx, item in enumerate(panier):
      cote_totale *= item["cote"]
      col_info, col_del = st.columns([4, 1])
      with col_info:
        st.write(
            f"**{idx+1}. {item['affiche']}** — {item['equipe_cible']} "
            f"({item['intitule']}) @ **{item['cote']:.2f}**"
        )
      with col_del:
        if st.button("🗑️", key=f"del_{idx}"):
          st.session_state["panier_selections"].pop(idx)
          st.rerun()

    st.markdown("---")
    type_ticket = (
        "SIMPLE" if len(panier) == 1 else f"COMBINÉ ({len(panier)} sélections)"
    )
    st.markdown(f"### Type de ticket : **{type_ticket}**")
    st.metric("Cote Totale du Ticket", f"{cote_totale:.2f}")

    mise_totale = st.number_input(
        "Mise Totale (€)", min_value=0.5, step=1.0, value=10.0
    )
    gain_potentiel_brut = mise_totale * cote_totale
    gain_potentiel_net = gain_potentiel_brut - mise_totale

    st.info(
        f"💰 **Gain brut potentiel :** {gain_potentiel_brut:.2f}€  \n"
        f"📈 **Gain NET potentiel :** {gain_potentiel_net:+.2f}€"
    )

    if st.button("💾 Valider et Enregistrer le Ticket"):
      nouveau_id = len(df_paris) + 1

      # Résumé des affiches et des cibles pour le stockage
      affiches_str = " | ".join([p["affiche"] for p in panier])
      cibles_str = " | ".join([p["equipe_cible"] for p in panier])
      details_str = " | ".join([p["intitule"] for p in panier])

      nouveau_pari = pd.DataFrame([{
          "id_ticket": nouveau_id,
          "date": panier[0]["date"],
          "type_pari": type_ticket,
          "affiche": affiches_str,
          "equipe_cible": cibles_str,
          "intitule": details_str,
          "cote_totale": round(cote_totale, 2),
          "mise_totale": float(mise_totale),
          "statut": "EN_ATTENTE",
          "gain_net": 0.0,
      }])

      df_updated = pd.concat([df_paris, nouveau_pari], ignore_index=True)
      sauvegarder_donnees(df_updated)

      # Vider le panier
      st.session_state["panier_selections"] = []
      st.success("Ticket enregistré avec succès !")
      st.rerun()

# --- TAB 2 : LISTE ET RÉSOLUTION ---
with tab2:
  st.subheader("Liste de mes tickets")
  if df_paris.empty:
    st.info("Aucun ticket enregistré pour l'instant.")
  else:
    for index, row in df_paris.iloc[::-1].iterrows():
      with st.expander(
          f"[{row['statut']}] {row['date']} — {row['type_pari']} @ Cote"
          f" {row['cote_totale']}"
      ):
        st.write(f"**Affiche(s) :** {row['affiche']}")
        st.write(f"**Cible(s) :** {row['equipe_cible']}")
        st.write(f"**Détail(s) :** {row['intitule']}")
        st.write(
            f"**Cote Totale :** {row['cote_totale']} | **Mise :**"
            f" {row['mise_totale']}€"
        )

        if row["statut"] == "EN_ATTENTE":
          col1, col2 = st.columns(2)
          if col1.button("✅ GAGNÉ", key=f"g_{row['id_ticket']}"):
            df_paris.at[index, "statut"] = "GAGNE"
            df_paris.at[index, "gain_net"] = round(
                (row["mise_totale"] * row["cote_totale"]) - row["mise_totale"],
                2,
            )
            sauvegarder_donnees(df_paris)
            st.rerun()
          if col2.button("❌ PERDU", key=f"p_{row['id_ticket']}"):
            df_paris.at[index, "statut"] = "PERDU"
            df_paris.at[index, "gain_net"] = round(-row["mise_totale"], 2)
            sauvegarder_donnees(df_paris)
            st.rerun()
        else:
          st.write(f"**Gain Net :** {row['gain_net']:+.2f}€")

# --- TAB 3 : STATISTIQUES ET DIAGNOSTIC ---
with tab3:
  st.subheader("Analyse du flair par cible")
  df_termines = df_paris[df_paris["statut"] != "EN_ATTENTE"]

  if df_termines.empty:
    st.info("Clôturez au moins un pari pour débloquer les statistiques.")
  else:
    total = len(df_termines)
    gagnes = len(df_termines[df_termines["statut"] == "GAGNE"])
    profit = df_termines["gain_net"].sum()
    tot_mise = df_termines["mise_totale"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Réussite Globale", f"{(gagnes/total)*100:.0f}%")
    c2.metric("Total Misé", f"{tot_mise:.2f}€")
    c3.metric("Bilan Financier", f"{profit:+.2f}€")

    st.markdown("---")
    st.write("### Diagnostics d'Intuition (par équipe / cible)")

    # Découpage des cibles individuelles pour l'analyse
    cibles_flat = []
    for _, row in df_termines.iterrows():
      cibles = str(row["equipe_cible"]).split(" | ")
      for c in cibles:
        cibles_flat.append({
            "cible": c,
            "statut": row["statut"],
            "mise": row["mise_totale"] / len(cibles),
            "gain_net": row["gain_net"] / len(cibles),
        })

    df_cibles = pd.DataFrame(cibles_flat)

    stats = []
    for eq, group in df_cibles.groupby("cible"):
      v = len(group[group["statut"] == "GAGNE"])
      d = len(group[group["statut"] == "PERDU"])
      tot_eq = v + d
      wr = (v / tot_eq) * 100
      gain = group["gain_net"].sum()

      if tot_eq < 2:
        diag = "⚪ Recul insuffisant"
      elif gain > 0 and wr >= 60:
        diag = "🟢 FIABLE"
      elif gain < 0 and wr <= 40:
        diag = "🔴 PIÈGE"
      else:
        diag = "🟠 MITIGÉ"

      stats.append({
          "Équipe / Cible": eq,
          "Réussite": f"{wr:.0f}% ({v}V/{d}D)",
          "Bilan Net Estimé": f"{gain:+.2f}€",
          "Diagnostic": diag,
      })

    st.dataframe(pd.DataFrame(stats), use_container_width=True)
