import random

FIRST_NAMES = ["James","Sarah","Michael","Emily","David","Jessica","Robert","Jennifer","Daniel","Laura"]
LAST_NAMES = ["Mitchell","Parker","Roberts","Anderson","Johnson","Williams","Brown","Davis","Miller","Wilson"]

NEWSLETTER_KEYWORDS = {
    'en': ['newsletter','subscribe','signup','sign up','email','updates','join','stay updated','get updates'],
    'de': ['newsletter','abonnieren','anmelden','registrieren','e-mail','updates','beitreten','bleiben sie auf dem laufenden'],
    'fr': ['newsletter','abonner',"s'inscrire",'inscription','email','mises à jour','rejoindre','rester informé'],
    # Add other languages...
}

ALL_KEYWORDS = list({kw for kws in NEWSLETTER_KEYWORDS.values() for kw in kws})

SUCCESS_INDICATORS = ['thank','success','subscribed','confirm','check your email','check your inbox',
                      'danke','erfolg','abonniert','bestätigen','überprüfen sie ihre e-mail',
                      'merci','succès','abonné','confirmer','vérifiez votre email']


EMAIL_NEWSLETTER="doomv5697@gmail.com"
