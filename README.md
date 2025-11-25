# Galaga-remaster
Voici une version remaster du jeu Galaga codé en Python.

Nouvelle fonctionnalité par rapport au jeu original:
-Nouveau mouvements pour le joueur : on bouge en (x, y).
-Nouveaux mouvements d’ennemis : horizontal, arrive_top/bottom, random, chase.
-Power-ups : double canons (mécanique différente)
-Projectiles dynamiques en direction du joueur.

Ce jeu est adapté pour une résolution d'écran en 1080 x 1880 (en mode portrait).

Il est également adapté pour un Raspberry pi 4 avec 4Go de RAM.
C'est important d'utiliser le code sur un appareil qui n'a pas une capacité de RAM au dessus de 4Go.
Sinon, le mouvement des ennemis est beaucoup trop rapide, les tirs aussi, les mouvements du joueur, etc.
Le jeu a été littéralement codé sur un Raspberry Pi 4 et il serait probalement compatible sur les autres        modèles de Raspberry avec une capacité de RAM dans les alentour de 4Go.

Un petit changement est nécessaire dans le code:
Il faut changer la directory des images des ennemis des joueurs etc.

Par exemple:
img = pygame.image.load("C:/Users/felix/OneDrive/Bureau/Galaga/photos/bullet.png").convert_alpha()

Il faut ajuster le chemin jusqu'à .../Galaga/photos/bullet.png
À répéter pour toutes les images.

Même chose pour el fichier.txt highscore:
C:/Users/felix/OneDrive/Bureau/Galaga/highscore

Le dossier audio se track tout seul.
