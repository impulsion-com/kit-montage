# Réel 9:16 face cam. Copier ce fichier dans le dossier du projet sous le nom build.py,
# adapter src, slug, titre et mots-clés, puis lancer : montage build.py plan
from plan import run

CONFIG = dict(
    src="~/Movies/mon-rush.mp4",        # le rush face cam (9:16 ou 16:9, recadré au centre)
    slug="testedit",
    title=dict(text="Google Ads en freelance ?"),
    keywords=["sur Instagram", "Google Ads", "media buying", "en freelance"],
    replacements=[("média buying", "media buying")],
    # broll : fond plein écran derrière la personne détourée (Mac). `file` = image ou vidéo locale,
    # `prompt` = image générée (skill nanobanana + GEMINI_API_KEY). Retirer le bloc pour un premier essai.
    broll=[
        dict(anchor="Google Ads", offset=-0.05, dur=1.4,
             prompt="Large monitor in a modern office showing an online advertising dashboard with rising performance graphs, blurred background, cool blue tones"),
        dict(anchor="en freelance", offset=-0.05, dur=1.2,
             prompt="Freelancer's open laptop on a wooden café terrace table by the sea at golden hour, coffee cup, palm leaves, warm light"),
    ],
    overlays=[
        dict(file="assets/message-instagram.png", anchor="sur Instagram", offset=-0.05, dur=1.15, x=0.5, y=0.89, w=0.78, anim="rise"),
    ],
)
if __name__ == "__main__":
    run(CONFIG)
