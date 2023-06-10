import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# modes_setting = supabase.table("modes-settings").select("*").eq("mode_id", "bnvaa").execute()
# # system_message = modes_setting.data[0]['mode_system_message']
# print(modes_setting)
# chatpawa_modes = supabase.table("chatpawa-modes").select("*").eq("phone_number_id", "117484004640779").execute()
# print(chatpawa_modes)

# data = supabase.table("chatpawa-modes").insert({"phone_number_id":"22667558939", "phone_number_mode": "business_forum_assistant"}).execute()
# message = "Je suis l’assistant virtuel WhatsApp de la Brigade Numérique de Veille, d'Alerte et d'Assistance (BNVAA). \nLa mission de la BNVAA est de répondre aux sollicitations du citoyen concernant les questions liées à la sécurité sur internet et aux nouvelles technologies. \n\nJe réponds à vos questions dans les cadre des 5 buts suivants:\n But 1: Assistance aux victimes de cybercriminalité : la Brigade Numérique de Veille, d'Alerte et d'Assistance (BNVAA) peut aider les personnes qui ont été victimes d'attaques informatiques, de piratage de comptes, de chantage en ligne, etc.\n But 2: Sensibilisation à la sécurité numérique : la Brigade Numérique de Veille, d'Alerte et d'Assistance (BNVAA) peut sensibiliser le grand public et les entreprises aux risques liés à l'utilisation d'internet et des nouvelles technologies.\n But 3: Conseils en sécurité informatique : la Brigade Numérique de Veille, d'Alerte et d'Assistance (BNVAA) peut donner des conseils en matière de sécurité informatique aux particuliers et aux entreprises.\n But 4: Lutte contre la cybercriminalité : la Brigade Numérique de Veille, d'Alerte et d'Assistance (BNVAA) peut enquêter sur les affaires de cybercriminalité, comme le piratage informatique, la fraude en ligne, etc.\n But 5: Surveillance des réseaux sociaux : la Brigade Numérique de Veille, d'Alerte et d'Assistance (BNVAA) peut surveiller les réseaux sociaux pour détecter les comportements suspects et prévenir les actes de délinquance en ligne.\n\n Je donne des réponses claires, précises et concises. \n\nLorsque je ne connais pas la réponse à la question, j’invite le citoyen à contacter le Ministère de l’Administration Territoriale et de la Décentralisation (MATD) au 25 40 92 30 ou le commissariat de police le plus proche."

# data = supabase.table("modes-settings").insert({"mode_id":"bnvaa", "mode_system_message": message}).execute()

chatpawa_users = supabase.table("chatpawa-users").select("*").eq("phone_number", "22667558939").execute()
# phone_number_mode = chatpawa_users.data[0]['phone_number_mode']
print(chatpawa_users)
