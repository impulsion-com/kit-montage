# Vidéo 16:9 habillée de motion design : exemple réel (intro d'une formation Impulsion).
# Chaque graphisme est ancré sur un mot PRONONCÉ dans la vidéo (`at`, `until`) : les ancres
# ci-dessous ne marchent que sur ce rush, elles montrent la syntaxe. Graphismes dans les tiers
# gauche et droit, visage au centre.
from plan import run

L, R = 0.035, 0.965
S = 1.2             # échelle des panneaux   # bords d'ancrage (align left / right)

CONFIG = dict(
    src="~/Movies/mon-intro.mp4",
    slug="intro-dmb-demo",
    aspect="16:9",
    replacements=[("Mediabayeur", "media buyer"), ("Cloud", "Claude")],
    keywords=["Devenir media buyer", "freelance", "micro-entreprise", "Meta Ads", "Google Ads",
              "Claude Code", "automatiser", "réussir en freelance", "l'académie", "la communauté", "à votre rythme",
              "posez des questions", "bonne formation"],
    hide_captions=[(2.6, 6.1), (8.7, 13.3), (50.7, 53.9)],   # nom incrusté, puis plans de coupe qui disent déjà le texte
    style=dict(subY=0.83),
    graphics=[
        dict(kind="headline", at="bienvenue", offset=0.1, dur=4.6, x=L, y=0.42, scale=1.15, props=dict(
            align="left", eyebrow="FORMATION", lead="Devenir", pill="Media Buyer",
            micro="MEDIA BUYING · CLAUDE CODE · FREELANCE")),
        dict(kind="program", at="Nous commencerons", offset=-0.1, until="Tout le programme", x=L, y=0.47, scale=S, props=dict(
            align="left", eyebrow="LE PROGRAMME",
            items=[
                dict(title="La micro-entreprise", at="micro-entreprise", chips=[
                    dict(label="Créer", at="créer"), dict(label="Fonctionnement", at="fonctionnement"),
                    dict(label="Fiscalité", at="fiscalité"), dict(label="Obligations", at="obligations")]),
                dict(title="Le media buying", at="media buying", chips=[
                    dict(label="Meta Ads", at="Meta"), dict(label="Google Ads", at="Google")]),
                dict(title="Claude Code", at="Ensuite", chips=[
                    dict(label="Automatiser", at="automatiser"), dict(label="Gagner du temps", at="gagner")]),
                dict(title="Réussir en freelance", at="Enfin", chips=[
                    dict(label="Offre", at="offre"), dict(label="Tarifs", at="tarifs"),
                    dict(label="Prospecter", at="prospecter"), dict(label="Vendre", at="vendre")]),
            ])),
        dict(kind="prompt", at="automatiser", offset=-0.3, until="Enfin", until_offset=-0.1, x=R, y=0.4, scale=S, props=dict(
            align="right", eyebrow="CLAUDE CODE", typeMs=1300,
            text="Crée ma campagne Search et rédige les annonces",
            lines=[dict(label="Structure de campagne", at="création"), dict(label="Annonces rédigées", at="gestion"),
                   dict(label="Suivi automatisé", at="considérable")])),
        dict(kind="growth", at="grandir", offset=-0.35, until="hébergé", until_offset=0.2, x=R, y=0.42, scale=S, props=dict(
            align="right", eyebrow="VOTRE ACTIVITÉ", label="Faire grandir")),
        dict(kind="stack", at="retrouverez", offset=-0.1, until="Je compte", x=R, y=0.44, scale=S, props=dict(
            align="right", eyebrow="ACADEMIE.IMPULSION.COM", title="Tout au même endroit",
            items=[dict(icon="lessons", label="Les leçons", at="leçons"),
                   dict(icon="resources", label="Les ressources", at="ressources"),
                   dict(icon="community", label="La communauté", sub="pendant et après la formation", at="communauté")])),
        dict(kind="stack", at="exercices", offset=-0.3, until="Une dernière", x=L, y=0.42, scale=S, props=dict(
            align="left", eyebrow="À CHAQUE MODULE",
            items=[dict(icon="check", label="Exercice terminé", sub="pour progresser efficacement", at="progresser")])),
        dict(kind="notify", at="posez", offset=-0.3, until="Allez", x=R, y=0.36, scale=S, props=dict(
            align="right",
            items=[dict(app="Communauté · Académie", title="Nouvelle question", body="Comment je fixe mon premier tarif ?", at="posez"),
                   dict(app="Communauté · Académie", title="Réponse de l'équipe", body="On regarde ça ensemble 👇", at="répondre")])),
        # --- plans de coupe plein écran (video-shotcraft adapté, src/shots)
        dict(kind="shot", at="lancer", offset=-0.4, until="Nous", until_offset=-0.05, props=dict(
            name="pillSlot", stem="Vous saurez", pills=["lancer", "développer"], beat=95)),
        dict(kind="shot", at="Tout", after=39, offset=-0.1, until="retrouverez", until_offset=-0.15, props=dict(
            name="scramble", text="ACADEMIE.IMPULSION.COM")),
        dict(kind="shot", at="prenez", offset=-0.15, until="leçons", after=50, until_offset=0.35, props=dict(
            name="blurSlide", title="Avancez à votre rythme", subtitle="Revenez sur les leçons quand vous voulez")),
        dict(kind="cta", at="Allez", offset=-0.1, end=62.3, x=L, y=0.45, scale=S, props=dict(
            align="left", eyebrow="ON DÉMARRE", label="Module 1 · La micro-entreprise")),
    ],
)
if __name__ == "__main__":
    run(CONFIG)
