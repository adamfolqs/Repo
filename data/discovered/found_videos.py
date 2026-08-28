"""Colostrum creator videos found via web search, 2026-08-28.

Each row is a real video URL observed in search results, with the caption text
as returned. Engagement numbers are NOT here: search does not expose view or
like counts, so those cells stay empty until the scraper fills them. Guessing
them would make the sheet's sort order fiction.

BRAND-OWNED accounts are marked so they can be excluded from outreach --
@trymiraclemoo and @wondercowusa are the companies, not creators.
"""

ROWS = [
    # handle, video_id, caption, brand, is_brand_account
    ("jenlaurenn", "7339697324911988014", "Replying to @madzyounz armra review! #armra #colostrum #wellness", "ARMRA", False),
    ("katiejanehughes", "7543722539978099981", "My Daily Skincare Routine with ARMRA Colostrum", "ARMRA", False),
    ("cynthiamhuang", "7325892507798097194", "my honest first impressions of armra colostrum!!! #colostrum #tryarmra #armracolostrum #supplements #supplementsthatwork #vitamins #wellnesstok #wellnessjourney #superfood #guthealth #fyp", "ARMRA", False),
    ("realjessemetcalfe", "7576744365159238943", "HONEST review of Armra Colostrum Supplement. Best Colostrum in the game! @ARMRA", "ARMRA", False),
    ("drnikkakanani", "7395304560987753758", "Armra Colostrum Doctor Review part. Part 2 coming tomorrow #armracolostrum #colostrum #colostrumbenefits", "ARMRA", False),
    ("whatmojoloves", "7373064716282826027", "Replying to @Iza Here is my review on Armra colostrum. Every year the wellness industry picks one new trendy expensive supplement to rally behind. For me, it didn't make enough of a difference to justify the price point so its a hard pass for me. #wellness #productreview #wellnesstips #colostrum #supplements", "ARMRA", False),
    ("wellness.bysha", "7293365266409393438", "Trying Armra colostrum Day 1 Blood orange flavor review- LOVED IT #armracolostrum #Armra #wellness #productreview #wellnessproducts #wellnesstips #healthyliving #holistichealth @ARMRA", "ARMRA", False),

    ("abigailfeehls", "7332973868455382314", "Jumping on the colostrum train! Thank you Miracle Moo for working with me! Use ABIGAIL10 at checkout - link in bio #miraclemoovement #colostrumreview #colostrum #colostrumbenefits #selfcare #morningroutine", "Miracle Moo", False),
    ("terri_cardenas", "7298548045627657503", "Miracle moo bovine colostrum #miraclemoocolostrum #energy #boostimmunity #keepyouregular #grassfed #fyp #foryou #tiktokfamous #Duet", "Miracle Moo", False),
    ("soheman", "7421687867702971694", "Miracle Moo Colostrum Powder Unflavared #falldealsforyou #tiktokbacktoschool #tiktokshop #tiktokusa #reviews #health #guthealth #immuneboost", "Miracle Moo", False),
    ("gisellee_ramirezz", "7415745780578831659", "Miracle Moo Colostrum Powder #calostrobovino #colostrumbenefits #colostrum #sistemadigestivo #sistemainmunologico #treasurefinds #septemberfinds @Miracle Moo #español", "Miracle Moo", False),
    ("virginiaavc", "7288361419639213355", "#greenscreenvideo #miraclemoo #miraclemorningroutine #miraclemoonmagic #collostrum #calostrobovino #calostrobovinopuro #viral #tiktokviral", "Miracle Moo", False),
    ("veronika_vasquezr", "7387874320539749675", "Miracle Moo Colostrum Powder #viralforyourpage", "Miracle Moo", False),
    ("colostrumlovers", "7285407400138427690", "Miracle moo its magic. Link in my bio #health", "Miracle Moo", False),
    ("nicollefigueroaa", "7370905706226076970", "Realmente me ha ayudado muchisimo | miracle moo", "Miracle Moo", False),
    ("nicollefigueroaa", "7436927845638622510", "Mi experiencia con el milagroso producto miracle moo en 30 dias", "Miracle Moo", False),
    ("valereviews", "7325916397366758687", "Puedes encontrar el calostro bovino en la TikTok Shop!", "Miracle Moo", False),
    ("resetnutricional", "7320395718655610118", "Cai en la mercadotecnia de TikTok. Ya has probado este suplemento? #miraclemoo #suplementos #calostrobovino #nutricion #fyp", "Miracle Moo", False),
    ("leahdajud", "7322121129433320709", "Desmintiendo el suplemento Calostro bovino de moda en TikTok. No hay atajos magicos. Confien en su nutriologo, no en las modas. #nutrifacts #fitness #calostrobovino #desmintiendotiktoks #nutricion #nutriologa #miraclemoo #saludable #wellness", "Miracle Moo", False),

    ("cayleyxox", "7291013931995303214", "Anyone else taking this!? Loving it so far! @WonderCow Colostrum #colostrum #colostrumbenefits #tryarmra", "WonderCow", False),
    ("bombontec", "7347899259590561067", "Calostro Bovino suplemento @WonderCow #wondercow @TikTok Shop #tiktokspringsale #keeptiktok", "WonderCow", False),
    ("resetnutricional", "7370800235007823109", "Evidencia cientifica que avala la suplementacion de Calostro Bovino con una mejora en el manejo de estres oxidativo, radicales libres, mejor sistema inmunologico y digestivo! Cowabunga Colostrum - Tiktok Shop en mi cuenta #calostrobovino #cowabungacolostrum #suplemento #nutricion #nutriologa #viral", "Cowabunga", False),
    ("nutricionatuestilo", "7366018036505070866", "Beneficios del Calostro Bovino: Salud, Digestion y piel", "", False),
    ("toya_no_la", "7507817051050790186", "Colostrum can help with you hair, skin, nails, and gut health. #colostrum #colostrumbenefits #guthealth #healthygut #tiktokshopmemorialday #tiktokshopsummerturnup", "", False),

    # Brand-owned accounts - keep for competitive reference, exclude from outreach
    ("trymiraclemoo", "7507969616090680622", "Feel better with one scoop a day. Shop now to support your gut health with Miracle Moo Colostrum", "Miracle Moo", True),
    ("try.miraclemoo", "7285448112296971562", "Miracle Moo colostrum is POWERFUL #womenshealth #diet #supplements #bovinecolostrum #miraclemoo", "Miracle Moo", True),
    ("wondercowusa", "7252807568089746730", "3 things @Zam noticed after taking WonderCow Colostrum daily! #supplementsthatwork #guthealth #healthyliving #superfood #colostrum", "WonderCow", True),
]
